#!/usr/bin/env bash
set -euo pipefail

IMAGE="${1:?image required}"
VERSION="${2:-0.2.4-alpha}"
RAW="/tmp/PU2PNY-${VERSION}-validate.img"
ROOT="/mnt/pu2pny-024"
PID=""
LOOP=""

cleanup(){
  set +e
  test -n "$PID" && sudo kill "$PID" 2>/dev/null || true
  sudo umount "$ROOT/proc" "$ROOT/dev" "$ROOT/sys" "$ROOT/boot/firmware" "$ROOT" 2>/dev/null || true
  test -n "$LOOP" && sudo losetup -d "$LOOP" 2>/dev/null || true
  sudo rm -f "$RAW" /tmp/pu2pnyd-024.log
}
trap cleanup EXIT

echo '[1/13] Image integrity'
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

echo '[2/13] OS identity'
grep -q '^VERSION_CODENAME=bookworm$' "$ROOT/etc/os-release"
grep -Fxq "$VERSION" "$ROOT/etc/2pny/version"
grep -Fxq 'pu2pny' "$ROOT/etc/hostname"

echo '[3/13] Wi-Fi command dispatcher regression'
SW="$ROOT/usr/local/sbin/2pny-network-switch"
test -x "$SW"
bash -n "$SW"
grep -Fq 'case "${1:-}" in' "$SW"
! grep -Fq 'case "\${1:-}" in' "$SW"
grep -Fq 'PU2PNY-WIFI-CANDIDATE' "$SW"
grep -Fq 'Não foi possível entrar na rede' "$SW"
grep -Fq 'rfkill unblock wifi' "$SW"
grep -Fq 'nmcli device wifi rescan' "$SW"
OUT="$(sudo chroot "$ROOT" /usr/local/sbin/2pny-network-switch scan-json)"
test "$OUT" = '[]'

echo '[4/13] Network and captive portal'
CORE="$ROOT/usr/local/sbin/2pny-network-core"
bash -n "$CORE"
grep -Fq 'SETUP_IP=10.43.0.1' "$CORE"
grep -Fq '2pny-auto-maintenance.service' "$CORE"
grep -q '^ssid=pu2pny$' "$ROOT/usr/share/2pny/network/hostapd.template"
for d in detectportal.firefox.com captive.gnome.org nmcheck.gnome.org connectivity-check.ubuntu.com network-test.debian.org; do
  grep -Fq "address=/$d/10.43.0.1" "$ROOT/usr/share/2pny/network/dnsmasq-ap.template"
done

echo '[5/13] Automatic maintenance is lightweight and optional'
MAINT="$ROOT/usr/local/sbin/2pny-auto-maintenance"
MSVC="$ROOT/etc/systemd/system/2pny-auto-maintenance.service"
bash -n "$MAINT"
test -x "$MAINT"
test -f "$ROOT/var/lib/2pny/auto-maintenance.enabled"
grep -Fq 'Nice=15' "$MSVC"
grep -Fq 'IOSchedulingClass=idle' "$MSVC"
grep -Fq 'CPUWeight=20' "$MSVC"
grep -Fq 'apt-get' "$MAINT"
! grep -Fq 'apt-get upgrade' "$MAINT"
! grep -Fq 'dist-upgrade' "$MAINT"
sudo chroot "$ROOT" /usr/local/sbin/2pny-auto-maintenance status | grep -q '"state"'

echo '[6/13] Nextion real detection and progress'
PROBE="$ROOT/usr/local/sbin/2pny-hardware-probe"
DISPLAY="$ROOT/usr/local/sbin/2pny-display-status"
python3 -m py_compile "$PROBE" "$DISPLAY"
sudo rm -rf "$ROOT/usr/local/sbin/__pycache__"
grep -Fq 'def probe_nextion_mmdvm' "$PROBE"
grep -Fq 'mmdvm_serial_confirmed' "$PROBE"
grep -Fq '0x80' "$PROBE"
grep -Fq 'comok' "$PROBE"
grep -Fq 'SERIAL = 0x80' "$DISPLAY"
grep -Fq 'def mmdvm_frame' "$DISPLAY"
grep -Fq 'def bridge_send' "$DISPLAY"
grep -Fq 'PU2PNY' "$DISPLAY"
grep -Fq 'xstr' "$DISPLAY"
grep -Fq 'fill 23,125' "$DISPLAY"
test -L "$ROOT/etc/systemd/system/multi-user.target.wants/2pny-display-boot.service"

