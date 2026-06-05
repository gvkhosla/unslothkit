# Agent guide for UnslothKit

Use this repo to make Unsloth fine-tuning beginner-simple and reproducible.

## Default workflow

1. Clarify the user's task, data, hardware, and deployment target.
2. Run:
   ```bash
   python3 -m unslothkit doctor
   python3 -m unslothkit recommend --task <task>
   ```
3. Generate a project:
   ```bash
   python3 -m unslothkit new <project-dir> --task <task> --model tiny-smoke-test
   ```
4. Validate data before any training:
   ```bash
   python3 -m unslothkit data check <project-dir>/data/train.jsonl
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
- Keep eval data held out.
- Inspect real generations; loss alone is not enough.
- Do not launch paid cloud GPUs, push to HF, or overwrite user data without explicit approval.
- Keep commands copy-pasteable and beginner-readable.

## Key files

- `unslothkit/cli.py` — CLI entrypoint
- `unslothkit/data.py` — data normalization/linting
- `unslothkit/recommend.py` — model/hardware recommendations
- `unslothkit/templates.py` — generated `train.py`, `chat.py`, `eval.py`
- `skills/unsloth-finetune/SKILL.md` — Pi/Claude/Codex skill instructions
