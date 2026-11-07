#!/usr/bin/env bash
set -Eeuo pipefail
LOG_DIR="${XDG_STATE_HOME:-$HOME/.local/state}/mergemind-demo"
for name in mergemind switch-gateway switch-core; do
  pidfile="$LOG_DIR/$name.pid"
  if [[ -f "$pidfile" ]]; then
    pid="$(cat "$pidfile")"
    if [[ "$pid" =~ ^[0-9]+$ ]] && kill -0 "$pid" 2>/dev/null; then
      kill "$pid" && echo "Stopped $name (PID $pid)."
    fi
    rm -f "$pidfile"
  fi
done
echo "Switch PostgreSQL data is retained. Stop its containers separately only if needed:"
echo "  cd ${SWITCH_DIR:-$HOME/projects/hackathon/switch} && docker compose -f deploy/local/docker-compose.yml stop"
