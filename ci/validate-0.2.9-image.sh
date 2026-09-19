#!/usr/bin/env bash
set -euo pipefail
if (( EUID != 0 )); then exec sudo bash "$0" "$@"; fi
IMAGE="${1:?image required}"
VERSION="${2:-0.2.9-alpha}"
RAW="/tmp/PU2PNY-${VERSION}-validate.img"
ROOT="/mnt/pu2pny-os-029"
LOOP=""; PID=""
cleanup(){
  set +e
  test -n "$PID" && kill "$PID" 2>/dev/null || true
  umount "$ROOT/proc" "$ROOT/dev" "$ROOT/sys" "$ROOT/boot/firmware" "$ROOT" 2>/dev/null || true
  test -n "$LOOP" && losetup -d "$LOOP" 2>/dev/null || true
  rm -f "$RAW" /tmp/pu2pnyd-029.log
}
trap cleanup EXIT
trap 'echo "Validation failed at line $LINENO: $BASH_COMMAND" >&2' ERR

echo '[1/12] image integrity'
xz -t "$IMAGE"
EXPECTED="$(awk '{print $1}' "$IMAGE.sha256")"; ACTUAL="$(sha256sum "$IMAGE"|awk '{print $1}')"
test "$EXPECTED" = "$ACTUAL"
xz -dc "$IMAGE" >"$RAW"
LOOP="$(losetup --find --partscan --show "$RAW")"
for _ in {1..40}; do test -b "${LOOP}p2" && break; sleep .25; done
mkdir -p "$ROOT"; mount "${LOOP}p2" "$ROOT"; mkdir -p "$ROOT/boot/firmware"; mount "${LOOP}p1" "$ROOT/boot/firmware"

echo '[2/12] identity and modular sources'
grep -Fxq "$VERSION" "$ROOT/etc/2pny/version"
grep -Fxq 'pu2pny' "$ROOT/etc/hostname"
grep -Fq '0.2.9-alpha' "$ROOT/usr/share/2pny/dashboard.html"
grep -Fq '0.2.9-alpha' "$ROOT/usr/share/2pny/wizard.html"

echo '[3/12] runtime module syntax'
for x in 2pny-network-core 2pny-network-switch 2pny-hostfiles-update 2pny-rf-apply 2pny-mode-apply; do
  test -x "$ROOT/usr/local/sbin/$x"; bash -n "$ROOT/usr/local/sbin/$x"
done
for x in 2pny-station-worker 2pny-display-core 2pny-display-apply 2pny-server-catalog 2pny-protocol-network-apply 2pny-aprs; do
  test -x "$ROOT/usr/local/sbin/$x"; python3 -m py_compile "$ROOT/usr/local/sbin/$x"
done
python3 -m py_compile "$ROOT/usr/local/lib/2pny-live-core.py" "$ROOT/usr/local/libexec/2pny-dmr-apply"
rm -rf "$ROOT/usr/local/sbin/__pycache__" "$ROOT/usr/local/lib/__pycache__" "$ROOT/usr/local/libexec/__pycache__"

echo '[4/12] Wi-Fi first-install contract'
SW="$ROOT/usr/local/sbin/2pny-network-switch"; WIZ="$ROOT/usr/share/2pny/wizard.html"
grep -Fq 'wifi-country' "$SW"
grep -Fq 'for attempt in 1 2 3' "$SW"
grep -Fq 'try_hidden_connect' "$SW"
grep -Fq 'restore_on_error' "$SW"
grep -Fq 'País / região do Wi' "$WIZ"
grep -Fq 'reconnectOverlay' "$WIZ"
grep -Fq 'pu2pny.local/wizard?step=2' "$WIZ"

echo '[5/12] RadioID database and operator-first UI'
WORKER="$ROOT/usr/local/sbin/2pny-station-worker"; DASH="$ROOT/usr/share/2pny/dashboard.html"
grep -Fq 'operators.sqlite' "$WORKER"
grep -Fq 'https://radioid.net/api/dmr/user/' "$WORKER"
grep -Fq 'CREATE TABLE IF NOT EXISTS contacts' "$WORKER"
grep -Fq 'operatorView' "$DASH"
grep -Fq 'Nome do operador' "$DASH"
grep -Fq 'O painel não exibe o ID digital' "$DASH"
! grep -Fq 'Indicativo / ID' "$DASH"

