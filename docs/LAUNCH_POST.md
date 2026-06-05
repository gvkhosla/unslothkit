# Launch post

I’ve been wanting to make it easier for myself to fine-tune open-source models and bring them into my own workflows and agents.

So I made **FineTuneKit** — a small beginner-friendly starter kit built on top of Unsloth.

The idea is simple: go from a use case / CSV / examples to a working fine-tuning project without getting stuck on model choice, data formatting, eval setup, or boilerplate scripts.

It helps with:

- picking a model for your hardware
- checking and converting data
- splitting train/eval sets
- generating `train.py`, `eval.py`, and `chat.py`
- giving agents like Pi / Claude Code / Codex a clear workflow to help

Quickstart:

```bash
git clone https://github.com/gvkhosla/finetunekit.git
cd finetunekit
python3 -m finetunekit quickstart
```

Repo: https://github.com/gvkhosla/finetunekit

Mostly built this for myself, but hoping it makes fine-tuning with Unsloth easier for other beginners too.
