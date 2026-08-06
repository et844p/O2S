#!/usr/bin/env bash
# Push all branches to et844p_wayfair/O2S (create that empty repo on GitHub first).
set -euo pipefail
WAYFAIR_URL="https://github.com/et844p_wayfair/O2S.git"

if ! git remote | grep -q '^wayfair$'; then
  git remote add wayfair "$WAYFAIR_URL"
fi
git remote set-url wayfair "$WAYFAIR_URL"

echo "Pushing all branches to et844p_wayfair/O2S ..."
git push wayfair --all
git push wayfair --tags 2>/dev/null || true
echo "Done. Set origin to wayfair if desired:"
echo "  git remote set-url origin $WAYFAIR_URL"
