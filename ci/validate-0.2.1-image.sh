#!/usr/bin/env bash
set -euo pipefail

IMAGE="${1:?image required}"
VERSION="${2:-0.2.1-alpha}"
RAW="/tmp/pu2pnu-os-${VERSION}-validate.img"
ROOT="/mnt/pu2pny-021"
PID=""
LOOP=""

cleanup(){
  set +e
  test -n "$PID" && sudo kill "$PID" 2>/dev/null || true
  sudo umount "$ROOT/proc" "$ROOT/dev" "$ROOT/sys" "$ROOT/boot/firmware" "$ROOT" 2>/dev/null || true
  test -n "$LOOP" && sudo losetup -d "$LOOP" 2>/dev/null || true
  sudo rm -f "$RAW" /tmp/pu2pnyd-021.log /tmp/pu2pny-wizard-021.html
}
trap cleanup EXIT

echo '[1/10] Integrity and partitions'
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

echo '[2/10] OS identity'
grep -q '^VERSION_CODENAME=bookworm$' "$ROOT/etc/os-release"
grep -Fxq "$VERSION" "$ROOT/etc/2pny/version"
grep -Fxq 'pu2pny' "$ROOT/etc/hostname"
grep -Eq '^127\.0\.1\.1[[:space:]]+pu2pny([[:space:]]|$)' "$ROOT/etc/hosts"

echo '[3/10] Required runtime'
for x in /usr/bin/nmcli /usr/sbin/NetworkManager /usr/sbin/hostapd /usr/sbin/dnsmasq /usr/sbin/iw /usr/bin/avahi-publish /usr/sbin/modprobe /usr/sbin/iptables /usr/bin/python3; do
  test -x "$ROOT$x" || { echo "missing $x" >&2; exit 1; }
done
test -x "$ROOT/usr/sbin/rfkill" || test -x "$ROOT/usr/bin/rfkill"

echo '[4/10] Network core, hotplug and captive access'
for x in 2pny-network-core 2pny-network-switch 2pny-ap-control 2pny-mdns-alias; do
  test -x "$ROOT/usr/local/sbin/$x"
  bash -n "$ROOT/usr/local/sbin/$x"
done
test -L "$ROOT/etc/systemd/system/multi-user.target.wants/2pny-network-core.service"
test "$(readlink "$ROOT/etc/systemd/system/2pny-firstboot.service")" = /dev/null
test "$(readlink "$ROOT/etc/systemd/system/2pny-setup-watch.service")" = /dev/null
test "$(readlink "$ROOT/etc/systemd/system/hostapd.service")" = /dev/null
test "$(readlink "$ROOT/etc/systemd/system/dnsmasq.service")" = /dev/null
grep -Fq 'LAST_CARRIER' "$ROOT/usr/local/sbin/2pny-network-core"
grep -Fq 'PU2PNY-ETH-AUTO' "$ROOT/usr/local/sbin/2pny-network-core"
grep -Fq 'nmcli --wait 10 connection up' "$ROOT/usr/local/sbin/2pny-network-core"
grep -Fq '10.43.0.1/24' "$ROOT/usr/local/sbin/2pny-network-core"
grep -Fq '10.43.0.11/24' "$ROOT/usr/local/sbin/2pny-network-core"
grep -Fq 'MASQUERADE' "$ROOT/usr/local/sbin/2pny-network-core"
grep -Fq 'scan-json' "$ROOT/usr/local/sbin/2pny-network-switch"
grep -Fq 'pny-scan0' "$ROOT/usr/local/sbin/2pny-network-switch"
grep -q '^ssid=pu2pny$' "$ROOT/usr/share/2pny/network/hostapd.template"
grep -q '^wpa=0$' "$ROOT/usr/share/2pny/network/hostapd.template"
! grep -q '^ssid=2PNY-SETUP$' "$ROOT/usr/share/2pny/network/hostapd.template"
grep -q 'dhcp-range=10.42.0.20,10.42.0.200' "$ROOT/usr/share/2pny/network/dnsmasq-ap.template"
grep -q 'dhcp-range=10.43.0.20,10.43.0.200' "$ROOT/usr/share/2pny/network/dnsmasq-eth.template"
grep -qx 'dhcp-option=3' "$ROOT/usr/share/2pny/network/dnsmasq-eth.template"
grep -qx 'dhcp-option=6' "$ROOT/usr/share/2pny/network/dnsmasq-eth.template"
grep -qx 'dhcp-option-force=114,http://10.42.0.1/captive-api' "$ROOT/usr/share/2pny/network/dnsmasq-ap.template"
grep -qx 'dhcp-option-force=114,http://10.43.0.1/captive-api' "$ROOT/usr/share/2pny/network/dnsmasq-eth.template"

