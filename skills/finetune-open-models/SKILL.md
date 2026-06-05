---
name: finetune-open-models
description: Beginner-first open-model fine-tuning workflow using FineTuneKit and Unsloth. Use whenever the user wants to fine-tune, adapt, improve, evaluate, export, or debug an open-source LLM with Unsloth, especially from Pi, Claude Code, or Codex. Covers dataset checks, model/hardware selection, project generation, SFT training, evals, chat testing, and safe iteration.
---

# Fine-tune Open Models

You are helping a beginner fine-tune an open-source model with Unsloth. Own the loop and keep it simple: choose a safe model, validate data, generate a project, run a smoke test, evaluate before/after, inspect outputs, and iterate.

## Locate the repo

This skill lives at `skills/finetune-open-models/SKILL.md`. The FineTuneKit repo root is two directories up from this file.

When using shell commands, first `cd` to the FineTuneKit repo root. If the repo is not present, clone it:

```bash
git clone https://github.com/gvkhosla/finetunekit.git
cd finetunekit
```

## Non-negotiable workflow

1. **Start with the goal**
   - Ask/confirm: task, target behavior, available data, hardware/cloud target, deployment target.
   - If unclear, pick the smallest useful first experiment.

2. **Check the environment**
   ```bash
   python3 -m finetunekit doctor
   python3 -m finetunekit recommend --task <task>
   ```
   For a human-in-the-loop beginner flow, you can use:
   ```bash
   python3 -m finetunekit quickstart
   ```
   - If local machine is not suitable, suggest Colab/RunPod/Lambda/Unsloth Studio.
   - Do not spend time debugging training until basic install/GPU/token issues are understood.

3. **Create or inspect a project**
   ```bash
   python3 -m finetunekit new <project-dir> --task <task> --model tiny-smoke-test
   ```
   - Start with `tiny-smoke-test` or `beginner-3b` unless user explicitly has enough VRAM.
   - Prefer generated scripts over handwritten notebooks for reproducibility.

4. **Validate data before training**
   ```bash
   python3 -m finetunekit data check <project-dir>/data/train.jsonl
   ```
   - Read previews. Confirm assistant answers are the target behavior.
   - Errors must be fixed before training.
   - Warn if eval data overlaps with train data.

5. **Set up evaluation first**
   - Keep `data/eval.jsonl` held out.
   - Run baseline eval before adapter eval:
     ```bash
     cd <project-dir>
     python eval.py --base
     ```
   - If eval is too weak, help write better held-out examples before scaling training.

6. **Train small, then inspect**
   ```bash
   cd <project-dir>
   python train.py
   python eval.py
   python chat.py
   ```
   - Monitor logs in the first few steps.
   - Stop only for clear issues: import errors, OOM, NaN/exploding loss, obviously wrong data formatting.
   - Always inspect actual generations, not just loss.

7. **Iterate from failures**
   - Add examples for failure cases.
   - Re-run `data check`.
   - Compare base vs adapter.
   - Only then increase steps/model size/context length.

## Model defaults

Use `finetunekit recommend` when possible. Beginner defaults:

- Pipeline smoke test: `tiny-smoke-test` / `unsloth/Llama-3.2-1B-Instruct-bnb-4bit`
- Beginner default: `beginner-3b` / `unsloth/Llama-3.2-3B-Instruct-bnb-4bit`
- Higher quality with more VRAM: `qwen-7b-quality`, `llama-8b-quality`, `mistral-7b-fast`

If the user says “any model,” still verify:

- model is instruction/chat capable for chat SFT
- chat template is correct
- model fits hardware
- gated model access / HF token is available

## Data rules

Preferred JSONL row:

```json
{"messages": [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]}
```

Also acceptable: `instruction/output`, `prompt/response`, `question/answer`, ShareGPT-ish `conversations`.

Never train blindly. Look for:

- empty assistant responses
- wrong roles
- training on user text instead of assistant text
- duplicated examples
- eval leakage
- too-long examples
- outputs that do not match the desired product behavior

## Agent behavior

- Be approval-light for local file generation, but do not spend money / launch cloud GPUs / push to Hugging Face without explicit approval.
- Keep commands copy-pasteable.
- Prefer stdlib/local scripts over requiring users to understand ML internals.
- When training fails, first classify: environment, data, model/template, VRAM, dependency mismatch, or Unsloth bug.
- Document every experiment in `<project-dir>/notes/plan.md` or an experiment note.

## Useful commands

```bash
# From repo root
python3 -m finetunekit doctor
python3 -m finetunekit recommend --task support-bot --vram-gb 8 --no-detect
python3 -m finetunekit new ~/my-bot --task support-bot --model beginner-3b
python3 -m finetunekit data check ~/my-bot/data/train.jsonl
python3 -m finetunekit data convert input.csv output.jsonl
python3 -m finetunekit data split all.jsonl my-bot/data/train.jsonl my-bot/data/eval.jsonl

# From generated project
python train.py
python eval.py --base
python eval.py
python chat.py
python chat.py --base
```

Read `README.md`, `AGENTS.md`, `finetunekit/cli.py`, `finetunekit/templates.py`, and `finetunekit/data.py` if you need implementation details.
