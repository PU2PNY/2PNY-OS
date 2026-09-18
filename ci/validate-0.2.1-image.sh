#!/usr/bin/env bash
set -euo pipefail

IMAGE="$1"
VERSION="$2"
RAW="/tmp/PU2PNY-OS-$VERSION-validate.img"
ROOT="/mnt/pu2pny-021"
PID=""
LOOP=""

cleanup(){
  set +e
  test -n "$PID" && sudo kill "$PID" 2>/dev/null || true
  sudo umount "$ROOT/proc" "$ROOT/dev" "$ROOT/sys" "$ROOT/boot/firmware" "$ROOT" 2>/dev/null || true
  test -n "$LOOP" && sudo losetup -d "$LOOP" 2>/dev/null || true
  sudo rm -f "$RAW"
}
trap cleanup EXIT

echo '[1/12] Compressed image integrity'
xz -t "$IMAGE"
EXPECTED="$(awk '{print $1}' "$IMAGE.sha256")"
ACTUAL="$(sha256sum "$IMAGE" | awk '{print $1}')"
test -n "$EXPECTED"
test "$EXPECTED" = "$ACTUAL"

sudo sh -c "xz -dc '$IMAGE' > '$RAW'"
LOOP="$(sudo losetup --find --partscan --show "$RAW")"
for _ in {1..30}; do
  test -b "$LOOP"p2 && break
  sleep .25
done
test -b "$LOOP"p1
test -b "$LOOP"p2

sudo mkdir -p "$ROOT"
sudo mount "$LOOP"p2 "$ROOT"
sudo mkdir -p "$ROOT/boot/firmware"
sudo mount "$LOOP"p1 "$ROOT/boot/firmware"

echo '[2/12] Base image, identity and version'
grep -q '^VERSION_CODENAME=bookworm$' "$ROOT/etc/os-release"
grep -Fxq "$VERSION" "$ROOT/etc/2pny/version"
grep -Fxq 'pu2pny' "$ROOT/etc/hostname"
grep -Eq '^127\.0\.1\.1[[:space:]]+pu2pny([[:space:]]|$)' "$ROOT/etc/hosts"

echo '[3/12] Runtime dependencies'
for f in /usr/bin/nmcli /usr/sbin/NetworkManager /usr/sbin/hostapd /usr/sbin/dnsmasq /usr/sbin/iw /usr/bin/avahi-publish /usr/sbin/modprobe /usr/sbin/iptables /usr/bin/python3; do
  test -x "$ROOT$f" || { echo "missing $f" >&2; exit 1; }
done
test -x "$ROOT/usr/sbin/rfkill" || test -x "$ROOT/usr/bin/rfkill"

echo '[4/12] Network core and conflict ownership'
for f in 2pny-network-core 2pny-network-switch 2pny-ap-control 2pny-mdns-alias; do
  test -x "$ROOT/usr/local/sbin/$f"
  bash -n "$ROOT/usr/local/sbin/$f"
done
test -L "$ROOT/etc/systemd/system/multi-user.target.wants/2pny-network-core.service"
test "$(readlink "$ROOT/etc/systemd/system/2pny-firstboot.service")" = /dev/null
test "$(readlink "$ROOT/etc/systemd/system/2pny-setup-watch.service")" = /dev/null
test "$(readlink "$ROOT/etc/systemd/system/hostapd.service")" = /dev/null
test "$(readlink "$ROOT/etc/systemd/system/dnsmasq.service")" = /dev/null
grep -Fq 'uplink-iface' "$ROOT/usr/local/sbin/2pny-network-core"
grep -Fq 'ap-iface' "$ROOT/usr/local/sbin/2pny-network-core"
grep -Fq 'MASQUERADE' "$ROOT/usr/local/sbin/2pny-network-core"
grep -Fq 'nmcli --wait 12 device connect' "$ROOT/usr/local/sbin/2pny-network-core"
grep -Fq '10.43.0.1/24' "$ROOT/usr/local/sbin/2pny-network-core"
grep -Fq '10.43.0.11/24' "$ROOT/usr/local/sbin/2pny-network-core"
grep -Fq 'LAST_CARRIER' "$ROOT/usr/local/sbin/2pny-network-core"
grep -Fq 'PU2PNY-ETH-AUTO' "$ROOT/usr/local/sbin/2pny-network-core"

