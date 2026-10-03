#!/bin/bash
set -euo pipefail
ROOT="${1:?root mount required}"
REPO="$(cd "$(dirname "$0")/.." && pwd)"
# Surgical hotfix: only the 0.3.31 proven-profile/autostart chain changes.
# RF/protocol/gateway/display/network/audio helpers remain byte-identical.
install -m 0755 "$REPO/src/2pny-profile-autostart-0.3.31.110.py" "$ROOT/usr/local/sbin/2pny-profile-autostart"
install -m 0755 "$REPO/src/2pny-profile-proven-0.3.31.110.py" "$ROOT/usr/local/sbin/2pny-profile-proven"
printf '%s\n' '0.3.31.110' > "$ROOT/etc/2pny/version"
python3 -m py_compile "$ROOT/usr/local/sbin/2pny-profile-autostart" "$ROOT/usr/local/sbin/2pny-profile-proven"
cmp -s "$ROOT/usr/local/sbin/2pny-profile-autostart" "$REPO/src/2pny-profile-autostart-0.3.31.110.py"
cmp -s "$ROOT/usr/local/sbin/2pny-profile-proven" "$REPO/src/2pny-profile-proven-0.3.31.110.py"
test -e "$ROOT/etc/systemd/system/2pny-profile-autostart.service"
test -e "$ROOT/etc/systemd/system/2pny-profile-proven.path"
test -e "$ROOT/etc/systemd/system/2pny-profile-proven.service"
echo PATCH_IMAGE_0331110_OK
