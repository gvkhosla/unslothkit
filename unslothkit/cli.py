from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Optional

from .data import check_data, convert_csv_to_jsonl
from .doctor import detect_nvidia_vram_gb, format_checks, run_doctor
from .recommend import recommend_models, task_hint
from .templates import create_project


def print_data_report(report) -> None:
    print(f"Data report: {report.path}")
    print(f"Examples: {report.total_examples}")
    if report.ok:
        print("Status: ✅ no blocking errors")
    else:
        print(f"Status: ❌ {len(report.errors)} error(s)")
    if report.warnings:
        print(f"Warnings: {len(report.warnings)}")
    for issue in report.issues[:80]:
        loc = f"line {issue.line}" if issue.line else "file"
        icon = {"error": "❌", "warning": "⚠️ ", "info": "ℹ️ "}.get(issue.severity, "•")
        print(f"{icon} {loc}: {issue.message}")
    if len(report.issues) > 80:
        print(f"... {len(report.issues) - 80} more issues omitted")
    if report.previews:
        print("\nPreview:")
        for prev in report.previews:
            print(f"--- line {prev['line']} ---")
            for msg in prev["messages"][:6]:
                content = (msg.get("content", "") or "").replace("\n", " ")
                if len(content) > 180:
                    content = content[:177] + "..."
                print(f"{msg.get('role')}: {content}")


def cmd_new(args: argparse.Namespace) -> int:
    create_project(Path(args.path), task=args.task, model_label=args.model, force=args.force)
    print(f"✅ Created project at {args.path}")
    print(f"Next:")
    print(f"  cd {args.path}")
    print("  unslothkit data check data/train.jsonl")
    print("  python train.py")
    return 0


def cmd_doctor(args: argparse.Namespace) -> int:
    checks = run_doctor()
    print(format_checks(checks))
    return 1 if any(c.status == "error" for c in checks) else 0


def cmd_recommend(args: argparse.Namespace) -> int:
    vram = args.vram_gb
    if vram is None and not args.no_detect:
        vram = detect_nvidia_vram_gb()
    print(f"Task: {args.task}")
    print(f"Hint: {task_hint(args.task)}")
    if vram:
        print(f"Detected/selected VRAM: ~{vram:.1f}GB")
    else:
        print("VRAM: unknown (showing general beginner order)")
    print("")
    for idx, rec in enumerate(recommend_models(args.task, vram), start=1):
        fit = "fits" if (vram is None or rec.min_vram_gb <= vram) else "stretch"
        print(f"{idx}. {rec.label} [{fit}]")
        print(f"   model: {rec.model}")
        print(f"   min_vram: ~{rec.min_vram_gb}GB | template: {rec.chat_template} | rank: {rec.lora_rank}")
        print(f"   best for: {rec.best_for}")
        print(f"   notes: {rec.notes}")
    return 0


def cmd_data_check(args: argparse.Namespace) -> int:
    report = check_data(Path(args.file), max_previews=args.previews, max_chars=args.max_chars)
    print_data_report(report)
    if args.report_json:
        payload = {
            "path": str(report.path),
            "total_examples": report.total_examples,
            "issues": [issue.__dict__ for issue in report.issues],
            "ok": report.ok,
        }
        Path(args.report_json).write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(f"\nWrote JSON report to {args.report_json}")
    return 0 if report.ok else 1


def cmd_data_convert(args: argparse.Namespace) -> int:
    n = convert_csv_to_jsonl(Path(args.input), Path(args.output))
    print(f"✅ Converted {n} rows -> {args.output}")
    report = check_data(Path(args.output))
    print_data_report(report)
    return 0 if report.ok else 1


def run_project_script(project: str, script: str, extra: list[str]) -> int:
    path = Path(project)
    if not (path / script).exists():
        print(f"❌ {path / script} not found. Run `unslothkit new` first?", file=sys.stderr)
        return 1
    cmd = [sys.executable, script] + extra
    print(f"Running in {path}: {' '.join(cmd)}")
    return subprocess.call(cmd, cwd=str(path))


def cmd_train(args: argparse.Namespace) -> int:
    return run_project_script(args.project, "train.py", args.extra)


def cmd_chat(args: argparse.Namespace) -> int:
    extra = []
    if args.base:
        extra.append("--base")
    if args.max_new_tokens:
        extra += ["--max-new-tokens", str(args.max_new_tokens)]
    return run_project_script(args.project, "chat.py", extra)


def cmd_eval(args: argparse.Namespace) -> int:
    extra = []
    if args.base:
        extra.append("--base")
    if args.limit:
        extra += ["--limit", str(args.limit)]
    return run_project_script(args.project, "eval.py", extra)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="unslothkit", description="Beginner-friendly Unsloth fine-tuning CLI")
    sub = p.add_subparsers(dest="command", required=True)

    new = sub.add_parser("new", help="create a guided Unsloth fine-tuning project")
    new.add_argument("path", help="project directory to create")
    new.add_argument("--task", default="chat-assistant", choices=["chat-assistant", "support-bot", "domain-qa", "writing-style", "extractor", "classifier", "code-helper"])
    new.add_argument("--model", default="beginner-3b", help="recommendation label or Hugging Face model id")
    new.add_argument("--force", action="store_true")
    new.set_defaults(func=cmd_new)

    doctor = sub.add_parser("doctor", help="check whether your machine/environment is ready")
    doctor.set_defaults(func=cmd_doctor)

    rec = sub.add_parser("recommend", help="recommend beginner-safe models for your task/hardware")
    rec.add_argument("--task", default="chat-assistant")
    rec.add_argument("--vram-gb", type=float, default=None)
    rec.add_argument("--no-detect", action="store_true")
    rec.set_defaults(func=cmd_recommend)

    data = sub.add_parser("data", help="dataset helpers")
    data_sub = data.add_subparsers(dest="data_command", required=True)
    check = data_sub.add_parser("check", help="lint and preview a JSONL training file")
    check.add_argument("file")
    check.add_argument("--previews", type=int, default=3)
    check.add_argument("--max-chars", type=int, default=12000)
    check.add_argument("--report-json")
    check.set_defaults(func=cmd_data_check)
    convert = data_sub.add_parser("convert", help="convert CSV to chat JSONL")
    convert.add_argument("input")
    convert.add_argument("output")
    convert.set_defaults(func=cmd_data_convert)

    train = sub.add_parser("train", help="run train.py in a generated project")
    train.add_argument("project", nargs="?", default=".")
    train.add_argument("extra", nargs=argparse.REMAINDER, help="extra args passed to train.py")
    train.set_defaults(func=cmd_train)

    chat = sub.add_parser("chat", help="run chat.py in a generated project")
    chat.add_argument("project", nargs="?", default=".")
    chat.add_argument("--base", action="store_true")
    chat.add_argument("--max-new-tokens", type=int, default=256)
    chat.set_defaults(func=cmd_chat)

    ev = sub.add_parser("eval", help="run eval.py in a generated project")
    ev.add_argument("project", nargs="?", default=".")
    ev.add_argument("--base", action="store_true")
    ev.add_argument("--limit", type=int, default=20)
    ev.set_defaults(func=cmd_eval)

    return p


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args) or 0)
    except FileExistsError as exc:
        print(f"❌ {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"❌ {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
