# Unsloth compatibility notes

FineTuneKit is designed as a lightweight on-ramp to Unsloth, not a fork or replacement. This document explains what generated projects currently assume.

## What generated `train.py` uses

Generated SFT projects use common Unsloth notebook patterns:

- `from unsloth import FastLanguageModel, is_bfloat16_supported`
- `FastLanguageModel.from_pretrained(...)`
- `FastLanguageModel.get_peft_model(...)`
- `unsloth.chat_templates.get_chat_template(...)`
- `unsloth.chat_templates.train_on_responses_only(...)` for supported templates
- TRL `SFTTrainer` / `SFTConfig`
- Hugging Face `datasets.Dataset`
- `model.save_pretrained(...)` for LoRA adapters
- optional `save_pretrained_merged(...)` / `save_pretrained_gguf(...)`

## What FineTuneKit intentionally does not do

- It does not vendor Unsloth code.
- It does not vendor Unsloth notebooks or assets.
- It does not claim to support every Unsloth model/task.
- It does not replace official Unsloth install docs, Studio, or notebooks.

## How to keep it useful for the Unsloth community

When Unsloth APIs or recommended notebooks change, update FineTuneKit templates to match official guidance. Prefer small, obvious generated scripts that users can compare with official examples.

## Local validation

The CLI can be tested without Unsloth installed:

```bash
python3 -m unittest discover -v
python3 -m finetunekit demo /tmp/finetunekit-demo
python3 -m finetunekit data check /tmp/finetunekit-demo/data/train.jsonl
```

Actual training validation requires a suitable Unsloth GPU environment. Use official install instructions:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
uv venv unsloth_env --python 3.13
source unsloth_env/bin/activate
uv pip install unsloth --torch-backend=auto
```

Then run a generated tiny smoke test before scaling up.