echo '[5/12] Internet-first AP and safe direct Ethernet'
grep -q '^ssid=pu2pny
grep -q '^wpa=0$' "$ROOT/usr/share/2pny/network/hostapd.template"
! grep -q 'wpa_passphrase' "$ROOT/usr/share/2pny/network/hostapd.template"
grep -q 'dhcp-range=10.42.0.20,10.42.0.200' "$ROOT/usr/share/2pny/network/dnsmasq-ap.template"
grep -q 'address=/pu2pny.local/10.42.0.1' "$ROOT/usr/share/2pny/network/dnsmasq-ap.template"
grep -q 'dhcp-range=10.43.0.20,10.43.0.200' "$ROOT/usr/share/2pny/network/dnsmasq-eth.template"
grep -qx 'port=0' "$ROOT/usr/share/2pny/network/dnsmasq-eth.template"
grep -qx 'dhcp-option=3' "$ROOT/usr/share/2pny/network/dnsmasq-eth.template"
grep -qx 'dhcp-option=6' "$ROOT/usr/share/2pny/network/dnsmasq-eth.template"
grep -qx 'dhcp-option-force=114,http://10.42.0.1/captive-api' "$ROOT/usr/share/2pny/network/dnsmasq-ap.template"
grep -qx 'dhcp-option-force=114,http://10.43.0.1/captive-api' "$ROOT/usr/share/2pny/network/dnsmasq-eth.template"
! grep -Eq '^dhcp-option=3,' "$ROOT/usr/share/2pny/network/dnsmasq-eth.template"
! grep -Eq '^dhcp-option=6,' "$ROOT/usr/share/2pny/network/dnsmasq-eth.template"

echo '[6/12] Hardware preparation and discovery'
for f in 2pny-hardware-drivers 2pny-hardware-prepare 2pny-hardware-probe 2pny-mode-apply; do
  test -x "$ROOT/usr/local/sbin/$f"
done
bash -n "$ROOT/usr/local/sbin/2pny-hardware-drivers"
bash -n "$ROOT/usr/local/sbin/2pny-hardware-prepare"
bash -n "$ROOT/usr/local/sbin/2pny-mode-apply"
grep -Fq 'firmware-realtek' "$ROOT/usr/local/sbin/2pny-hardware-prepare"
grep -Fq 'apt-get install' "$ROOT/usr/local/sbin/2pny-hardware-prepare"
grep -Fq 'cdc_acm ch341 cp210x ftdi_sio i2c_dev' "$ROOT/usr/local/sbin/2pny-hardware-drivers"
grep -q 'for baud in (115200, 460800)' "$ROOT/usr/local/sbin/2pny-hardware-probe"
grep -q 'def usb_devices' "$ROOT/usr/local/sbin/2pny-hardware-probe"
grep -q 'def display_outputs' "$ROOT/usr/local/sbin/2pny-hardware-probe"
python3 -m py_compile "$ROOT/usr/local/sbin/2pny-hardware-probe"
sudo rm -rf "$ROOT/usr/local/sbin/__pycache__"

echo '[7/12] Professional onboarding contract'
WIZARD="$ROOT/usr/share/2pny/wizard.html"
test -s "$WIZARD"
grep -Fq 'Primeiro acesso — Internet' "$WIZARD"
grep -Fq 'Preparando hardware' "$WIZARD"
grep -Fq 'Configuração básica' "$WIZARD"
grep -Fq '>Hotspot<' "$WIZARD"
grep -Fq '>Repetidora<' "$WIZARD"
grep -Fq '>Normal<' "$WIZARD"
grep -Fq '>Crossmode<' "$WIZARD"
grep -Fq 'Manter AP ativo' "$WIZARD"
grep -Fq 'Reverificar cabo e internet' "$WIZARD"
grep -Fq '/api/network/connect' "$WIZARD"
grep -Fq '/api/network/connect/status' "$WIZARD"
grep -Fq 'wifiScan' "$WIZARD"
grep -Fq 'ssidSelect' "$WIZARD"
grep -Fq 'showPass' "$WIZARD"
grep -Fq '10.43.0.11' "$WIZARD"
grep -Fq '/api/basic/apply' "$WIZARD"
! grep -qi 'offset' "$WIZARD"
! grep -qi 'porta mmdvm' "$WIZARD"
! grep -qi '/dev/serial0' "$WIZARD"

echo '[8/12] First-boot state is clean'
test ! -e "$ROOT/var/lib/2pny/provisioned"
test ! -e "$ROOT/var/lib/2pny/rf-apply-state.json"
test ! -e "$ROOT/var/lib/2pny/basic-radio.json"