echo '[5/10] Wi-Fi onboarding UI'
WIZARD="$ROOT/usr/share/2pny/wizard.html"
grep -Fq 'pu2pnu-os' "$WIZARD"
grep -Fq '0.2.1-alpha' "$WIZARD"
grep -Fq 'ssidSelect' "$WIZARD"
grep -Fq 'wifiScan' "$WIZARD"
grep -Fq 'Buscar redes' "$WIZARD"
grep -Fq 'showPass' "$WIZARD"
grep -Fq 'Mostrar' "$WIZARD"
grep -Fq '/api/network/connect/status' "$WIZARD"
grep -Fq '10.43.0.11' "$WIZARD"
! grep -qi 'RX Offset' "$WIZARD"
! grep -qi 'TX Offset' "$WIZARD"
! grep -qi 'Porta MMDVM detectada' "$WIZARD"

echo '[6/10] Backend source/runtime contract'
BIN="$ROOT/usr/local/bin/2pnyd"
test -x "$BIN"
grep -Fq 'pu2pny' "$ROOT/usr/share/2pny/network/hostapd.template"
test -x "$ROOT/usr/local/sbin/2pny-hardware-prepare"
test -x "$ROOT/usr/local/sbin/2pny-hardware-probe"
test -x "$ROOT/usr/local/sbin/2pny-mode-apply"
python3 -m py_compile "$ROOT/usr/local/sbin/2pny-hardware-probe"
sudo rm -rf "$ROOT/usr/local/sbin/__pycache__"

echo '[7/10] RF engine preserved'
test -x "$ROOT/usr/local/bin/MMDVM-Host"
test -x "$ROOT/usr/local/sbin/2pny-rf-apply"
grep -q '^DumpTAData=1$' "$ROOT/usr/local/sbin/2pny-rf-apply"
grep -q 'MemoryMax=96M' "$ROOT/etc/systemd/system/2pny-mmdvmhost.service"

echo '[8/10] Clean first-boot state'
test ! -e "$ROOT/var/lib/2pny/provisioned"
test ! -e "$ROOT/var/lib/2pny/rf-apply-state.json"
test ! -e "$ROOT/var/lib/2pny/network-connect.json"

echo '[9/10] Run final panel inside image'
sudo mkdir -p "$ROOT/proc" "$ROOT/dev" "$ROOT/sys" "$ROOT/run" "$ROOT/var/lib/2pny"
sudo mount -t proc proc "$ROOT/proc"
sudo mount --bind /dev "$ROOT/dev"
sudo mount --bind /sys "$ROOT/sys"
sudo chroot "$ROOT" /usr/local/bin/2pnyd >/tmp/pu2pnyd-021.log 2>&1 & PID=$!
OK=0
for _ in {1..50}; do
  if curl -fsS http://127.0.0.1/healthz 2>/dev/null | grep -q 'PU2PNY OK'; then
    OK=1
    break
  fi
  sleep .2
done
test "$OK" = 1 || { cat /tmp/pu2pnyd-021.log; exit 1; }
sudo ss -ltn | grep -E '(0\.0\.0\.0|\*|\[::\]):80\b'
curl -fsS http://127.0.0.1/wizard >/tmp/pu2pny-wizard-021.html
grep -Fq 'pu2pnu-os' /tmp/pu2pny-wizard-021.html
grep -Fq '0.2.1-alpha' /tmp/pu2pny-wizard-021.html
STATUS="$(curl -fsS http://127.0.0.1/api/status)"
echo "$STATUS" | grep -Fq '"version":"0.2.1-alpha"'
echo "$STATUS" | grep -Fq '"name":"pu2pnu-os"'
CONNECT="$(curl -fsS http://127.0.0.1/api/network/connect/status)"
echo "$CONNECT" | grep -q '"state"'
CAPTIVE="$(curl -fsS http://127.0.0.1/captive-api)"
echo "$CAPTIVE" | grep -q '"captive"'
echo "$CAPTIVE" | grep -q '"user-portal-url"'

echo '[10/10] Final result'
echo "pu2pnu-os $VERSION ARM64 image: OK"
