#!/usr/bin/env bash
set -euo pipefail

IMAGE="${1:?image required}"
VERSION="${2:-0.2.3-alpha}"
RAW="/tmp/PU2PNY-${VERSION}-validate.img"
ROOT="/mnt/pu2pny-023"
PID=""
LOOP=""

cleanup(){
  set +e
  test -n "$PID" && sudo kill "$PID" 2>/dev/null || true
  sudo umount "$ROOT/proc" "$ROOT/dev" "$ROOT/sys" "$ROOT/boot/firmware" "$ROOT" 2>/dev/null || true
  test -n "$LOOP" && sudo losetup -d "$LOOP" 2>/dev/null || true
  sudo rm -f "$RAW" /tmp/pu2pnyd-023.log
}
trap cleanup EXIT

echo '[1/12] Integrity and partitions'
xz -t "$IMAGE"
EXPECTED="$(awk '{print $1}' "$IMAGE.sha256")"
ACTUAL="$(sha256sum "$IMAGE" | awk '{print $1}')"
test -n "$EXPECTED" && test "$EXPECTED" = "$ACTUAL"
sudo sh -c "xz -dc '$IMAGE' > '$RAW'"
LOOP="$(sudo losetup --find --partscan --show "$RAW")"
for _ in {1..30}; do test -b "${LOOP}p2" && break; sleep .25; done
test -b "${LOOP}p1" && test -b "${LOOP}p2"
sudo mkdir -p "$ROOT"
sudo mount "${LOOP}p2" "$ROOT"
sudo mkdir -p "$ROOT/boot/firmware"
sudo mount "${LOOP}p1" "$ROOT/boot/firmware"

echo '[2/12] Identity'
grep -q '^VERSION_CODENAME=bookworm$' "$ROOT/etc/os-release"
grep -Fxq "$VERSION" "$ROOT/etc/2pny/version"
grep -Fxq 'pu2pny' "$ROOT/etc/hostname"

echo '[3/12] Source/runtime essentials'
test -x "$ROOT/usr/local/bin/2pnyd"
test -x "$ROOT/usr/local/sbin/2pny-network-switch"
test -x "$ROOT/usr/local/sbin/2pny-rf-apply"
test -x "$ROOT/usr/local/sbin/2pny-hardware-probe"
bash -n "$ROOT/usr/local/sbin/2pny-network-switch"
bash -n "$ROOT/usr/local/sbin/2pny-rf-apply"
python3 -m py_compile "$ROOT/usr/local/sbin/2pny-hardware-probe"
sudo rm -rf "$ROOT/usr/local/sbin/__pycache__"

echo '[4/12] Wi-Fi scan recovery'
SW="$ROOT/usr/local/sbin/2pny-network-switch"
grep -Fq 'systemctl stop 2pny-network-core.service' "$SW"
grep -Fq 'systemctl restart 2pny-network-core.service' "$SW"
grep -Fq 'nmcli device wifi rescan' "$SW"
grep -Fq 'scan_json()' "$SW"
grep -Fq 'SETUP_CIDR=10.43.0.1/24' "$SW"

echo '[5/12] Wizard UX and frequency guard'
WIZ="$ROOT/usr/share/2pny/wizard.html"
grep -Fq '0.2.3-alpha' "$WIZ"
grep -Fq 'Alterar rede' "$WIZ"
grep -Fq 'Abrir painel principal' "$WIZ"
grep -Fq 'txWrap' "$WIZ"
grep -Fq 'syncUseMode' "$WIZ"
grep -Fq '/api/wifi/scan' "$WIZ"
grep -Fq 'A placa Wi‑Fi está sendo usada para a busca' "$WIZ"
grep -Fq 'http://pu2pny.local/' "$WIZ"
! grep -Fq 'PU2PNY pronto para usar' "$WIZ"