echo '[9/12] RF engine and rollback preserved'
test -x "$ROOT/usr/local/bin/MMDVM-Host"
test -x "$ROOT/usr/local/sbin/2pny-rf-apply"
grep -q '^DumpTAData=1$' "$ROOT/usr/local/sbin/2pny-rf-apply"
grep -q 'MemoryMax=96M' "$ROOT/etc/systemd/system/2pny-mmdvmhost.service"
grep -Fq 'backups/mode' "$ROOT/usr/local/sbin/2pny-mode-apply"
grep -Fq 'configuration rolled back' "$ROOT/usr/local/sbin/2pny-mode-apply"

echo '[10/12] Start panel inside final ARM64 rootfs'
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

echo '[11/12] Runtime APIs and wizard'
curl -fsSI http://127.0.0.1/ | grep -Eq 'HTTP/[0-9.]+ 302'
curl -fsS http://127.0.0.1/wizard >/tmp/pu2pny-wizard-021.html
grep -Fq 'Primeiro acesso — Internet' /tmp/pu2pny-wizard-021.html
grep -Fq "$VERSION" /tmp/pu2pny-wizard-021.html
STATUS="$(curl -fsS http://127.0.0.1/api/status)"
echo "$STATUS" | grep -Fq "\"version\":\"$VERSION\""
CAPTIVE="$(curl -fsS http://127.0.0.1/captive-api)"
echo "$CAPTIVE" | grep -q '"captive"'
echo "$CAPTIVE" | grep -q '"user-portal-url"'
CONN="$(curl -fsS http://127.0.0.1/api/connectivity)"
echo "$CONN" | grep -q '"internet"'
echo "$CONN" | grep -q '"wifi_count"'
HW="$(curl -fsS http://127.0.0.1/api/hardware/status)"
echo "$HW" | grep -Eq '"state"[[:space:]]*:[[:space:]]*"(not_scanned|preparing|scanning|complete|error)"'

echo '[12/12] Release identity'
grep -Fxq "$VERSION" "$ROOT/etc/2pny/version"
grep -Fq "$VERSION" "$WIZARD"
grep -Fq 'pu2pnu-os' "$WIZARD"

echo "pu2pnu-os $VERSION final ARM64 image: OK"
 "$ROOT/usr/share/2pny/network/hostapd.template"
! grep -q '^ssid=2PNY-SETUP
grep -q '^wpa=0$' "$ROOT/usr/share/2pny/network/hostapd.template"
! grep -q 'wpa_passphrase' "$ROOT/usr/share/2pny/network/hostapd.template"
grep -q 'dhcp-range=10.42.0.20,10.42.0.200' "$ROOT/usr/share/2pny/network/dnsmasq-ap.template"
grep -q 'address=/pu2pny.local/10.42.0.1' "$ROOT/usr/share/2pny/network/dnsmasq-ap.template"
grep -q 'dhcp-range=10.43.0.20,10.43.0.200' "$ROOT/usr/share/2pny/network/dnsmasq-eth.template"
grep -qx 'port=0' "$ROOT/usr/share/2pny/network/dnsmasq-eth.template"
grep -qx 'dhcp-option=3' "$ROOT/usr/share/2pny/network/dnsmasq-eth.template"
grep -qx 'dhcp-option=6' "$ROOT/usr/share/2pny/network/dnsmasq-eth.template"
! grep -Eq '^dhcp-option=3,' "$ROOT/usr/share/2pny/network/dnsmasq-eth.template"
! grep -Eq '^dhcp-option=6,' "$ROOT/usr/share/2pny/network/dnsmasq-eth.template"

echo '[6/12] Hardware preparation and discovery'
for f in 2pny-hardware-drivers 2pny-hardware-prepare 2pny-hardware-probe 2pny-mode-apply; do
  test -x "$ROOT/usr/local/sbin/$f"
done
bash -n "$ROOT/usr/local/sbin/2pny-hardware-drivers"
bash -n "$ROOT/usr/local/sbin/2pny-hardware-prepare"
bash -n "$ROOT/usr/local/sbin/2pny-mode-apply"
grep -Fq 'firmware-realtek' "$ROOT/usr/local/sbin/2pny-hardware-prepare"
grep -Fq 'apt-get install' "$ROOT/usr/local/sbin/2pny-hardware-prepare"
grep -Fq 'cdc_acm ch341 cp210x ftdi_sio i2c_dev' "$ROOT/usr/local/sbin/2pny-hardware-drivers"
grep -q 'for baud in (115200, 460800)' "$ROOT/usr/local/sbin/2pny-hardware-probe"
grep -q 'def usb_devices' "$ROOT/usr/local/sbin/2pny-hardware-probe"
grep -q 'def display_outputs' "$ROOT/usr/local/sbin/2pny-hardware-probe"
python3 -m py_compile "$ROOT/usr/local/sbin/2pny-hardware-probe"
sudo rm -rf "$ROOT/usr/local/sbin/__pycache__"

