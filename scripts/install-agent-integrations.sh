#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SKILL_SRC="$ROOT/skills/finetune-open-models"
PI_EXT_SRC="$ROOT/pi/extensions/finetunekit.ts"

install_skill() {
  local dir="$1"
  mkdir -p "$dir"
  # Remove old pre-rename symlink, then refresh the new one.
  if [[ -L "$dir/unsloth-finetune" ]]; then rm -f "$dir/unsloth-finetune"; fi
  if [[ -L "$dir/finetune-open-models" ]]; then rm -f "$dir/finetune-open-models"; fi
  ln -sfn "$SKILL_SRC" "$dir/finetune-open-models"
  echo "linked skill -> $dir/finetune-open-models"
}

install_pi_extension() {
  local dir="$HOME/.pi/agent/extensions"
  mkdir -p "$dir"
  if [[ -L "$dir/unslothkit.ts" ]]; then rm -f "$dir/unslothkit.ts"; fi
  if [[ -L "$dir/finetunekit.ts" ]]; then rm -f "$dir/finetunekit.ts"; fi
  ln -sfn "$PI_EXT_SRC" "$dir/finetunekit.ts"
  echo "linked Pi extension -> $dir/finetunekit.ts"
}

usage() {
  cat <<'EOF'
Install FineTuneKit agent integrations.

Usage:
  scripts/install-agent-integrations.sh [all|pi|skills|claude|codex|agents]

Targets:
  all      Install Pi extension + skills in common locations
  pi       Install Pi skill and Pi extension
  skills   Install the shared skill under ~/.agents/skills
  claude   Install skill under ~/.claude/skills
  codex    Install skill under ~/.codex/skills
  agents   Install skill under ~/.agents/skills
EOF
}

TARGET="${1:-all}"
case "$TARGET" in
  all)
    install_skill "$HOME/.agents/skills"
    install_skill "$HOME/.pi/agent/skills"
    install_skill "$HOME/.claude/skills"
    install_skill "$HOME/.codex/skills"
    install_pi_extension
    ;;
  pi)
    install_skill "$HOME/.pi/agent/skills"
    install_pi_extension
    ;;
  skills|agents)
    install_skill "$HOME/.agents/skills"
    ;;
  claude)
    install_skill "$HOME/.claude/skills"
    ;;
  codex)
    install_skill "$HOME/.codex/skills"
    ;;
  -h|--help|help)
    usage
    ;;
  *)
    echo "Unknown target: $TARGET" >&2
    usage >&2
    exit 1
    ;;
esac

echo
cat <<EOF
Done.

Next:
  - Restart your agent, or run /reload in Pi.
  - In Pi, use /finetune.
  - In any agent, ask: "use the finetune-open-models skill to fine-tune a model".
EOF
