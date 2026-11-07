#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="$ROOT/.env"
MM_PORT="${MERGEMIND_PORT:-8001}"
[[ -f "$ENV_FILE" ]] || { echo "Missing $ENV_FILE; run scripts/setup.sh first." >&2; exit 1; }
read -rp "Switch agent bridge base URL [http://127.0.0.1:8000]: " BASE_URL
BASE_URL="${BASE_URL:-http://127.0.0.1:8000}"
read -rp "Switch room ID: " ROOM_ID
[[ -n "$ROOM_ID" ]] || { echo "Room ID is required." >&2; exit 1; }
read -rsp "Switch registration key (input hidden): " REGISTRATION_KEY
echo
[[ -n "$REGISTRATION_KEY" ]] || { echo "Registration key is required." >&2; exit 1; }

TMP_ROOT="${XDG_RUNTIME_DIR:-${TMPDIR:-/tmp}}"
KEY_FILE="$(mktemp "$TMP_ROOT/mergemind-registration.XXXXXX")"
chmod 600 "$KEY_FILE"
cleanup() { rm -f "$KEY_FILE"; unset REGISTRATION_KEY; }
trap cleanup EXIT
printf '%s' "$REGISTRATION_KEY" >"$KEY_FILE"
unset REGISTRATION_KEY

python3 - "$ENV_FILE" "$BASE_URL" "$ROOM_ID" "$KEY_FILE" "$MM_PORT" <<'PY'
import json, sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

env_path, base_url, room_id, key_path, port = sys.argv[1:6]
values = {}
for line in Path(env_path).read_text().splitlines():
    if "=" in line and not line.lstrip().startswith("#"):
        key, value = line.split("=", 1)
        values[key] = value.strip().strip('"').strip("'")
admin = values.get("MERGEMIND_ADMIN_TOKEN", "")
registration = Path(key_path).read_text()
if not admin or not registration:
    raise SystemExit("Admin token or registration key is missing.")
payload = json.dumps({
    "base_url": base_url.rstrip("/"),
    "registration_key": registration,
    "room_id": room_id.strip(),
}).encode()
request = Request(
    "http://127.0.0.1:" + port + "/api/switch/register",
    data=payload,
    headers={
        "Content-Type": "application/json",
        "X-MergeMind-Admin-Token": admin,
    },
)
try:
    with urlopen(request, timeout=90) as response:
        result = json.load(response)
except HTTPError as error:
    detail = error.read().decode("utf-8", "replace")
    raise SystemExit(f"Switch registration failed (HTTP {error.code}): {detail}")
except URLError as error:
    raise SystemExit(f"Could not reach MergeMind on 127.0.0.1:{port}: {error}")
print(f"Registered roles: {result.get('total_roles', 'unknown')}")
print(result.get("next_step", "Open MergeMind and verify the agent connection status."))
PY