echo '[7/12] Professional onboarding contract'
WIZARD="$ROOT/usr/share/2pny/wizard.html"
test -s "$WIZARD"
grep -Fq 'Primeiro acesso — Internet' "$WIZARD"
grep -Fq 'Preparando hardware' "$WIZARD"
grep -Fq 'Configuração básica' "$WIZARD"
grep -Fq '>Hotspot<' "$WIZARD"
grep -Fq '>Repetidora<' "$WIZARD"
grep -Fq '>Normal<' "$WIZARD"
grep -Fq '>Crossmode<' "$WIZARD"
grep -Fq 'Manter AP ativo' "$WIZARD"
grep -Fq 'Reverificar cabo e internet' "$WIZARD"
grep -Fq '/api/network/connect' "$WIZARD"
grep -Fq '/api/basic/apply' "$WIZARD"
! grep -qi 'offset' "$WIZARD"
! grep -qi 'porta mmdvm' "$WIZARD"
! grep -qi '/dev/serial0' "$WIZARD"

echo '[8/12] First-boot state is clean'
test ! -e "$ROOT/var/lib/2pny/provisioned"
test ! -e "$ROOT/var/lib/2pny/rf-apply-state.json"
test ! -e "$ROOT/var/lib/2pny/basic-radio.json"

echo '[9/12] RF engine and rollback preserved'
test -x "$ROOT/usr/local/bin/MMDVM-Host"
test -x "$ROOT/usr/local/sbin/2pny-rf-apply"
grep -q '^DumpTAData=1$' "$ROOT/usr/local/sbin/2pny-rf-apply"
grep -q 'MemoryMax=96M' "$ROOT/etc/systemd/system/2pny-mmdvmhost.service"
grep -Fq 'backups/mode' "$ROOT/usr/local/sbin/2pny-mode-apply"
grep -Fq 'configuration rolled back' "$ROOT/usr/local/sbin/2pny-mode-apply"

echo '[10/12] Start panel inside final ARM64 rootfs'
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

echo '[11/12] Runtime APIs and wizard'
curl -fsSI http://127.0.0.1/ | grep -Eq 'HTTP/[0-9.]+ 302'
curl -fsS http://127.0.0.1/wizard >/tmp/pu2pny-wizard-021.html
grep -Fq 'Primeiro acesso — Internet' /tmp/pu2pny-wizard-021.html
grep -Fq "$VERSION" /tmp/pu2pny-wizard-021.html
STATUS="$(curl -fsS http://127.0.0.1/api/status)"
echo "$STATUS" | grep -Fq "\"version\":\"$VERSION\""
CONN="$(curl -fsS http://127.0.0.1/api/connectivity)"
echo "$CONN" | grep -q '"internet"'
echo "$CONN" | grep -q '"wifi_count"'
HW="$(curl -fsS http://127.0.0.1/api/hardware/status)"
echo "$HW" | grep -Eq '"state"[[:space:]]*:[[:space:]]*"(not_scanned|preparing|scanning|complete|error)"'

echo '[12/12] Release identity'
grep -Fxq "$VERSION" "$ROOT/etc/2pny/version"
grep -Fq "$VERSION" "$WIZARD"

echo "pu2pnu-os $VERSION final ARM64 image: OK"
 "$ROOT/usr/share/2pny/network/hostapd.template"
grep -q '^wpa=0$' "$ROOT/usr/share/2pny/network/hostapd.template"
! grep -q 'wpa_passphrase' "$ROOT/usr/share/2pny/network/hostapd.template"
grep -q 'dhcp-range=10.42.0.20,10.42.0.200' "$ROOT/usr/share/2pny/network/dnsmasq-ap.template"
grep -q 'address=/pu2pny.local/10.42.0.1' "$ROOT/usr/share/2pny/network/dnsmasq-ap.template"
grep -q 'dhcp-range=10.43.0.20,10.43.0.200' "$ROOT/usr/share/2pny/network/dnsmasq-eth.template"
grep -qx 'port=0' "$ROOT/usr/share/2pny/network/dnsmasq-eth.template"
grep -qx 'dhcp-option=3' "$ROOT/usr/share/2pny/network/dnsmasq-eth.template"
grep -qx 'dhcp-option=6' "$ROOT/usr/share/2pny/network/dnsmasq-eth.template"
! grep -Eq '^dhcp-option=3,' "$ROOT/usr/share/2pny/network/dnsmasq-eth.template"
! grep -Eq '^dhcp-option=6,' "$ROOT/usr/share/2pny/network/dnsmasq-eth.template"

