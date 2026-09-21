#!/usr/bin/env bash
set -Eeuo pipefail
if (( EUID != 0 )); then exec sudo bash "$0" "$@"; fi
IMAGE="${1:?image required}"
VERSION="${2:-0.3.7-alpha}"

# First preserve every 0.3.6 structural/regression gate.
bash "$(dirname "$0")/validate-0.3.6-image.sh" "$IMAGE" "$VERSION"

RAW="/tmp/PU2PNY-${VERSION}-validate-037.img"
ROOT="/mnt/pu2pny-os-037"
LOOP=""
cleanup(){
  set +e
  mountpoint -q "$ROOT" && umount "$ROOT" 2>/dev/null || true
  test -n "$LOOP" && losetup -d "$LOOP" 2>/dev/null || true
  rm -f "$RAW"
}
trap cleanup EXIT
trap 'echo "0.3.7 validation failed at line $LINENO: $BASH_COMMAND" >&2' ERR

xz -dc "$IMAGE" >"$RAW"
LOOP="$(losetup --find --partscan --show "$RAW")"
for _ in {1..60}; do test -b "${LOOP}p2" && break; sleep .25; done
mkdir -p "$ROOT"; mount "${LOOP}p2" "$ROOT"

echo '[0.3.7/1] Direct components'
test -x "$ROOT/usr/local/bin/2pny-direct-core"
test -x "$ROOT/usr/local/sbin/2pny-direct-start"
test -s "$ROOT/etc/systemd/system/2pny-direct.service"
test -L "$ROOT/etc/systemd/system/multi-user.target.wants/2pny-direct.service"
test -s "$ROOT/usr/share/2pny/direct.html"
grep -Fq '/api/direct/call' "$ROOT/usr/local/bin/2pnyd" || strings "$ROOT/usr/local/bin/2pnyd" | grep -Fq '/api/direct/call'
grep -Fq "['/direct','Direct','direct']" "$ROOT/usr/share/2pny/ui-common-0.3.0.js"
grep -Fq 'CGNAT' "$ROOT/usr/share/2pny/direct.html"
file "$ROOT/usr/local/bin/2pny-direct-core" | grep -Eq 'ELF 64-bit.*ARM aarch64|ELF 64-bit.*ARM64'
test ! -e "$ROOT/var/lib/2pny/direct/identity.json"
test ! -e "$ROOT/var/lib/2pny/direct/peers.json"

echo '[0.3.7/2] Direct crypto self-test'
chroot "$ROOT" /usr/local/bin/2pny-direct-core --selftest | grep -Fq DIRECT_SELFTEST_OK

echo '[0.3.7/3] D-Star audio/link voice payload'
test -x "$ROOT/usr/local/bin/dgwvoicetransmit"
test -d "$ROOT/usr/share/2pny/audio/dstar"
test "$(find "$ROOT/usr/share/2pny/audio/dstar" -maxdepth 1 -type f -name '*.ambe' | wc -l)" -ge 8
test "$(find "$ROOT/usr/share/2pny/audio/dstar" -maxdepth 1 -type f -name '*.indx' | wc -l)" -ge 8
test -s "$ROOT/usr/share/2pny/audio/dstar/en_GB.ambe"
test -s "$ROOT/usr/share/2pny/audio/dstar/en_GB.indx"
grep -Fq 'audio_path="/usr/share/2pny/audio/dstar/"' "$ROOT/usr/local/sbin/2pny-protocol-network-apply"
grep -Fq 'Data={audio_path}' "$ROOT/usr/local/sbin/2pny-protocol-network-apply"

echo '[0.3.7/4] Display Moderno V2'
grep -Fq 'PU2PNY Moderno V2' "$ROOT/usr/local/sbin/2pny-display-core"
grep -Fq 'Graphical 128x64 renderer' "$ROOT/usr/local/sbin/2pny-display-core"
grep -Fq 'PU2PNY Moderno V2' "$ROOT/usr/share/2pny/display.html"

echo '[0.3.7/5] DMR baseline remains intact'
strings "$ROOT/usr/local/bin/DMRGateway" | grep -Fq 'PU2PNY, XLX module control'
strings "$ROOT/usr/local/bin/DMRGateway" | grep -Fq 'PU2PNY, XLX status voice requested'

echo "PU2PNY-OS $VERSION ARM64: 0.3.6 regression gates + 0.3.7 Direct/D-Star/Display structural gates PASS"
