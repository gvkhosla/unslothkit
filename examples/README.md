# Examples

Tiny example files for smoke-testing UnslothKit data flows.

## Chat sample

```bash
python3 -m unslothkit data check examples/chat_sample.jsonl
```

## Create a starter project from the sample

```bash
python3 -m unslothkit quickstart --path /tmp/unslothkit-support-demo --task support-bot --model tiny-smoke-test --data examples/chat_sample.jsonl --force
```

Then inspect:

```bash
cd /tmp/unslothkit-support-demo
cat START_HERE.md
```

These examples are intentionally tiny. They are for pipeline validation, not model quality.