echo '[7/13] RF stays writable and hands display to MMDVMHost'
RF="$ROOT/usr/local/sbin/2pny-rf-apply"
bash -n "$RF"
grep -Fq 'CONFIG=/var/lib/2pny/mmdvm/MMDVM-Host.ini' "$RF"
grep -Fq 'ScreenLayout=2' "$RF"
grep -Fq 'Speed=9600' "$RF"
grep -Fq '2pny-display-status ready' "$RF"
grep -Fq 'ExecStart=/usr/local/bin/MMDVM-Host /var/lib/2pny/mmdvm/MMDVM-Host.ini' "$ROOT/etc/systemd/system/2pny-mmdvmhost.service"

echo '[8/13] Wizard UX'
WIZ="$ROOT/usr/share/2pny/wizard.html"
grep -Fq '0.2.4-alpha' "$WIZ"
grep -Fq 'autoMaintenance' "$WIZ"
grep -Fq '/api/maintenance' "$WIZ"
grep -Fq 'Validando a senha' "$WIZ"
grep -Fq 'A última tentativa de Wi‑Fi falhou' "$WIZ"
grep -Fq 'Se a senha estiver errada' "$WIZ"
grep -Fq 'http://pu2pny.local/' "$WIZ"
grep -Fq 'Abrir painel principal' "$WIZ"

echo '[9/13] Dashboard preserved'
DASH="$ROOT/usr/share/2pny/dashboard.html"
grep -Fq 'Painel principal' "$DASH"
grep -Fq 'Atividade recente' "$DASH"
grep -Fq '0.2.4-alpha' "$DASH"

echo '[10/13] Clean first boot state'
test ! -e "$ROOT/var/lib/2pny/provisioned"
test ! -e "$ROOT/var/lib/2pny/wifi-scan.json"
test ! -e "$ROOT/var/lib/2pny/network-connect.json"
test ! -e "$ROOT/var/lib/2pny/maintenance.json"
test -e "$ROOT/var/lib/2pny/auto-maintenance.enabled"

echo '[11/13] Run panel inside final ARM64 image'
sudo mkdir -p "$ROOT/proc" "$ROOT/dev" "$ROOT/sys" "$ROOT/run" "$ROOT/var/lib/2pny"
sudo mount -t proc proc "$ROOT/proc"
sudo mount --bind /dev "$ROOT/dev"
sudo mount --bind /sys "$ROOT/sys"
sudo chroot "$ROOT" /usr/local/bin/2pnyd >/tmp/pu2pnyd-024.log 2>&1 & PID=$!
OK=0
for _ in {1..60}; do
  if curl -fsS http://127.0.0.1/healthz 2>/dev/null | grep -q 'PU2PNY OK'; then OK=1; break; fi
  sleep .2
done
test "$OK" = 1 || { cat /tmp/pu2pnyd-024.log; exit 1; }
STATUS="$(curl -fsS http://127.0.0.1/api/status)"
echo "$STATUS" | grep -Fq '"version":"0.2.4-alpha"'
CONN="$(curl -fsS http://127.0.0.1/api/connectivity)"
echo "$CONN" | grep -q '"wifi_ssid"'
MA="$(curl -fsS http://127.0.0.1/api/maintenance)"
echo "$MA" | grep -q '"enabled":true'

echo '[12/13] Captive and route behavior'
LOC="$(curl -sSI http://127.0.0.1/ | awk 'BEGIN{IGNORECASE=1}/^Location:/{gsub("\r","");print $2}')"
test "$LOC" = /wizard
for path in generate_204 canonical.html check_network_status.txt; do
  CODE="$(curl -sS -o /dev/null -w '%{http_code}' "http://127.0.0.1/$path")"
  test "$CODE" = 302
done
sudo touch "$ROOT/var/lib/2pny/provisioned"
LOC="$(curl -sSI http://127.0.0.1/ | awk 'BEGIN{IGNORECASE=1}/^Location:/{gsub("\r","");print $2}')"
test "$LOC" = /dashboard
test "$(curl -fsS http://127.0.0.1/canonical.html)" = 'success'
test "$(curl -fsS http://127.0.0.1/check_network_status.txt)" = 'NetworkManager is online'
sudo rm -f "$ROOT/var/lib/2pny/provisioned"

echo '[13/13] Final result'
echo "PU2PNY $VERSION ARM64 image: OK"
