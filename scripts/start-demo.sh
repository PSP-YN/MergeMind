#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SWITCH_DIR="${SWITCH_DIR:-$HOME/projects/hackathon/switch}"
MM_PORT="${MERGEMIND_PORT:-8001}"
SWITCH_PORT="${SWITCH_PORT:-8000}"
GATEWAY_PORT="${GATEWAY_PORT:-5173}"
LOG_DIR="${XDG_STATE_HOME:-$HOME/.local/state}/mergemind-demo"
mkdir -p "$LOG_DIR"

fail() { echo "ERROR: $*" >&2; exit 1; }
wait_http() {
  local url="$1" label="$2"
  for _ in $(seq 1 40); do
    if curl -fsS --max-time 2 "$url" >/dev/null 2>&1; then
      echo "  ready: $label ($url)"
      return 0
    fi
    sleep 1
  done
  echo "  not ready: $label; inspect $LOG_DIR" >&2
  return 1
}
start_bg() {
  local name="$1" port="$2"; shift 2
  if ss -ltn 2>/dev/null | grep -qE "[:.]$port[[:space:]]"; then
    echo "  already listening: $name on port $port"
    return 0
  fi
  local pidfile="$LOG_DIR/$name.pid"
  if [[ -f "$pidfile" ]] && kill -0 "$(cat "$pidfile")" 2>/dev/null; then
    echo "  process already running: $name"
    return 0
  fi
  nohup "$@" >"$LOG_DIR/$name.log" 2>&1 </dev/null &
  echo $! >"$pidfile"
  echo "  started: $name (log: $LOG_DIR/$name.log)"
}

command -v docker >/dev/null || fail "Docker is required for the local Switch PostgreSQL service."
command -v curl >/dev/null || fail "curl is required."
command -v ss >/dev/null || fail "iproute (ss) is required."
[[ -f "$ROOT/.env" ]] || fail "MergeMind .env is missing. Run bash scripts/setup.sh first."
[[ -x "$ROOT/.venv/bin/uvicorn" ]] || fail "MergeMind virtual environment missing. Run bash scripts/setup.sh."
[[ -d "$SWITCH_DIR/core" && -f "$SWITCH_DIR/deploy/local/docker-compose.yml" ]] || fail "Switch source checkout not found at $SWITCH_DIR. Set SWITCH_DIR to its path."
[[ -f "$SWITCH_DIR/.env" ]] || fail "Switch .env is missing. In the Switch checkout, run 'just init-env' once and retain the generated credentials."

echo "Starting MergeMind + local Switch demo stack"
echo "  MergeMind: http://127.0.0.1:$MM_PORT"
echo "  Switch API: http://127.0.0.1:$SWITCH_PORT"
echo "  Switch Gateway: http://127.0.0.1:$GATEWAY_PORT"

echo "[1/4] Starting persistent Switch database"
docker compose -f "$SWITCH_DIR/deploy/local/docker-compose.yml" --project-directory "$SWITCH_DIR" up -d postgres init-db

echo "[2/4] Starting Switch core API"
start_bg switch-core "$SWITCH_PORT" bash -lc "cd '$SWITCH_DIR' && set -a && source .env && set +a && exec uv run --project core python -m switch_core.main"
wait_http "http://127.0.0.1:$SWITCH_PORT/health" "Switch core"

echo "[3/4] Starting Switch Gateway UI"
if [[ ! -d "$SWITCH_DIR/gateway/node_modules" ]]; then
  (cd "$SWITCH_DIR/gateway" && npm ci)
fi
start_bg switch-gateway "$GATEWAY_PORT" bash -lc "cd '$SWITCH_DIR/gateway' && exec npm run dev -- --host 127.0.0.1 --port '$GATEWAY_PORT'"
wait_http "http://127.0.0.1:$GATEWAY_PORT/login" "Switch Gateway"

echo "[4/4] Starting MergeMind"
start_bg mergemind "$MM_PORT" bash -lc "cd '$ROOT' && exec .venv/bin/uvicorn backend.app.main:app --host 127.0.0.1 --port '$MM_PORT'"
wait_http "http://127.0.0.1:$MM_PORT/health" "MergeMind"

if command -v ollama >/dev/null && curl -fsS --max-time 2 http://127.0.0.1:11434/api/tags >/dev/null 2>&1; then
  echo "  ready: Ollama local model service"
else
  echo "  NOTE: Ollama is not responding. Start Ollama and pull the configured model before a live workflow."
fi

echo
echo "Stack is up. Next:"
echo "  1. Sign in to Switch Gateway: http://127.0.0.1:$GATEWAY_PORT"
echo "  2. Create a registration key and a room (see docs/local-demo.md)."
echo "  3. Unlock MergeMind at http://127.0.0.1:$MM_PORT using MERGEMIND_ADMIN_TOKEN from $ROOT/.env."
echo "  4. Register the five agents, add them to the room, and wait for 5/5 connected."
echo "Logs and PID files: $LOG_DIR"
