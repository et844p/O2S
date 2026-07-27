#!/usr/bin/env bash
set -euo pipefail

INSTALL_ONLY=false
RUN_AUTH=false

for arg in "$@"; do
  case "$arg" in
    --install-only) INSTALL_ONLY=true ;;
    --auth) RUN_AUTH=true ;;
  esac
done

CONFIG_DIR="${HOME}/.config/google-workspace-mcp"
CREDENTIALS_FILE="${CONFIG_DIR}/credentials.json"
TOKEN_FILE="${CONFIG_DIR}/tokens.json"

log() {
  printf '[google-drive-setup] %s\n' "$*"
}

ensure_npx_package() {
  log "Prefetching @dguido/google-workspace-mcp..."
  npx -y @dguido/google-workspace-mcp version >/dev/null
}

write_credentials_file() {
  local client_id="${GOOGLE_CLIENT_ID:-}"
  local client_secret="${GOOGLE_CLIENT_SECRET:-}"

  if [[ -z "$client_id" || -z "$client_secret" ]]; then
    return 1
  fi

  mkdir -p "$CONFIG_DIR"
  cat >"$CREDENTIALS_FILE" <<EOF
{
  "installed": {
    "client_id": "${client_id}",
    "client_secret": "${client_secret}",
    "redirect_uris": ["http://localhost"]
  }
}
EOF
  chmod 600 "$CREDENTIALS_FILE"
  log "Wrote OAuth credentials to ${CREDENTIALS_FILE}"
}

print_next_steps() {
  cat <<'EOF'

Google Drive is configured but not authenticated yet.

1. Create a Google Cloud OAuth Desktop app:
   https://console.cloud.google.com/apis/credentials
   Enable APIs:
   https://console.cloud.google.com/flows/enableapi?apiid=drive.googleapis.com,docs.googleapis.com,sheets.googleapis.com

2. Add these secrets in Cursor:
   https://cursor.com/dashboard/cloud-agents
   - GOOGLE_CLIENT_ID
   - GOOGLE_CLIENT_SECRET

3. Re-run this setup script with auth:
   bash scripts/setup_google_drive.sh --auth

   Or authenticate locally in Cursor; the MCP server opens a browser on first use.

EOF
}

ensure_npx_package

if write_credentials_file; then
  :
else
  if [[ "$INSTALL_ONLY" == true ]]; then
    log "GOOGLE_CLIENT_ID / GOOGLE_CLIENT_SECRET not set yet; skipping auth."
    exit 0
  fi
  print_next_steps
  exit 1
fi

if [[ "$INSTALL_ONLY" == true && "$RUN_AUTH" == false ]]; then
  log "Credentials found. Run with --auth to complete Google sign-in."
  exit 0
fi

if [[ "$RUN_AUTH" == true || "$INSTALL_ONLY" == false ]]; then
  log "Starting Google OAuth flow..."
  if [[ -n "${CURSOR_CLOUD:-}" || -n "${CLOUD_AGENT_BC_ID:-}" ]]; then
    log "Cloud agent detected. If a browser cannot open, copy the auth URL from the output below."
  fi
  npx -y @dguido/google-workspace-mcp auth
  if [[ -f "$TOKEN_FILE" ]]; then
    log "Authentication complete. Tokens saved to ${TOKEN_FILE}"
  else
    log "Auth finished, but token file was not found at ${TOKEN_FILE}"
    exit 1
  fi
fi
