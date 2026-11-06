#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [ ! -f .env ] || [ ! -d .venv ]; then
  echo "Run bash scripts/setup.sh first." >&2
  exit 1
fi

source .venv/bin/activate
exec uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
