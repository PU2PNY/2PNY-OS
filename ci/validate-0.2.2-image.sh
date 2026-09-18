#!/usr/bin/env bash
set -euo pipefail

IMAGE="${1:?image required}"
VERSION="${2:-0.2.2-alpha}"
RAW="/tmp/PU2PNY-${VERSION}-validate.img"
ROOT="/mnt/pu2pny-022"
PID=""
LOOP=""

cleanup(){
  set +e
  test -n "$PID" && sudo kill "$PID" 2>/dev/null || true
  sudo umount "$ROOT/proc" "$ROOT/dev" "$ROOT/sys" "$ROOT/boot/firmware" "$ROOT" 2>/dev/null || true
  test -n "$LOOP" && sudo losetup -d "$LOOP" 2>/dev/null || true
  sudo rm -f "$RAW" /tmp/pu2pnyd-022.log /tmp/pu2pny-wizard-022.html
}
trap cleanup EXIT

echo '[1/11] Image integrity'
xz -t "$IMAGE"
EXPECTED="$(awk '{print $1}' "$IMAGE.sha256")"
ACTUAL="$(sha256sum "$IMAGE" | awk '{print $1}')"
test -n "$EXPECTED"
test "$EXPECTED" = "$ACTUAL"

sudo sh -c "xz -dc '$IMAGE' > '$RAW'"
LOOP="$(sudo losetup --find --partscan --show "$RAW")"
for _ in {1..30}; do
  test -b "${LOOP}p2" && break
  sleep .25
done
test -b "${LOOP}p1"
test -b "${LOOP}p2"
sudo mkdir -p "$ROOT"
sudo mount "${LOOP}p2" "$ROOT"
sudo mkdir -p "$ROOT/boot/firmware"
sudo mount "${LOOP}p1" "$ROOT/boot/firmware"

echo '[2/11] OS identity'
grep -q '^VERSION_CODENAME=bookworm$' "$ROOT/etc/os-release"
grep -Fxq "$VERSION" "$ROOT/etc/2pny/version"
grep -Fxq 'pu2pny' "$ROOT/etc/hostname"
grep -Eq '^127\.0\.1\.1[[:space:]]+pu2pny([[:space:]]|$)' "$ROOT/etc/hosts"

echo '[3/11] Runtime dependencies'
for x in /usr/bin/nmcli /usr/sbin/NetworkManager /usr/sbin/hostapd /usr/sbin/dnsmasq /usr/sbin/iw /usr/bin/avahi-publish /usr/sbin/modprobe /usr/sbin/iptables /usr/bin/python3; do
  test -x "$ROOT$x" || { echo "missing $x" >&2; exit 1; }
done
test -x "$ROOT/usr/sbin/rfkill" || test -x "$ROOT/usr/bin/rfkill"

echo '[4/11] One-address setup networking'
for x in 2pny-network-core 2pny-network-switch 2pny-ap-control 2pny-mdns-alias; do
  test -x "$ROOT/usr/local/sbin/$x"
  bash -n "$ROOT/usr/local/sbin/$x"
