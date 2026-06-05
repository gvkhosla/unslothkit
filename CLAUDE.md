# Claude Code instructions

This repo is an agent-native beginner layer for Unsloth fine-tuning.

Load and follow `skills/finetune-open-models/SKILL.md` whenever the user asks to fine-tune, adapt, improve, evaluate, export, or debug an open-source model with Unsloth.

Short version:

```bash
python3 -m finetunekit doctor
python3 -m finetunekit recommend --task <task>
python3 -m finetunekit new <project-dir> --task <task> --model tiny-smoke-test
python3 -m finetunekit data check <project-dir>/data/train.jsonl
cd <project-dir>
python eval.py --base
python train.py
python eval.py
python chat.py
```

Never train blindly. Validate data, baseline eval first, inspect outputs, then iterate.
