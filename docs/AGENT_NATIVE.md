# Agent-native FineTuneKit

FineTuneKit is designed for anyone using a coding agent to fine-tune open-source models.

The goal is simple: let a person bring the goal/data/context, and let their agent reliably handle the repetitive fine-tuning workflow without inventing broken training code.

## Supported harness patterns

### Pi

Pi gets the richest integration:

```bash
./scripts/install-agent-integrations.sh pi
```

Then restart Pi or run `/reload` and use:

```text
/finetune
```

The Pi extension registers a simple `/finetune` launcher plus agent-callable tools:

- `finetunekit_doctor`
- `finetunekit_recommend`
- `finetunekit_create_project`
- `finetunekit_check_data`
- `finetunekit_convert_data`
- `finetunekit_split_data`
- `finetunekit_start_training`
- `finetunekit_run_eval`

Training launched from Pi runs in the background, writes a log under `.finetunekit/runs/`, and updates a Pi status/widget so the user can see what is happening without digging through terminals.

### Claude Code and Codex

Install the shared skill:

```bash
./scripts/install-agent-integrations.sh claude
./scripts/install-agent-integrations.sh codex
```

The skill is:

```text
skills/finetune-open-models/SKILL.md
```

### Amp, OpenCode, and other coding agents

Use the repo-level instructions:

```text
AGENTS.md
CLAUDE.md
docs/AGENT_QUICKSTART.md
```

Most coding harnesses can read `AGENTS.md` or can be pointed at it manually. The workflow is intentionally command-oriented so any agent can follow it.

## Agent workflow contract

Agents should follow this loop:

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

Rules:

- Clarify task, data, hardware, and success criteria first.
- Start with `tiny-smoke-test` unless the user has a known-good GPU setup.
- Never train until `data check` passes and previews look right.
- Keep eval data held out.
- Ask before launching paid cloud GPU jobs, pushing to Hugging Face, or overwriting user data.
- In Pi, prefer the native tools over raw shell for project creation, data conversion/splitting, training starts, and evals.

## Why this matters

Most people will not fine-tune from scratch by hand; they will ask a coding agent to help. Without a workflow contract, agents often improvise fine-tuning scripts, skip evals, or train on bad data. FineTuneKit gives agents boring, repeatable commands and generated scripts that are easy for people to inspect.
