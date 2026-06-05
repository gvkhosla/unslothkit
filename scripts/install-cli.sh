#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BIN_DIR="${1:-$HOME/bin}"
mkdir -p "$BIN_DIR"

cat > "$BIN_DIR/finetunekit" <<EOF
#!/usr/bin/env bash
cd "$ROOT"
exec python3 -m finetunekit "\$@"
EOF
chmod +x "$BIN_DIR/finetunekit"

# Backward-compatible alias for anyone who installed the pre-rename MVP.
cat > "$BIN_DIR/unslothkit" <<EOF
#!/usr/bin/env bash
cd "$ROOT"
exec python3 -m finetunekit "\$@"
EOF
chmod +x "$BIN_DIR/unslothkit"

echo "Installed finetunekit wrapper -> $BIN_DIR/finetunekit"
echo "Installed compatibility alias -> $BIN_DIR/unslothkit"
if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
  echo "Note: $BIN_DIR is not on PATH. Add this to your shell config:"
  echo "  export PATH=\"$BIN_DIR:\$PATH\""
fi
