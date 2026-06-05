from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional

from .data import check_data, convert_csv_to_jsonl, split_jsonl
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
        fit = "unknown" if vram is None else ("fits" if rec.min_vram_gb <= vram else "stretch")
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


def cmd_data_split(args: argparse.Namespace) -> int:
    train_n, eval_n = split_jsonl(
        Path(args.input),
        Path(args.train_output),
        Path(args.eval_output),
        eval_ratio=args.eval_ratio,
        seed=args.seed,
        max_eval=args.max_eval,
    )
    print(f"✅ Split {args.input} -> {train_n} train / {eval_n} eval")
    train_report = check_data(Path(args.train_output), max_previews=1)
    eval_report = check_data(Path(args.eval_output), max_previews=1)
    print("\nTrain:")
    print_data_report(train_report)
    print("\nEval:")
    print_data_report(eval_report)
    return 0 if train_report.ok and eval_report.ok else 1


def _ask(prompt: str, default: str = "") -> str:
    suffix = f" [{default}]" if default else ""
    try:
        value = input(f"{prompt}{suffix}: ").strip()
    except EOFError:
        print("")
        return default
    return value or default


def cmd_demo(args: argparse.Namespace) -> int:
    project_path = Path(args.path).expanduser()
    sample = Path(__file__).resolve().parents[1] / "examples" / "chat_sample.jsonl"
    print(f"🦥 Creating UnslothKit demo at {project_path}")
    create_project(project_path, task="support-bot", model_label="tiny-smoke-test", force=args.force)
    all_path = project_path / "data" / "all_imported.jsonl"
    shutil.copyfile(sample, all_path)
    split_jsonl(all_path, project_path / "data" / "train.jsonl", project_path / "data" / "eval.jsonl", eval_ratio=0.5, seed=3407)
    report = check_data(project_path / "data" / "train.jsonl")
    print_data_report(report)
    print("\nOpen this first:")
    print(f"  {project_path / 'START_HERE.md'}")
    print("\nNext:")
    print(f"  cd {project_path}")
    print("  python eval.py --base   # in GPU/Unsloth env")
    print("  python train.py")
    return 0 if report.ok else 1


def cmd_quickstart(args: argparse.Namespace) -> int:
    print("🦥 UnslothKit quickstart\n")
    project = _ask("Project directory", args.path or "my-unsloth-bot")
    task = _ask("Task (support-bot/domain-qa/writing-style/extractor/classifier/code-helper)", args.task or "support-bot")
    vram = _ask("VRAM GB (optional; leave blank to auto-detect)", "")
    print("\nRecommended models:\n")
    rec_args = argparse.Namespace(task=task, vram_gb=float(vram) if vram else None, no_detect=bool(vram))
    cmd_recommend(rec_args)
    model = _ask("Model preset", args.model or "tiny-smoke-test")
    data_path = _ask("Existing data file (optional CSV or JSONL)", args.data or "")

    project_path = Path(project).expanduser()
    create_project(project_path, task=task, model_label=model, force=args.force)
    print(f"\n✅ Created project at {project_path}")

    if data_path:
        src = Path(data_path).expanduser()
        if not src.exists():
            print(f"❌ Data file not found: {src}", file=sys.stderr)
            return 1
        all_path = project_path / "data" / "all_imported.jsonl"
        train_path = project_path / "data" / "train.jsonl"
        eval_path = project_path / "data" / "eval.jsonl"
        if src.suffix.lower() == ".csv":
            n = convert_csv_to_jsonl(src, all_path)
            print(f"✅ Converted {n} CSV rows into {all_path}")
        else:
            shutil.copyfile(src, all_path)
            print(f"✅ Copied {src} into {all_path}")
        imported_report = check_data(all_path, max_previews=1)
        if imported_report.ok and imported_report.total_examples >= 2:
            train_n, eval_n = split_jsonl(all_path, train_path, eval_path, eval_ratio=0.1, seed=3407)
            print(f"✅ Created held-out split: {train_n} train / {eval_n} eval")
        else:
            shutil.copyfile(all_path, train_path)
            print("⚠️  Could not create train/eval split; using imported data as train and keeping sample eval data")

    print("\nChecking training data:\n")
    report = check_data(project_path / "data" / "train.jsonl")
    print_data_report(report)

    print("\nNext copy/paste commands:")
    print(f"  cd {project_path}")
    print("  python eval.py --base   # in GPU/Unsloth env")
    print("  python train.py")
    print("  python eval.py")
    print("  python chat.py")
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

    demo = sub.add_parser("demo", help="create a tiny sample project so you can see the generated workflow immediately")
    demo.add_argument("path", nargs="?", default="unslothkit-demo")
    demo.add_argument("--force", action="store_true")
    demo.set_defaults(func=cmd_demo)

    quick = sub.add_parser("quickstart", help="interactive beginner wizard: recommend model, create project, import/check data")
    quick.add_argument("--path", default=None)
    quick.add_argument("--task", default=None)
    quick.add_argument("--model", default=None)
    quick.add_argument("--data", default=None, help="optional CSV or JSONL file to import as train data")
    quick.add_argument("--force", action="store_true")
    quick.set_defaults(func=cmd_quickstart)

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
    split = data_sub.add_parser("split", help="split one JSONL file into train/eval JSONL files")
    split.add_argument("input")
    split.add_argument("train_output")
    split.add_argument("eval_output")
    split.add_argument("--eval-ratio", type=float, default=0.1)
    split.add_argument("--seed", type=int, default=3407)
    split.add_argument("--max-eval", type=int, default=None)
    split.set_defaults(func=cmd_data_split)

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
