#!/usr/bin/env bash
set -euo pipefail
if (( EUID != 0 )); then exec sudo bash "$0" "$@"; fi
IMAGE="${1:?image required}"
VERSION="${2:-0.3.20-alpha}"
RAW="/tmp/PU2PNY-${VERSION}-validate-0320.img"
ROOT="/mnt/pu2pny-os-0320"
LOOP=""; PID=""
cleanup(){
  set +e
  test -n "$PID" && kill "$PID" 2>/dev/null || true
  umount "$ROOT/proc" "$ROOT/dev" "$ROOT/sys" "$ROOT/boot/firmware" "$ROOT" 2>/dev/null || true
  test -n "$LOOP" && losetup -d "$LOOP" 2>/dev/null || true
  rm -f "$RAW" /tmp/pu2pnyd-0320.log
}
trap cleanup EXIT
trap 'echo "Validation failed at line $LINENO: $BASH_COMMAND" >&2' ERR

echo '[1/9] integrity'
xz -t "$IMAGE"
EXPECTED="$(awk '{print $1}' "$IMAGE.sha256")"; ACTUAL="$(sha256sum "$IMAGE"|awk '{print $1}')"
test "$EXPECTED" = "$ACTUAL"
xz -dc "$IMAGE" >"$RAW"
LOOP="$(losetup --find --partscan --show "$RAW")"
for _ in {1..60}; do test -b "${LOOP}p2" && break; sleep .25; done
mkdir -p "$ROOT"; mount "${LOOP}p2" "$ROOT"; mkdir -p "$ROOT/boot/firmware"; mount "${LOOP}p1" "$ROOT/boot/firmware"

echo '[2/9] identity and protected baseline'
grep -Fxq "$VERSION" "$ROOT/etc/2pny/version"
grep -Fxq 'pu2pny' "$ROOT/etc/hostname"
test -x "$ROOT/usr/local/bin/MMDVM-Host"
test -x "$ROOT/usr/local/bin/DMRGateway"
test -x "$ROOT/usr/local/bin/dstargateway"
test -x "$ROOT/usr/local/bin/YSFGateway"
strings "$ROOT/usr/local/bin/DMRGateway" | grep -Fq 'PU2PNY, XLX module control'
strings "$ROOT/usr/local/bin/DMRGateway" | grep -Fq 'PU2PNY, system voice priority'
test -s "$ROOT/usr/local/share/dstargateway.d/en_GB.ambe"
test -s "$ROOT/usr/local/share/dstargateway.d/en_GB.indx"

echo '[3/9] runtime syntax'
for x in 2pny-network-core 2pny-network-switch 2pny-wifi-profiles 2pny-auto-maintenance 2pny-hostfiles-update 2pny-rf-apply 2pny-mode-apply 2pny-display-online-detect; do
  test -x "$ROOT/usr/local/sbin/$x"; bash -n "$ROOT/usr/local/sbin/$x"
done
for x in 2pny-station-worker 2pny-hardware-probe 2pny-display-core 2pny-display-status 2pny-display-apply 2pny-display-detector 2pny-server-catalog 2pny-protocol-network-apply 2pny-protocol-profiles 2pny-update-manager 2pny-mqtt-preflight 2pny-aprs 2pny-netdiag 2pny-timezone-apply; do
  test -x "$ROOT/usr/local/sbin/$x"; python3 -m py_compile "$ROOT/usr/local/sbin/$x"
done
python3 -m py_compile "$ROOT/usr/local/lib/2pny-live-core.py" "$ROOT/usr/local/libexec/2pny-dmr-apply"
rm -rf "$ROOT/usr/local/sbin/__pycache__" "$ROOT/usr/local/lib/__pycache__" "$ROOT/usr/local/libexec/__pycache__"

echo '[4/9] 0.3.20 focused contracts'
HOT="$ROOT/usr/share/2pny/hotspot.html"; DASH="$ROOT/usr/share/2pny/dashboard.html"; UI="$ROOT/usr/share/2pny/ui-common-0.3.0.js"
DSTAR="$ROOT/usr/local/sbin/2pny-protocol-network-apply"; STATION="$ROOT/usr/local/sbin/2pny-station-worker"
grep -Fq 'B (padrão PU2PNY)' "$HOT"
grep -Fq 'id="dstarLocalModule"' "$HOT"
grep -Fq 'DSTAR_LOCAL=' "$DSTAR"
grep -Fq '"Module":dstar_local if proto=="DSTAR"' "$DSTAR"
grep -Fq 'Band={dstar_local}' "$DSTAR"
grep -Fq 'XLXHosts.txt' "$DSTAR"
grep -Fq 'requested_server' "$STATION"
grep -Fq 'is unknown, ignoring link request' "$STATION"
grep -Fq 'observeProtocolConnection' "$HOT"
! grep -Fq 'waitProtocolConnection' "$HOT"
grep -Fq 'families:[['"'"'XLX'"'"','"'"'XLX'"'"'],['"'"'BrandMeister'"'"','"'"'BrandMeister'"'"']' "$HOT"
grep -Fq 'pny-real-hidden' "$UI"
grep -Fq 'tot-warn' "$DASH"; grep -Fq 'tot-danger' "$DASH"
grep -Fq '9+30' "$DASH"