echo '[6/12] Hardware preparation and discovery'
for f in 2pny-hardware-drivers 2pny-hardware-prepare 2pny-hardware-probe 2pny-mode-apply; do
  test -x "$ROOT/usr/local/sbin/$f"
done
bash -n "$ROOT/usr/local/sbin/2pny-hardware-drivers"
bash -n "$ROOT/usr/local/sbin/2pny-hardware-prepare"
bash -n "$ROOT/usr/local/sbin/2pny-mode-apply"
grep -Fq 'firmware-realtek' "$ROOT/usr/local/sbin/2pny-hardware-prepare"
grep -Fq 'apt-get install' "$ROOT/usr/local/sbin/2pny-hardware-prepare"
grep -Fq 'cdc_acm ch341 cp210x ftdi_sio i2c_dev' "$ROOT/usr/local/sbin/2pny-hardware-drivers"
grep -q 'for baud in (115200, 460800)' "$ROOT/usr/local/sbin/2pny-hardware-probe"
grep -q 'def usb_devices' "$ROOT/usr/local/sbin/2pny-hardware-probe"
grep -q 'def display_outputs' "$ROOT/usr/local/sbin/2pny-hardware-probe"
python3 -m py_compile "$ROOT/usr/local/sbin/2pny-hardware-probe"
sudo rm -rf "$ROOT/usr/local/sbin/__pycache__"

echo '[7/12] Professional onboarding contract'
WIZARD="$ROOT/usr/share/2pny/wizard.html"
test -s "$WIZARD"
grep -Fq 'Primeiro acesso — Internet' "$WIZARD"
grep -Fq 'Preparando hardware' "$WIZARD"
grep -Fq 'Configuração básica' "$WIZARD"
grep -Fq '>Hotspot<' "$WIZARD"
grep -Fq '>Repetidora<' "$WIZARD"
grep -Fq '>Normal<' "$WIZARD"
grep -Fq '>Crossmode<' "$WIZARD"
grep -Fq 'Manter AP ativo' "$WIZARD"
grep -Fq 'Reverificar cabo e internet' "$WIZARD"
grep -Fq '/api/network/connect' "$WIZARD"
grep -Fq '/api/basic/apply' "$WIZARD"
! grep -qi 'offset' "$WIZARD"
! grep -qi 'porta mmdvm' "$WIZARD"
! grep -qi '/dev/serial0' "$WIZARD"

echo '[8/12] First-boot state is clean'
test ! -e "$ROOT/var/lib/2pny/provisioned"
test ! -e "$ROOT/var/lib/2pny/rf-apply-state.json"
test ! -e "$ROOT/var/lib/2pny/basic-radio.json"

echo '[9/12] RF engine and rollback preserved'
test -x "$ROOT/usr/local/bin/MMDVM-Host"
test -x "$ROOT/usr/local/sbin/2pny-rf-apply"
grep -q '^DumpTAData=1$' "$ROOT/usr/local/sbin/2pny-rf-apply"
grep -q 'MemoryMax=96M' "$ROOT/etc/systemd/system/2pny-mmdvmhost.service"
grep -Fq 'backups/mode' "$ROOT/usr/local/sbin/2pny-mode-apply"
grep -Fq 'configuration rolled back' "$ROOT/usr/local/sbin/2pny-mode-apply"

echo '[10/12] Start panel inside final ARM64 rootfs'
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

echo '[11/12] Runtime APIs and wizard'
curl -fsSI http://127.0.0.1/ | grep -Eq 'HTTP/[0-9.]+ 302'
curl -fsS http://127.0.0.1/wizard >/tmp/pu2pny-wizard-021.html
grep -Fq 'Primeiro acesso — Internet' /tmp/pu2pny-wizard-021.html
grep -Fq "$VERSION" /tmp/pu2pny-wizard-021.html
STATUS="$(curl -fsS http://127.0.0.1/api/status)"
echo "$STATUS" | grep -Fq "\"version\":\"$VERSION\""
CONN="$(curl -fsS http://127.0.0.1/api/connectivity)"
echo "$CONN" | grep -q '"internet"'
echo "$CONN" | grep -q '"wifi_count"'
HW="$(curl -fsS http://127.0.0.1/api/hardware/status)"
echo "$HW" | grep -Eq '"state"[[:space:]]*:[[:space:]]*"(not_scanned|preparing|scanning|complete|error)"'

echo '[12/12] Release identity'
grep -Fxq "$VERSION" "$ROOT/etc/2pny/version"
grep -Fq "$VERSION" "$WIZARD"

echo "pu2pnu-os $VERSION final ARM64 image: OK"
