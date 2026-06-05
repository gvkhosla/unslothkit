# UnslothKit

Beginner-friendly, agent-native scaffolding for fine-tuning open-source models with [Unsloth](https://github.com/unslothai/unsloth).

UnslothKit helps people and their coding agents go from “I have a use case / CSV / chat examples” to a reproducible Unsloth project with:

- model + hardware recommendations
- data conversion, linting, and previews
- generated `train.py`, `chat.py`, and `eval.py`
- beginner-safe LoRA/QLoRA defaults
- Pi launcher + agent skills for Pi, Claude Code, and Codex

The CLI itself uses only Python stdlib. The generated training project installs Unsloth in the GPU environment.

## 60-second start

```bash
git clone https://github.com/gvkhosla/unslothkit.git
cd unslothkit
python3 -m unslothkit doctor
python3 -m unslothkit recommend --task support-bot
python3 -m unslothkit new my-support-bot --task support-bot --model tiny-smoke-test
python3 -m unslothkit data check my-support-bot/data/train.jsonl
```

Then, in a GPU/Unsloth environment:

```bash
cd my-support-bot
python train.py
python eval.py --base
python eval.py
python chat.py
```

## Install as a CLI

```bash
git clone https://github.com/gvkhosla/unslothkit.git
cd unslothkit
pip install -e .
unslothkit new my-bot
```

## Agent setup

Install shared skills for Pi / Claude Code / Codex and the Pi-native extension:

```bash
./scripts/install-agent-integrations.sh all
```

Then restart your agent or run `/reload` in Pi.

### Pi-native launcher

In Pi, use:

```text
/unsloth
```

The Pi extension adds:

- a TUI launcher
- `unslothkit_doctor`
- `unslothkit_recommend`
- `unslothkit_create_project`
- `unslothkit_check_data`

### Claude Code / Codex / other agents

The repo includes:

```text
AGENTS.md
CLAUDE.md
skills/unsloth-finetune/SKILL.md
```

Agents should follow the same loop:

1. clarify task/data/hardware
2. run `doctor`
3. recommend a small model
4. create project
5. check data
6. baseline eval
7. train
8. adapter eval + chat inspection
9. iterate from failures

## Commands

```bash
# Environment + model selection
python3 -m unslothkit doctor
python3 -m unslothkit recommend --task support-bot --vram-gb 8 --no-detect

# Project generation
python3 -m unslothkit new my-bot --task support-bot --model tiny-smoke-test
python3 -m unslothkit new my-bot --task domain-qa --model beginner-3b

# Data helpers
python3 -m unslothkit data check my-bot/data/train.jsonl
python3 -m unslothkit data convert input.csv my-bot/data/train.jsonl

# Generated-project workflow
cd my-bot
python eval.py --base
python train.py
python eval.py
python chat.py
python chat.py --base
```

## What `new` generates

```text
my-bot/
  config.json          # beginner-safe model + LoRA defaults
  train.py             # Unsloth SFT script
  chat.py              # interactive adapter/base chat
  eval.py              # tiny held-out before/after eval
  data/train.jsonl     # sample training data
  data/eval.jsonl      # sample held-out eval data
  notes/plan.md        # experiment checklist
```

## Data formats

Preferred chat JSONL:

```json
{"messages": [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]}
```

Also accepted by `data check`:

- `{"instruction": "...", "input": "...", "output": "..."}`
- `{"prompt": "...", "response": "..."}`
- `{"question": "...", "answer": "..."}`
- ShareGPT-ish `{"conversations": [{"from": "human", "value": "..."}, ...]}`

CSV conversion accepts headers:

- `instruction,output`
- `prompt,response`
- `question,answer`

```bash
python3 -m unslothkit data convert support.csv data/train.jsonl
```

## Training environment

For Unsloth Core, follow the current Unsloth install path in your GPU environment:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
uv venv unsloth_env --python 3.13
source unsloth_env/bin/activate
uv pip install unsloth --torch-backend=auto
```

Then run generated `train.py` from your project directory.

## Beginner rules baked in

- Run `doctor` before training.
- Run `data check` before training.
- Start with a 1B/3B smoke test before a 7B/8B run.
- Keep `data/eval.jsonl` held out.
- Compare `python eval.py --base` vs `python eval.py`.
- Inspect real outputs; do not trust loss alone.
- Do not launch paid cloud GPUs or push models to Hugging Face without explicit approval.

## Status

MVP scaffold. Good next additions:

- `/unsloth-train`, `/unsloth-eval`, `/unsloth-chat` Pi commands
- live training/eval Pi widget
- LLM-as-judge evals
- task-specific recipes for extractor/classifier/domain-QA/writing-style
- Colab/RunPod launchers
- Hugging Face export helpers