echo '[6/12] Dashboard'
DASH="$ROOT/usr/share/2pny/dashboard.html"
test -s "$DASH"
grep -Fq 'Painel principal' "$DASH"
grep -Fq '/api/dashboard' "$DASH"
grep -Fq '/wizard?step=1' "$DASH"
grep -Fq 'Atividade recente' "$DASH"
grep -Fq 'Hotspot simplex — RX e TX iguais' "$DASH"

echo '[7/12] Nextion compatibility'
RF="$ROOT/usr/local/sbin/2pny-rf-apply"
grep -Fq 'Display=Nextion' "$RF"
grep -Fq 'ScreenLayout=2' "$RF"
grep -Fq 'Brightness=80' "$RF"
grep -Fq 'display-runtime.json' "$RF"
grep -Fq 'CONFIG=/var/lib/2pny/mmdvm/MMDVM-Host.ini' "$RF"
! grep -Fq 'CONFIG=/etc/2pny/mmdvm/MMDVM-Host.ini' "$RF"

echo '[8/12] Clean first boot'
test ! -e "$ROOT/var/lib/2pny/provisioned"
test ! -e "$ROOT/var/lib/2pny/wifi-scan.json"
test ! -e "$ROOT/var/lib/2pny/network-connect.json"
test ! -e "$ROOT/var/lib/2pny/display-runtime.json"

echo '[9/12] Start panel inside final image'
sudo mkdir -p "$ROOT/proc" "$ROOT/dev" "$ROOT/sys" "$ROOT/run" "$ROOT/var/lib/2pny"
sudo mount -t proc proc "$ROOT/proc"
sudo mount --bind /dev "$ROOT/dev"
sudo mount --bind /sys "$ROOT/sys"
sudo chroot "$ROOT" /usr/local/bin/2pnyd >/tmp/pu2pnyd-023.log 2>&1 & PID=$!
OK=0
for _ in {1..50}; do
  if curl -fsS http://127.0.0.1/healthz 2>/dev/null | grep -q 'PU2PNY OK'; then OK=1; break; fi
  sleep .2
done
test "$OK" = 1 || { cat /tmp/pu2pnyd-023.log; exit 1; }

echo '[10/12] First access routes to wizard'
CODE="$(curl -sS -o /dev/null -w '%{http_code}' http://127.0.0.1/)"
test "$CODE" = 302
LOC="$(curl -sSI http://127.0.0.1/ | awk 'BEGIN{IGNORECASE=1}/^Location:/{gsub("\r","");print $2}')"
test "$LOC" = /wizard
CODE="$(curl -sS -o /dev/null -w '%{http_code}' http://127.0.0.1/dashboard)"
test "$CODE" = 302
curl -fsS http://127.0.0.1/wizard | grep -Fq '0.2.3-alpha'
STATUS="$(curl -fsS http://127.0.0.1/api/status)"
echo "$STATUS" | grep -Fq '"version":"0.2.3-alpha"'
echo "$STATUS" | grep -Fq '"provisioned":false'

echo '[11/12] Configured system routes to dashboard'
sudo touch "$ROOT/var/lib/2pny/provisioned"
CODE="$(curl -sS -o /dev/null -w '%{http_code}' http://127.0.0.1/)"
test "$CODE" = 302
LOC="$(curl -sSI http://127.0.0.1/ | awk 'BEGIN{IGNORECASE=1}/^Location:/{gsub("\r","");print $2}')"
test "$LOC" = /dashboard
curl -fsS http://127.0.0.1/dashboard | grep -Fq 'Painel principal'
DATA="$(curl -fsS http://127.0.0.1/api/dashboard)"
echo "$DATA" | grep -Fq '"version":"0.2.3-alpha"'
echo "$DATA" | grep -Fq '"provisioned":true'
CAPTIVE="$(curl -fsS http://127.0.0.1/captive-api)"
echo "$CAPTIVE" | grep -q '"captive":false'
sudo rm -f "$ROOT/var/lib/2pny/provisioned"

echo '[12/12] Final result'
echo "PU2PNY $VERSION ARM64 image: OK"
