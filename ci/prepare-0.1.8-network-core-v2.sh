#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-.}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Keep one implementation of the network core. The previous v2 implementation
# duplicated the runtime and regressed Wi-Fi handoff, interface discovery and
# watchdog stability. The canonical implementation renders daemon configs for
# the detected interfaces and only resets an AP during startup or recovery.
bash "$SCRIPT_DIR/prepare-0.1.8-network-core.sh" "$ROOT"

echo '2PNY 0.1.8 network core v2 compatibility layer applied'
