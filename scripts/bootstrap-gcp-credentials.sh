#!/usr/bin/env bash
set -euo pipefail

CREDS_DIR="${GCP_CREDS_DIR:-/workspace/.gcp}"
CREDS_FILE="${GOOGLE_APPLICATION_CREDENTIALS_FILE:-$CREDS_DIR/service-account.json}"

mkdir -p "$CREDS_DIR"
chmod 700 "$CREDS_DIR"

if [[ -n "${GOOGLE_APPLICATION_CREDENTIALS:-}" && ! -f "${GOOGLE_APPLICATION_CREDENTIALS}" ]]; then
  if python3 -c "import json, os; json.loads(os.environ['GOOGLE_APPLICATION_CREDENTIALS'])" 2>/dev/null; then
    printf '%s' "$GOOGLE_APPLICATION_CREDENTIALS" > "$CREDS_FILE"
    chmod 600 "$CREDS_FILE"
  fi
fi

if [[ -f "$CREDS_FILE" ]]; then
  export GOOGLE_APPLICATION_CREDENTIALS="$CREDS_FILE"
fi
