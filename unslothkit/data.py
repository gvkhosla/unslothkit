from __future__ import annotations

import csv
import json
import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, List, Optional, Sequence, Tuple

VALID_ROLES = {"system", "user", "assistant", "tool"}


@dataclass
class DataIssue:
    severity: str  # "error", "warning", "info"
    line: int
    message: str


@dataclass
class DataReport:
    path: Path
    total_examples: int = 0
    issues: List[DataIssue] = field(default_factory=list)
    previews: List[Dict[str, Any]] = field(default_factory=list)

    @property
    def errors(self) -> List[DataIssue]:
        return [i for i in self.issues if i.severity == "error"]

    @property
    def warnings(self) -> List[DataIssue]:
        return [i for i in self.issues if i.severity == "warning"]

    @property
    def ok(self) -> bool:
        return not self.errors


def load_jsonl(path: Path) -> Iterator[Tuple[int, Dict[str, Any]]]:
    with path.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            text = line.strip()
            if not text:
                continue
            try:
                obj = json.loads(text)
            except json.JSONDecodeError as exc:
                yield line_no, {"__parse_error__": str(exc)}
                continue
            if not isinstance(obj, dict):
                yield line_no, {"__parse_error__": "JSONL rows must be objects"}
                continue
            yield line_no, obj


def normalize_example(obj: Dict[str, Any]) -> Optional[List[Dict[str, str]]]:
    """Normalize common beginner data shapes to HF chat messages."""
    if "messages" in obj and isinstance(obj["messages"], list):
        return obj["messages"]
    if "conversations" in obj and isinstance(obj["conversations"], list):
        # Accept either HF {role, content} or ShareGPT {from, value}.
        messages = []
        for turn in obj["conversations"]:
            if not isinstance(turn, dict):
                return None
            if "role" in turn and "content" in turn:
                messages.append({"role": str(turn["role"]), "content": str(turn["content"])})
            elif "from" in turn and "value" in turn:
                role = {"human": "user", "gpt": "assistant", "assistant": "assistant", "user": "user", "system": "system"}.get(str(turn["from"]).lower(), str(turn["from"]).lower())
                messages.append({"role": role, "content": str(turn["value"])})
            else:
                return None
        return messages
    if "instruction" in obj and "output" in obj:
        user = str(obj.get("instruction") or "")
        extra = str(obj.get("input") or "").strip()
        if extra:
            user = user.rstrip() + "\n\n" + extra
        return [{"role": "user", "content": user}, {"role": "assistant", "content": str(obj.get("output") or "")}]
    if "prompt" in obj and "response" in obj:
        return [{"role": "user", "content": str(obj.get("prompt") or "")}, {"role": "assistant", "content": str(obj.get("response") or "")}]
    if "question" in obj and "answer" in obj:
        return [{"role": "user", "content": str(obj.get("question") or "")}, {"role": "assistant", "content": str(obj.get("answer") or "")}]
    return None


def validate_messages(messages: Any, line_no: int, max_chars: int = 12000) -> List[DataIssue]:
    issues: List[DataIssue] = []
    if not isinstance(messages, list) or not messages:
        return [DataIssue("error", line_no, "example must contain a non-empty messages/conversations list or instruction/output fields")]

    assistant_count = 0
    user_count = 0
    prev_role: Optional[str] = None
    total_chars = 0
    for idx, msg in enumerate(messages):
        if not isinstance(msg, dict):
            issues.append(DataIssue("error", line_no, f"message {idx} is not an object"))
            continue
        role = msg.get("role")
        content = msg.get("content")
        if role not in VALID_ROLES:
            issues.append(DataIssue("error", line_no, f"message {idx} has invalid role {role!r}; expected one of {sorted(VALID_ROLES)}"))
        if not isinstance(content, str) or not content.strip():
            issues.append(DataIssue("error", line_no, f"message {idx} has empty content"))
        else:
            total_chars += len(content)
        if role == "assistant":
            assistant_count += 1
        if role == "user":
            user_count += 1
        if role == prev_role and role in {"user", "assistant"}:
            issues.append(DataIssue("warning", line_no, f"message {idx} repeats role {role!r}; chat data usually alternates user/assistant"))
        prev_role = role

    if user_count == 0:
        issues.append(DataIssue("error", line_no, "example has no user message"))
    if assistant_count == 0:
        issues.append(DataIssue("error", line_no, "example has no assistant response to train on"))
    if messages and isinstance(messages[-1], dict) and messages[-1].get("role") != "assistant":
        issues.append(DataIssue("warning", line_no, "last message is not assistant; most SFT data should end with the desired assistant answer"))
    if total_chars > max_chars:
        issues.append(DataIssue("warning", line_no, f"example is long (~{total_chars} chars); it may exceed your max_seq_length"))
    return issues