done
grep -Fq 'SETUP_IP=10.43.0.1' "$ROOT/usr/local/sbin/2pny-network-core"
grep -Fq 'SETUP_CIDR=10.43.0.1/24' "$ROOT/usr/local/sbin/2pny-network-core"
grep -Fq 'nmcli --wait 14 connection up PU2PNY-WIFI' "$ROOT/usr/local/sbin/2pny-network-core"
grep -Fq 'LAST_CARRIER' "$ROOT/usr/local/sbin/2pny-network-core"
grep -Fq 'ETH_MODE="direct"' "$ROOT/usr/local/sbin/2pny-network-core"
grep -Fq 'scan-json' "$ROOT/usr/local/sbin/2pny-network-switch"
grep -q '^ssid=pu2pny$' "$ROOT/usr/share/2pny/network/hostapd.template"
grep -q '^listen-address=10.43.0.1$' "$ROOT/usr/share/2pny/network/dnsmasq-ap.template"
grep -q 'dhcp-range=10.43.0.20,10.43.0.200' "$ROOT/usr/share/2pny/network/dnsmasq-ap.template"
grep -qx 'dhcp-option-force=114,http://10.43.0.1/captive-api' "$ROOT/usr/share/2pny/network/dnsmasq-ap.template"
grep -q 'address=/connectivitycheck.gstatic.com/10.43.0.1' "$ROOT/usr/share/2pny/network/dnsmasq-ap.template"
grep -q 'dhcp-range=10.43.0.20,10.43.0.200' "$ROOT/usr/share/2pny/network/dnsmasq-eth.template"
grep -qx 'dhcp-option=3' "$ROOT/usr/share/2pny/network/dnsmasq-eth.template"
grep -qx 'dhcp-option=6' "$ROOT/usr/share/2pny/network/dnsmasq-eth.template"
grep -qx 'dhcp-option-force=114,http://10.43.0.1/captive-api' "$ROOT/usr/share/2pny/network/dnsmasq-eth.template"
! grep -Rqs '10\.42\.0\.1' "$ROOT/usr/share/2pny/network" "$ROOT/usr/local/sbin/2pny-network-core" "$ROOT/usr/local/sbin/2pny-network-switch"
! grep -Rqs '10\.43\.0\.11' "$ROOT/usr/share/2pny/network" "$ROOT/usr/local/sbin/2pny-network-core"

echo '[5/11] Display and Nextion discovery'
PROBE="$ROOT/usr/local/sbin/2pny-hardware-probe"
test -x "$PROBE"
python3 -m py_compile "$PROBE"
sudo rm -rf "$ROOT/usr/local/sbin/__pycache__"
grep -Fq 'for baud in (9600, 19200, 38400, 57600, 115200, 230400, 921600)' "$PROBE"
grep -Fq '"class": "nextion_mmdvm"' "$PROBE"
grep -Fq '"state": "mmdvm_display_port"' "$PROBE"
grep -Fq 'def spi_devices' "$PROBE"
grep -Fq 'def usb_display' "$PROBE"
grep -Fq 'display_outputs()' "$PROBE"
grep -Fq 'probe_configured_display' "$PROBE"

echo '[6/11] RF writable configuration and rollback'
RF="$ROOT/usr/local/sbin/2pny-rf-apply"
MODE="$ROOT/usr/local/sbin/2pny-mode-apply"
SVC="$ROOT/etc/systemd/system/2pny-mmdvmhost.service"
bash -n "$RF"
bash -n "$MODE"
grep -Fq 'CONFIG=/var/lib/2pny/mmdvm/MMDVM-Host.ini' "$RF"
grep -Fq 'CONFIG=/var/lib/2pny/mmdvm/MMDVM-Host.ini' "$MODE"
grep -Fq 'mktemp /run/2pny/.MMDVM-Host.ini.XXXXXX' "$RF"
grep -Fq 'Display=Nextion' "$RF"
grep -Fq 'NEXTION_SECTION="[Nextion]' "$RF"
grep -Fq 'install -m 0640' "$RF"
grep -Fq 'ExecStart=/usr/local/bin/MMDVM-Host /var/lib/2pny/mmdvm/MMDVM-Host.ini' "$SVC"
! grep -Fq '/etc/2pny/mmdvm/MMDVM-Host.ini' "$RF"
! grep -Fq '/etc/2pny/mmdvm/MMDVM-Host.ini' "$MODE"
! grep -Fq '/etc/2pny/mmdvm/MMDVM-Host.ini' "$SVC"
grep -q '^DumpTAData=1$' "$RF"
grep -q 'MemoryMax=96M' "$SVC"
grep -Fq 'ReadWritePaths=/var/lib/2pny /run' "$ROOT/etc/systemd/system/2pnyd.service"
sudo chroot "$ROOT" /bin/bash -c 'mkdir -p /var/lib/2pny/mmdvm /run/2pny; t=$(mktemp /run/2pny/.MMDVM-Host.ini.XXXXXX); echo test >"$t"; install -m 0640 "$t" /var/lib/2pny/mmdvm/MMDVM-Host.ini.test; rm -f "$t" /var/lib/2pny/mmdvm/MMDVM-Host.ini.test'

