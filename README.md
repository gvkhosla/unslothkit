# UnslothKit

A beginner-friendly CLI layer for [Unsloth](https://github.com/unslothai/unsloth). It helps you create a fine-tuning project, check your data, choose a model for your GPU, and run the generated Unsloth scripts.

UnslothKit is intentionally lightweight: the CLI itself uses only Python stdlib. Generated projects install Unsloth in the training environment.

## Pi-native launcher

This repo includes a Pi extension at `pi/extensions/unslothkit.ts`, globally linked to:

```text
~/.pi/agent/extensions/unslothkit.ts
```

Restart Pi or run `/reload`, then use:

```text
/unsloth
```

The extension adds a TUI launcher plus agent-callable tools for doctor, recommendations, project creation, and data checks.

## MVP commands

```bash
python -m unslothkit doctor
python -m unslothkit recommend --task support-bot
python -m unslothkit new my-support-bot --task support-bot --model beginner-3b
cd my-support-bot
python -m unslothkit data check data/train.jsonl
python train.py
python chat.py
```

If installed as a package:

```bash
pip install -e .
unslothkit new my-bot
```

## What it generates

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

## Data formats accepted by `data check`

Preferred chat JSONL:

```json
{"messages": [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]}
```

Also accepted:

- `{"instruction": "...", "input": "...", "output": "..."}`
- `{"prompt": "...", "response": "..."}`
- `{"question": "...", "answer": "..."}`
- ShareGPT-ish `{"conversations": [{"from": "human", "value": "..."}, ...]}`

CSV conversion:

```bash
unslothkit data convert support.csv data/train.jsonl
```

CSV headers must be one of: `instruction,output`, `prompt,response`, or `question,answer`.

## Training environment

For Unsloth Core, follow the current Unsloth install path:

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

## Status

MVP scaffold. Next obvious additions:

- Web UI / notebook generator
- LLM-as-judge evals
- Project dashboard for loss/eval outputs
- More task recipes: JSON extractor, classifier, code helper
- Colab/RunPod launchers