echo '[5/9] DMR/YSF regression structure'
DMR="$ROOT/usr/local/libexec/2pny-dmr-apply"
grep -Fq 'duplex=1 if usemode=="repeater" else 0' "$DMR"
grep -Fq 'slot1=True if duplex' "$DMR"; grep -Fq 'slot2=True if duplex' "$DMR"
grep -Fq 'route_slots=(1,2) if duplex' "$DMR"
grep -Fq 'if kind.lower()=="xlx": essid=""' "$DMR"
grep -Fq 'CYSFReflectors::findByName' "$DSTAR"
grep -Fq 'startup_name' "$DSTAR"
grep -Fq 'WiresXCommandPassthrough=0' "$DSTAR"

echo '[6/9] Nextion, APRS, clock, logs and OTA'
DET="$ROOT/usr/local/sbin/2pny-display-detector"; DAP="$ROOT/usr/local/sbin/2pny-display-apply"
grep -Fq 'host/display-in' "$DET"; grep -Fq 'host/display-out' "$DET"
grep -Fq '"physical_confirmed":True' "$DET"
grep -Fq 'renderer="pu2pny-modern-v2"' "$DAP"
grep -Fq 'DISPLAY_NOT_CONFIRMED' "$DAP"
grep -Fq '<h1>APRS</h1>' "$ROOT/usr/share/2pny/aprs.html"
for cmd in PING STATUS LAST MYLAST ONLINE MODULE INFO HELP; do grep -Fq "$cmd" "$ROOT/usr/local/sbin/2pny-aprs"; done
strings "$ROOT/usr/local/bin/2pnyd" | grep -Fq '/api/system/timezones'
strings "$ROOT/usr/local/bin/2pnyd" | grep -Fq '/api/diagnostics/errors/download'
grep -Fq 'datetime-local' "$ROOT/usr/share/2pny/system.html"
grep -Fq 'Instalar agora' "$ROOT/usr/share/2pny/system.html"
grep -Fq 'Instalar depois' "$ROOT/usr/share/2pny/system.html"
grep -Fq 'state="rolled_back"' "$ROOT/usr/local/sbin/2pny-update-manager"

echo '[7/9] Direct and no leaked runtime state'
test -x "$ROOT/usr/local/bin/2pny-direct-core"
chroot "$ROOT" /usr/local/bin/2pny-direct-core --selftest | grep -Fq DIRECT_SELFTEST_OK
for p in "$ROOT/var/lib/2pny/provisioned" "$ROOT/var/lib/2pny/rf-configured" "$ROOT/var/lib/2pny/network-radio.json" "$ROOT/var/lib/2pny/wifi-country"; do test ! -e "$p"; done

echo '[8/9] backend boot/API'
mkdir -p "$ROOT/proc" "$ROOT/dev" "$ROOT/sys" "$ROOT/run" "$ROOT/var/lib/2pny"
mount -t proc proc "$ROOT/proc"; mount --bind /dev "$ROOT/dev"; mount --bind /sys "$ROOT/sys"
chroot "$ROOT" /usr/local/bin/2pnyd >/tmp/pu2pnyd-0320.log 2>&1 & PID=$!
OK=0
for _ in {1..100}; do
  if curl -fsS http://127.0.0.1/healthz 2>/dev/null | grep -q 'PU2PNY OK'; then OK=1; break; fi
  sleep .2
done
test "$OK" = 1 || { cat /tmp/pu2pnyd-0320.log; exit 1; }
curl -fsS http://127.0.0.1/api/status | grep -Fq "\"version\":\"$VERSION\""
strings "$ROOT/usr/local/bin/2pnyd" | grep -Fq '0.3.20-alpha'
kill "$PID"; wait "$PID" 2>/dev/null || true; PID=""

echo '[9/9] final'
echo "PU2PNY-OS $VERSION ARM64 image: SW/structural gates PASS; RF/Nextion/duplex remain HW PENDING"
