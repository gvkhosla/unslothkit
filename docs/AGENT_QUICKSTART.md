# Agent Quickstart

Use this when operating FineTuneKit from Pi, Claude Code, Codex, or another coding agent.

## Goal

Make fine-tuning feel safe and beginner-simple. Do not assume the user knows model sizes, CUDA, chat templates, or dataset formats.

## First response checklist

Ask or infer:

- What should the model do?
- What data does the user have? CSV, JSONL, docs, chat logs, examples?
- What hardware/cloud target will train it?
- What does success look like?

Then run:

```bash
python3 -m finetunekit doctor
python3 -m finetunekit recommend --task <task>
```

## Happy path

For a human-in-the-loop setup, use the wizard:

```bash
python3 -m finetunekit quickstart
```

For non-interactive agents:

```bash
python3 -m finetunekit new <project-dir> --task <task> --model tiny-smoke-test
python3 -m finetunekit data check <project-dir>/data/train.jsonl
cd <project-dir>
python eval.py --base
python train.py
python eval.py
python chat.py
```

## Rules

- Start with `tiny-smoke-test` unless the user already has a known-good GPU setup.
- If the user gives one dataset file, use `data split` to create held-out eval data.
- Do not train until `data check` has no errors and previews look right.
- Keep eval data separate.
- Baseline eval before training.
- Inspect generations after training.
- Ask before spending money, launching cloud GPUs, pushing to Hugging Face, or overwriting user data.

## Common failure classification

- **Environment:** Python, CUDA, torch, unsloth, bitsandbytes, HF token.
- **VRAM:** OOM or too-large model/context/batch.
- **Data:** wrong roles, empty assistant answers, bad JSONL, training/eval leakage.
- **Template:** wrong chat template or model family mismatch.
- **Training:** NaN/exploding loss, no learning, overfitting tiny data.
- **Eval:** weak held-out set or metric not matching user goal.

## Pi-specific

If the Pi extension is installed, use `/finetune` or the tools:

- `finetunekit_doctor`
- `finetunekit_recommend`
- `finetunekit_create_project`
- `finetunekit_check_data`
