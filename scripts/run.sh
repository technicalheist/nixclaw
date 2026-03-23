#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$SCRIPT_DIR"

# Activate venv
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
fi

# Run with all arguments forwarded
python -m nixclaw "$@"
