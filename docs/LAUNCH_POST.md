# Launch post

I’ve been wanting to make it easier to use my coding agents to fine-tune open-source models and bring them into my own workflows.

So I made **FineTuneKit** — a small beginner-friendly, agent-native starter kit built on top of Unsloth.

The idea is simple: tell your coding agent the use case / CSV / examples, and get to a working fine-tuning project without getting stuck on model choice, data formatting, eval setup, or boilerplate scripts.

It helps with:

- picking a model for your hardware
- checking and converting data
- splitting train/eval sets
- generating `train.py`, `eval.py`, and `chat.py`
- giving agents like Pi / Claude Code / Codex / Amp / OpenCode a clear workflow to help

Quickstart:

```bash
git clone https://github.com/gvkhosla/finetunekit.git
cd finetunekit
python3 -m finetunekit quickstart
```

Repo: https://github.com/gvkhosla/finetunekit

Mostly built this for myself, but hoping it makes fine-tuning with Unsloth easier for other beginners too.
