# Examples

Tiny example files for smoke-testing FineTuneKit data flows.

## Chat sample

```bash
python3 -m finetunekit data check examples/chat_sample.jsonl
```

## Create a starter project from the sample

```bash
python3 -m finetunekit quickstart --path /tmp/finetunekit-support-demo --task support-bot --model tiny-smoke-test --data examples/chat_sample.jsonl --force
```

Then inspect:

```bash
cd /tmp/finetunekit-support-demo
cat START_HERE.md
```

These examples are intentionally tiny. They are for pipeline validation, not model quality.