echo '[7/11] Professional onboarding UI'
WIZARD="$ROOT/usr/share/2pny/wizard.html"
grep -Fq 'PU2PNY' "$WIZARD"
grep -Fq '0.2.2-alpha' "$WIZARD"
grep -Fq 'http://10.43.0.1/' "$WIZARD"
grep -Fq 'http://pu2pny.local/' "$WIZARD"
grep -Fq 'ssidSelect' "$WIZARD"
grep -Fq 'wifiScan' "$WIZARD"
grep -Fq 'showPass' "$WIZARD"
grep -Fq '/api/network/connect/status' "$WIZARD"
grep -Fq 'Wi‑Fi conectado com sucesso' "$WIZARD"
! grep -Fqi 'pu2pnu-os' "$WIZARD"
! grep -Fq '10.42.0.1' "$WIZARD"
! grep -Fq '10.43.0.11' "$WIZARD"
! grep -Fqi 'RX Offset' "$WIZARD"
! grep -Fqi 'TX Offset' "$WIZARD"
! grep -Fqi 'Porta MMDVM detectada' "$WIZARD"

echo '[8/11] Clean first boot'
test ! -e "$ROOT/var/lib/2pny/provisioned"
test ! -e "$ROOT/var/lib/2pny/rf-configured"
test ! -e "$ROOT/var/lib/2pny/rf-apply-state.json"
test ! -e "$ROOT/var/lib/2pny/network-connect.json"

echo '[9/11] Run final panel in ARM64 image'
sudo mkdir -p "$ROOT/proc" "$ROOT/dev" "$ROOT/sys" "$ROOT/run" "$ROOT/var/lib/2pny"
sudo mount -t proc proc "$ROOT/proc"
sudo mount --bind /dev "$ROOT/dev"
sudo mount --bind /sys "$ROOT/sys"
sudo chroot "$ROOT" /usr/local/bin/2pnyd >/tmp/pu2pnyd-022.log 2>&1 & PID=$!
OK=0
for _ in {1..50}; do
  if curl -fsS http://127.0.0.1/healthz 2>/dev/null | grep -q 'PU2PNY OK'; then OK=1; break; fi
  sleep .2
done
test "$OK" = 1 || { cat /tmp/pu2pnyd-022.log; exit 1; }
sudo ss -ltn | grep -E '(0\.0\.0\.0|\*|\[::\]):80\b'
curl -fsS http://127.0.0.1/wizard >/tmp/pu2pny-wizard-022.html
grep -Fq 'PU2PNY' /tmp/pu2pny-wizard-022.html
grep -Fq '0.2.2-alpha' /tmp/pu2pny-wizard-022.html
STATUS="$(curl -fsS http://127.0.0.1/api/status)"
echo "$STATUS" | grep -Fq '"version":"0.2.2-alpha"'
echo "$STATUS" | grep -Fq '"name":"PU2PNY"'
CONNECT="$(curl -fsS http://127.0.0.1/api/network/connect/status)"
echo "$CONNECT" | grep -q '"state"'
echo "$CONNECT" | grep -Fq '"resume_url":"http://pu2pny.local/wizard"'
CAPTIVE="$(curl -fsS http://127.0.0.1/captive-api)"
echo "$CAPTIVE" | grep -q '"captive":true'
CODE="$(curl -sS -o /dev/null -w '%{http_code}' http://127.0.0.1/generate_204)"
test "$CODE" = 302

echo '[10/11] Captive portal releases after setup'
sudo touch "$ROOT/var/lib/2pny/provisioned"
CODE="$(curl -sS -o /dev/null -w '%{http_code}' http://127.0.0.1/generate_204)"
test "$CODE" = 204
test "$(curl -fsS http://127.0.0.1/connecttest.txt)" = 'Microsoft Connect Test'
CAPTIVE="$(curl -fsS http://127.0.0.1/captive-api)"
echo "$CAPTIVE" | grep -q '"captive":false'
sudo rm -f "$ROOT/var/lib/2pny/provisioned"

echo '[11/11] Final result'
echo "PU2PNY $VERSION ARM64 image: OK"
