#!/usr/bin/env bash
set -euo pipefail
IMAGE="${1:?image required}"
VERSION="${2:-0.1.9-alpha}"
RAW="/tmp/PU2PNY-OS-${VERSION}-validate.img"
ROOT=/mnt/pu2pny-019
PID=''; LOOP=''
cleanup(){ set +e; test -n "$PID" && sudo kill "$PID" 2>/dev/null || true; sudo umount "$ROOT/proc" "$ROOT/dev" "$ROOT/sys" "$ROOT/boot/firmware" "$ROOT" 2>/dev/null || true; test -n "$LOOP" && sudo losetup -d "$LOOP" 2>/dev/null || true; sudo rm -f "$RAW"; }
trap cleanup EXIT

xz -t "$IMAGE"
EXPECTED=$(awk '{print $1}' "${IMAGE}.sha256")
ACTUAL=$(sha256sum "$IMAGE" | awk '{print $1}')
test "$EXPECTED" = "$ACTUAL"
sudo sh -c "xz -dc '$IMAGE' > '$RAW'"
LOOP=$(sudo losetup --find --partscan --show "$RAW")
for _ in {1..20}; do test -b "${LOOP}p2" && break; sleep .25; done
sudo mkdir -p "$ROOT"
sudo mount "${LOOP}p2" "$ROOT"
sudo mkdir -p "$ROOT/boot/firmware"
sudo mount "${LOOP}p1" "$ROOT/boot/firmware"

echo '[1/10] Base, version and identity'
grep -q '^VERSION_CODENAME=bookworm$' "$ROOT/etc/os-release"
grep -Fxq "$VERSION" "$ROOT/etc/2pny/version"
grep -Fxq 'pu2pny' "$ROOT/etc/hostname"
grep -Eq '^127\.0\.1\.1[[:space:]]+pu2pny([[:space:]]|$)' "$ROOT/etc/hosts"

echo '[2/10] Runtime and local driver tools'
for f in /usr/bin/nmcli /usr/sbin/NetworkManager /usr/sbin/hostapd /usr/sbin/dnsmasq /usr/sbin/iw /usr/bin/avahi-publish /usr/sbin/modprobe; do
  test -x "$ROOT$f" || { echo "missing $f"; exit 1; }
done
test -x "$ROOT/usr/sbin/rfkill" || test -x "$ROOT/usr/bin/rfkill"
test -x "$ROOT/usr/local/sbin/2pny-hardware-drivers"
test -x "$ROOT/usr/local/sbin/2pny-hardware-probe"
test -x "$ROOT/usr/local/sbin/2pny-mdns-alias"

echo '[3/10] Network core and AP runtime contract'
test -x "$ROOT/usr/local/sbin/2pny-network-core"
test -x "$ROOT/usr/local/sbin/2pny-network-switch"
test -x "$ROOT/usr/local/sbin/2pny-ap-control"
test -L "$ROOT/etc/systemd/system/multi-user.target.wants/2pny-network-core.service"
test "$(readlink "$ROOT/etc/systemd/system/2pny-firstboot.service")" = /dev/null
test "$(readlink "$ROOT/etc/systemd/system/2pny-setup-watch.service")" = /dev/null
test "$(readlink "$ROOT/etc/systemd/system/hostapd.service")" = /dev/null
test "$(readlink "$ROOT/etc/systemd/system/dnsmasq.service")" = /dev/null
bash -n "$ROOT/usr/local/sbin/2pny-network-core"
bash -n "$ROOT/usr/local/sbin/2pny-network-switch"
bash -n "$ROOT/usr/local/sbin/2pny-ap-control"
grep -Fq 'echo "$HOSTAPD_PID" >"$RUN/hostapd.pid"' "$ROOT/usr/local/sbin/2pny-network-core"
grep -Fq 'kill -0 "$(cat /run/2pny/hostapd.pid 2>/dev/null)"' "$ROOT/usr/local/sbin/2pny-ap-control"