def check_data(path: Path, max_previews: int = 3, max_chars: int = 12000) -> DataReport:
    report = DataReport(path=path)
    seen_keys: Dict[str, int] = {}
    if not path.exists():
        report.issues.append(DataIssue("error", 0, f"file not found: {path}"))
        return report
    if path.suffix.lower() != ".jsonl":
        report.issues.append(DataIssue("warning", 0, "expected .jsonl; use `unslothkit data convert` for CSV/instruction files"))

    for line_no, obj in load_jsonl(path):
        if "__parse_error__" in obj:
            report.issues.append(DataIssue("error", line_no, obj["__parse_error__"]))
            continue
        messages = normalize_example(obj)
        report.total_examples += 1
        if messages is None:
            report.issues.append(DataIssue("error", line_no, "unrecognized row shape; expected messages, conversations, instruction/output, prompt/response, or question/answer"))
            continue
        report.issues.extend(validate_messages(messages, line_no, max_chars=max_chars))
        key = "\n".join(m.get("content", "").strip() for m in messages if isinstance(m, dict))[:1000]
        if key in seen_keys:
            report.issues.append(DataIssue("warning", line_no, f"possible duplicate of line {seen_keys[key]}"))
        else:
            seen_keys[key] = line_no
        if len(report.previews) < max_previews:
            report.previews.append({"line": line_no, "messages": messages})

    if report.total_examples == 0:
        report.issues.append(DataIssue("error", 0, "no examples found"))
    elif report.total_examples < 20:
        report.issues.append(DataIssue("warning", 0, f"only {report.total_examples} examples found; fine-tuning usually needs more, but this is OK for a smoke test"))
    return report


def convert_csv_to_jsonl(input_path: Path, output_path: Path) -> int:
    """Convert CSV with common columns to chat JSONL."""
    count = 0
    with input_path.open("r", encoding="utf-8-sig", newline="") as f_in, output_path.open("w", encoding="utf-8") as f_out:
        reader = csv.DictReader(f_in)
        if not reader.fieldnames:
            raise ValueError("CSV has no header row")
        fields = {name.lower(): name for name in reader.fieldnames}
        for row in reader:
            obj: Dict[str, Any]
            if "instruction" in fields and "output" in fields:
                instr = row.get(fields["instruction"], "")
                inp = row.get(fields.get("input", ""), "") if "input" in fields else ""
                out = row.get(fields["output"], "")
                user = instr if not inp else f"{instr}\n\n{inp}"
                obj = {"messages": [{"role": "user", "content": user}, {"role": "assistant", "content": out}]}
            elif "prompt" in fields and "response" in fields:
                obj = {"messages": [{"role": "user", "content": row.get(fields["prompt"], "")}, {"role": "assistant", "content": row.get(fields["response"], "")}]}
            elif "question" in fields and "answer" in fields:
                obj = {"messages": [{"role": "user", "content": row.get(fields["question"], "")}, {"role": "assistant", "content": row.get(fields["answer"], "")}]}
            else:
                raise ValueError("CSV must contain instruction/output, prompt/response, or question/answer columns")
            f_out.write(json.dumps(obj, ensure_ascii=False) + "\n")
            count += 1
    return count


def split_jsonl(input_path: Path, train_path: Path, eval_path: Path, eval_ratio: float = 0.1, seed: int = 3407, max_eval: Optional[int] = None) -> Tuple[int, int]:
    """Split a JSONL file into train/eval files while preserving complete rows."""
    if not 0 < eval_ratio < 1:
        raise ValueError("eval_ratio must be between 0 and 1")
    lines = [line for line in input_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if len(lines) < 2:
        raise ValueError("need at least 2 non-empty JSONL rows to split")
    rng = random.Random(seed)
    rng.shuffle(lines)
    eval_count = max(1, round(len(lines) * eval_ratio))
    if max_eval is not None:
        eval_count = min(eval_count, max_eval)
    eval_count = min(eval_count, len(lines) - 1)
    eval_lines = lines[:eval_count]
    train_lines = lines[eval_count:]
    train_path.parent.mkdir(parents=True, exist_ok=True)
    eval_path.parent.mkdir(parents=True, exist_ok=True)
    train_path.write_text("\n".join(train_lines) + "\n", encoding="utf-8")
    eval_path.write_text("\n".join(eval_lines) + "\n", encoding="utf-8")
    return len(train_lines), len(eval_lines)


def write_sample(path: Path, task: str = "chat-assistant") -> None:
    examples = [
        {"messages": [{"role": "system", "content": "You are a helpful, concise assistant."}, {"role": "user", "content": "How do I reset my password?"}, {"role": "assistant", "content": "Click Forgot password on the sign-in page, enter your email, then follow the reset link. If the email does not arrive within 10 minutes, check spam or contact support."}]},
        {"messages": [{"role": "user", "content": "Can you summarize our refund policy?"}, {"role": "assistant", "content": "Refunds are available within 30 days for unused plans. For billing mistakes, include your invoice ID so support can investigate."}]},
        {"messages": [{"role": "user", "content": "The app keeps crashing. What should I do?"}, {"role": "assistant", "content": "Please update to the latest version, restart the app, and send your device type plus the crash time if it continues. I can escalate this to engineering if needed."}]},
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for ex in examples:
            f.write(json.dumps(ex, ensure_ascii=False) + "\n")