echo '[6/12] complete local flag pack'
test -f "$ROOT/usr/share/2pny/flags/LICENSE-MIT"
COUNT="$(find "$ROOT/usr/share/2pny/flags/4x3" -maxdepth 1 -type f -name '*.svg' | wc -l)"
test "$COUNT" -ge 240
for cc in br us pt gb ar jp au za; do test -s "$ROOT/usr/share/2pny/flags/4x3/$cc.svg"; done

echo '[7/12] radio binaries and protocol modules'
for x in MMDVM-Host DMRGateway MMDVM-Display NextionUpdater dstargateway YSFGateway P25Gateway NXDNGateway DAPNETGateway; do
  test -x "$ROOT/usr/local/bin/$x"
done
for svc in 2pny-dmrgateway.service 2pny-dstargateway.service 2pny-ysfgateway.service 2pny-p25gateway.service 2pny-nxdngateway.service 2pny-dapnetgateway.service 2pny-display-core.service 2pny-station.service 2pny-aprs.service; do
  test -s "$ROOT/etc/systemd/system/$svc"
done

echo '[8/12] DMR voice and RF command support'
for lang in pt_PT en_GB es_ES; do
  test -s "$ROOT/usr/share/2pny/audio/dmrgateway/$lang.ambe"
  test -s "$ROOT/usr/share/2pny/audio/dmrgateway/$lang.indx"
done
strings "$ROOT/usr/local/bin/DMRGateway" | grep -Fq 'PU2PNY, XLX module control'
strings "$ROOT/usr/local/bin/DMRGateway" | grep -Fq 'PU2PNY, XLX status voice requested'
strings "$ROOT/usr/local/bin/DMRGateway" | grep -Fq 'PU2PNY, hourly time voice'

echo '[9/12] display and APRS modules'
grep -Fq 'ExecStart=/usr/local/sbin/2pny-display-core' "$ROOT/etc/systemd/system/2pny-display-core.service"
grep -Fq 'SSD1306' "$ROOT/usr/local/sbin/2pny-display-core"
grep -Fq 'nextion_mmdvm' "$ROOT/usr/local/sbin/2pny-display-core"
grep -Fq 'rotate.aprs2.net' "$ROOT/usr/local/sbin/2pny-aprs"
grep -Fq 'id="aprsEnabled"' "$ROOT/usr/share/2pny/dashboard.html"
grep -Fq '"/api/aprs"' "$ROOT/src/2pnyd/main.go" 2>/dev/null || grep -Fq 'APRS atualizado' "$ROOT/usr/share/2pny/dashboard.html"
grep -Fq 'dapnet.afu.rwth-aachen.de' "$ROOT/usr/local/sbin/2pny-server-catalog"
! grep -Fqi 'DPRS' "$ROOT/usr/local/sbin/2pny-aprs"

echo '[10/12] no leaked runtime/user state'
for p in \
 "$ROOT/var/lib/2pny/provisioned" "$ROOT/var/lib/2pny/rf-configured" \
 "$ROOT/var/lib/2pny/network-radio.json" "$ROOT/var/lib/2pny/network-connect.json" \
 "$ROOT/var/lib/2pny/station/operators.sqlite"; do test ! -e "$p"; done

echo '[11/12] boot web backend and local assets'
mkdir -p "$ROOT/proc" "$ROOT/dev" "$ROOT/sys" "$ROOT/run" "$ROOT/var/lib/2pny"
mount -t proc proc "$ROOT/proc"; mount --bind /dev "$ROOT/dev"; mount --bind /sys "$ROOT/sys"
chroot "$ROOT" /usr/local/bin/2pnyd >/tmp/pu2pnyd-029.log 2>&1 & PID=$!
OK=0
for _ in {1..80}; do
  if curl -fsS http://127.0.0.1/healthz 2>/dev/null | grep -q 'PU2PNY OK'; then OK=1; break; fi
  sleep .2
done
test "$OK" = 1 || { cat /tmp/pu2pnyd-029.log; exit 1; }
curl -fsS http://127.0.0.1/api/status | grep -Fq '"version":"0.2.9-alpha"'
curl -fsS http://127.0.0.1/api/network/country | grep -Fq '"country":"BR"'
curl -fsS http://127.0.0.1/flags/4x3/br.svg | grep -Eq '<svg|<SVG'
kill "$PID"; PID=""

echo '[12/12] final result'
echo "PU2PNY-OS $VERSION ARM64 image: OK"