echo '[4/10] Open captive first access and aliases'
grep -q '^ssid=2PNY-SETUP$' "$ROOT/usr/share/2pny/network/hostapd.template"
grep -q '^wpa=0$' "$ROOT/usr/share/2pny/network/hostapd.template"
! grep -q 'wpa_passphrase' "$ROOT/usr/share/2pny/network/hostapd.template"
grep -q 'dhcp-range=10.42.0.20,10.42.0.200' "$ROOT/usr/share/2pny/network/dnsmasq-ap.template"
grep -q 'dhcp-range=10.43.0.20,10.43.0.200' "$ROOT/usr/share/2pny/network/dnsmasq-eth.template"
grep -q 'address=/pu2pny.local/10.42.0.1' "$ROOT/usr/share/2pny/network/dnsmasq-ap.template"
grep -q 'address=/2pny.local/10.42.0.1' "$ROOT/usr/share/2pny/network/dnsmasq-ap.template"
grep -q 'address=/pu2pny.local/10.43.0.1' "$ROOT/usr/share/2pny/network/dnsmasq-eth.template"
grep -q 'address=/2pny.local/10.43.0.1' "$ROOT/usr/share/2pny/network/dnsmasq-eth.template"

echo '[5/10] mDNS alias service'
test -f "$ROOT/etc/systemd/system/2pny-mdns-alias.service"
grep -q 'avahi-publish -a -f 2pny.local' "$ROOT/usr/local/sbin/2pny-mdns-alias"
grep -q 'MemoryMax=16M' "$ROOT/etc/systemd/system/2pny-mdns-alias.service"
bash -n "$ROOT/usr/local/sbin/2pny-mdns-alias"

echo '[6/10] Hardware discovery source/runtime'
bash -n "$ROOT/usr/local/sbin/2pny-hardware-drivers"
grep -q 'cdc_acm ch341 cp210x ftdi_sio i2c_dev' "$ROOT/usr/local/sbin/2pny-hardware-drivers"
grep -q 'for baud in (115200, 460800)' "$ROOT/usr/local/sbin/2pny-hardware-probe"
grep -q 'def usb_devices' "$ROOT/usr/local/sbin/2pny-hardware-probe"
grep -q 'def display_outputs' "$ROOT/usr/local/sbin/2pny-hardware-probe"
python3 -m py_compile "$ROOT/usr/local/sbin/2pny-hardware-probe"
sudo rm -rf "$ROOT/usr/local/sbin/__pycache__"

echo '[7/10] No stale provisioned state'
test ! -e "$ROOT/var/lib/2pny/provisioned"

echo '[8/10] Chroot network self-test'
sudo mkdir -p "$ROOT/proc" "$ROOT/dev" "$ROOT/sys" "$ROOT/run" "$ROOT/var/lib/2pny"
sudo mount -t proc proc "$ROOT/proc"
sudo mount --bind /dev "$ROOT/dev"
sudo mount --bind /sys "$ROOT/sys"
sudo chroot "$ROOT" /usr/local/sbin/2pny-network-core --self-test

echo '[9/10] Panel runtime, mobile UI and manual progression'
sudo chroot "$ROOT" /usr/local/bin/2pnyd >/tmp/pu2pnyd-019.log 2>&1 & PID=$!
OK=0
for _ in {1..40}; do curl -fsS http://127.0.0.1/healthz 2>/dev/null | grep -q '2PNY OK' && { OK=1; break; }; sleep .2; done
test "$OK" = 1 || { cat /tmp/pu2pnyd-019.log; exit 1; }
WIZ=$(mktemp)
curl -fsS http://127.0.0.1/wizard >"$WIZ"
grep -q 'PU2PNY OS' "$WIZ"
grep -q 'pu2pny-responsive-019' "$WIZ"
grep -q 'Continuar para RF' "$WIZ"
! grep -q 'id="continue" disabled' "$WIZ"
grep -q 'Ex.: /dev/serial0' "$WIZ"
grep -q '0.1.9-alpha' "$WIZ"
curl -fsS http://127.0.0.1/ | grep -q 'PU2PNY OS'
sudo ss -ltn | grep -E '(0\.0\.0\.0|\*|\[::\]):80\b'
rm -f "$WIZ"

echo '[10/10] RF and Talker Alias preserved'
test -x "$ROOT/usr/local/bin/MMDVM-Host"
grep -q '^DumpTAData=1$' "$ROOT/usr/local/sbin/2pny-rf-apply"
grep -q 'MemoryMax=96M' "$ROOT/etc/systemd/system/2pny-mmdvmhost.service"

echo 'PU2PNY OS 0.1.9 final ARM64 image: OK'
