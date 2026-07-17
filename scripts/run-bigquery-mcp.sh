#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
source "$SCRIPT_DIR/bootstrap-gcp-credentials.sh"

exec npx -y @toolbox-sdk/server --prebuilt bigquery --stdio
