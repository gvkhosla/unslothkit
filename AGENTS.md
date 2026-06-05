# Agent guide for FineTuneKit

Use this repo to make Unsloth fine-tuning beginner-simple and reproducible.

## Default workflow

1. Clarify the user's task, data, hardware, and deployment target.
2. For a beginner at the keyboard, prefer:
   ```bash
   python3 -m finetunekit quickstart
   ```
   For non-interactive work, run:
   ```bash
   python3 -m finetunekit doctor
   python3 -m finetunekit recommend --task <task>
   ```
3. Generate a project:
   ```bash
   python3 -m finetunekit new <project-dir> --task <task> --model tiny-smoke-test
   ```
4. Validate data before any training:
   ```bash
   python3 -m finetunekit data check <project-dir>/data/train.jsonl
   ```
5. In the generated project, run baseline eval before adapter eval:
   ```bash
   python eval.py --base
   python train.py
   python eval.py
   python chat.py
   ```

## Rules

- Start small: `tiny-smoke-test` or `beginner-3b` before 7B/8B.
- Never train until data previews look correct.
- If the user provides one JSONL file, use `python3 -m finetunekit data split ...` to create held-out eval data.
- Keep eval data held out.
- Inspect real generations; loss alone is not enough.
- Do not launch paid cloud GPUs, push to HF, or overwrite user data without explicit approval.
- Keep commands copy-pasteable and beginner-readable.

## Key files

- `finetunekit/cli.py` — CLI entrypoint
- `finetunekit/data.py` — data normalization/linting
- `finetunekit/recommend.py` — model/hardware recommendations
- `finetunekit/templates.py` — generated `train.py`, `chat.py`, `eval.py`
- `skills/finetune-open-models/SKILL.md` — Pi/Claude/Codex skill instructions
