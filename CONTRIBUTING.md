# Contributing to FineTuneKit

FineTuneKit's goal is to help more beginners successfully start fine-tuning with Unsloth. Contributions should make the first successful run easier, safer, or clearer.

## Good contributions

- Beginner-friendly task recipes: support bot, domain Q&A, extractor, classifier, writing style, code helper.
- Better data checks: leakage detection, JSON output validation, token-length warnings, duplicate detection.
- Better eval templates: exact match, rubric checks, LLM-as-judge, side-by-side comparisons.
- Cloud launchers: Colab, RunPod, Lambda, Modal.
- Pi / Claude Code / Codex agent workflows.
- Clear docs and examples with small toy datasets.

## Design principles

1. **Complement Unsloth, do not fork/replace it.** Generated training scripts should stay close to official Unsloth examples and link users back to official docs.
2. **No black boxes.** Beginners should be able to open `train.py`, `eval.py`, and `config.json` and understand what is happening.
3. **Eval before training.** Every recipe should include held-out eval guidance.
4. **Small first.** Prefer smoke tests and small models before larger expensive runs.
5. **Agent-readable.** Keep docs direct, command-oriented, and explicit enough for coding agents to follow.

## Local checks

```bash
python3 -m unittest discover -v
python3 -m finetunekit recommend --task support-bot --vram-gb 8 --no-detect
python3 -m finetunekit data check examples/chat_sample.jsonl
```

## Adding a recipe

A good recipe should include:

- task description
- expected data shape
- recommended model presets
- eval idea
- 3-5 sample examples
- common failure modes

## Relationship to Unsloth

This is an independent community project built to help more people use Unsloth successfully. Please keep attribution clear and avoid implying official endorsement unless the Unsloth team explicitly says so.
