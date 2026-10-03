#!/bin/bash
set -euo pipefail
ROOT="${1:?root mount required}"
REPO="$(cd "$(dirname "$0")/.." && pwd)"
# Surgical rollback of the only regressed startup decision: restore the exact
# 0.3.30 profile-autostart behavior. No RF/protocol/display/network helper is touched.
install -m 0755 "$REPO/src/2pny-profile-autostart-0.3.28.py" "$ROOT/usr/local/sbin/2pny-profile-autostart"
printf '%s\n' '0.3.31.110' > "$ROOT/etc/2pny/version"
python3 -m py_compile "$ROOT/usr/local/sbin/2pny-profile-autostart"
cmp -s "$ROOT/usr/local/sbin/2pny-profile-autostart" "$REPO/src/2pny-profile-autostart-0.3.28.py"
test -e "$ROOT/etc/systemd/system/2pny-profile-proven.path"
echo PATCH_IMAGE_0331110_OK
