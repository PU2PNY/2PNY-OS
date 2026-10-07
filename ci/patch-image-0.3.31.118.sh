#!/bin/bash
set -euo pipefail
ROOT="${1:?root mount required}"
NEXTION_BIN="${2:?hardened NextionDriver binary required}"

test -x "$NEXTION_BIN"
test "$(cat "$ROOT/etc/2pny/version")" = '0.3.31.117'
test -f "$ROOT/etc/systemd/system/2pny-nextiondriver.service"
test -f "$ROOT/usr/local/sbin/2pny-display-apply"

grep -Fq 'User=mmdvm' "$ROOT/etc/systemd/system/2pny-nextiondriver.service"
grep -Fq 'RuntimeDirectory=2pny-nextiondriver' "$ROOT/etc/systemd/system/2pny-nextiondriver.service"
grep -Fq '/run/2pny-nextiondriver/ttyNextionDriver' "$ROOT/usr/local/sbin/2pny-display-apply"

# DISPLAY-026: only replace the ON7LDS binary with the build whose virtual PTY
# link lives in the unprivileged systemd RuntimeDirectory. No service, RF,
# gateway, UI, network or MMDVMHost configuration is changed by this overlay.
install -m 0755 "$NEXTION_BIN" "$ROOT/usr/local/bin/NextionDriver-pu2pny"
printf '0.3.31.118\n' >"$ROOT/etc/2pny/version"

test "$(cat "$ROOT/etc/2pny/version")" = '0.3.31.118'
strings "$ROOT/usr/local/bin/NextionDriver-pu2pny" | grep -Fq '/run/2pny-nextiondriver/ttyNextionDriver'
if strings "$ROOT/usr/local/bin/NextionDriver-pu2pny" | grep -Fq '/dev/ttyNextionDriver'; then
  echo 'legacy /dev NextionDriver link remains in binary' >&2
  exit 1
fi

echo PATCH_IMAGE_0331118_OK
