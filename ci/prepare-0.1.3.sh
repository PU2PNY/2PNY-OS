#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-.}"
SELF_DIR="$(cd "$(dirname "$0")" && pwd)"
bash "$SELF_DIR/prepare-0.1.3-live-status.sh" "$ROOT"
