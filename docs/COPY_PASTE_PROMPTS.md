# Copy/paste prompts for coding agents

Use these with Pi, Claude Code, Codex, Amp, OpenCode, or another coding-agent harness.

## Start from an idea

```text
Use this repo's AGENTS.md / FineTuneKit workflow. I want to fine-tune an open-source model with Unsloth for: <describe task>. Start small, check my environment, recommend a model, create a project, validate data before training, set up held-out evals, and do not start training or spend money without my approval.
```

## Start from a CSV

```text
Use FineTuneKit to turn this CSV into a fine-tuning project. Convert the CSV to chat JSONL if needed, create train/eval splits, run data checks, recommend a small model, and generate the project. Do not train until data previews look correct and I approve.
```

## Start from JSONL examples

```text
Use FineTuneKit with my JSONL examples. Validate the format, split held-out eval data if I only have one file, create a tiny smoke-test project first, and give me the exact commands to run base eval, train, adapter eval, and chat.
```

## Pi-specific

```text
Use /finetune or the FineTuneKit tools. Run doctor, recommend, create project, check data, and ask before starting background training. Show me the training log/status if a run is active.
```

## Debug a failed run

```text
Use FineTuneKit's workflow to debug this failed Unsloth fine-tuning run. Classify the issue as environment, VRAM, data, chat template/model mismatch, training config, or eval problem. Start by reading the generated config, data previews, and logs.
```
