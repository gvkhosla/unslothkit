# Unsloth community alignment

UnslothKit should be useful to the Unsloth team and community, not a competing abstraction that hides Unsloth.

## Positioning

UnslothKit is a beginner and agent workflow layer for Unsloth:

- It helps users pick safe starter settings.
- It validates data before training.
- It generates simple scripts based on Unsloth patterns.
- It sends users back to official Unsloth docs for installation, model support, Studio, advanced RL, and export details.

It is not a replacement for:

- Unsloth Core
- Unsloth Studio
- official Unsloth docs
- official Unsloth notebooks

## Messaging to use

Good:

> “UnslothKit helps beginners and coding agents create reproducible Unsloth fine-tuning projects.”

> “A lightweight starter layer for Unsloth.”

Avoid:

> “UnslothKit is Unsloth for beginners.”

> “Official Unsloth toolkit.”

> “Better than Unsloth Studio.”

## What would make the community like it

1. **Respect official docs**
   - Link to https://unsloth.ai/docs and https://github.com/unslothai/unsloth.
   - Keep generated scripts close to official examples.
   - Update templates when Unsloth APIs change.

2. **Reduce repeated beginner support load**
   - Catch bad data before users ask Discord for help.
   - Explain CUDA/VRAM/HF token issues in plain English.
   - Encourage smoke tests before big jobs.

3. **Make examples shareable**
   - Tiny datasets.
   - Clear task recipes.
   - Before/after eval outputs.

4. **Support agent workflows**
   - Pi `/unsloth` launcher.
   - Agent skill for Pi / Claude Code / Codex.
   - `AGENTS.md` and `docs/AGENT_QUICKSTART.md`.

5. **Be honest about limitations**
   - This is an MVP scaffold.
   - Generated evals are starter evals.
   - Training still requires a suitable Unsloth environment.

## Suggested roadmap for 10-100x more beginners

- Colab one-click generated notebook.
- “Paste CSV, get train/eval project” workflow.
- Task recipe gallery.
- LLM-as-judge eval generator.
- Unsloth Studio handoff docs.
- GPU fit estimator with actionable fallback settings.
- Export helpers for HF / Ollama / GGUF.
- Community “fix my dataset” command.

## Attribution snippet

Use this in docs/posts:

> UnslothKit is an independent community project built on top of Unsloth. For official installation instructions, model support, and advanced features, see https://unsloth.ai/docs and https://github.com/unslothai/unsloth.
