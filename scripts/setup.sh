#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
PYTHON_BIN="${PYTHON_BIN:-python3}"

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  echo "Python 3.11+ is required." >&2
  exit 1
fi

"$PYTHON_BIN" - <<'PY'
import sys
if sys.version_info < (3, 11):
    raise SystemExit("Python 3.11 or newer is required.")
print(f"Using Python {sys.version.split()[0]}")
PY

if [ ! -d .venv ]; then
  "$PYTHON_BIN" -m venv .venv
fi

source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r backend/requirements.txt

if [ ! -f .env ]; then
  python -m backend.app.cli init
else
  echo "Existing .env found; leaving it unchanged."
fi

echo
echo "MergeMind dependencies are installed."
echo "1. Start Ollama and pull the model: ollama pull qwen2.5-coder:3b"
echo "2. Start the app: bash scripts/run.sh"
echo "3. Open http://127.0.0.1:8000 and paste the admin token from .env."
