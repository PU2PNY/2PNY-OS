#!/usr/bin/env bash
set -euo pipefail
IMAGE="${1:?image required}"
VERSION="${2:-0.1.8-alpha}"
RAW="/tmp/2PNY-OS-${VERSION}-validate.img"
ROOT=/mnt/2pny-018
PID=''; LOOP=''
cleanup(){ set +e; test -n "$PID" && sudo kill "$PID" 2>/dev/null || true; sudo umount "$ROOT/proc" "$ROOT/dev" "$ROOT/sys" "$ROOT/boot/firmware" "$ROOT" 2>/dev/null || true; test -n "$LOOP" && sudo losetup -d "$LOOP" 2>/dev/null || true; sudo rm -f "$RAW"; }
trap cleanup EXIT
xz -t "$IMAGE"
EXPECTED=$(awk '{print $1}' "${IMAGE}.sha256"); ACTUAL=$(sha256sum "$IMAGE"|awk '{print $1}'); test "$EXPECTED" = "$ACTUAL"
sudo sh -c "xz -dc '$IMAGE' > '$RAW'"
LOOP=$(sudo losetup --find --partscan --show "$RAW")
for _ in {1..20}; do test -b "${LOOP}p2" && break; sleep .25; done
sudo mkdir -p "$ROOT"; sudo mount "${LOOP}p2" "$ROOT"; sudo mkdir -p "$ROOT/boot/firmware"; sudo mount "${LOOP}p1" "$ROOT/boot/firmware"

echo '[1/9] Bookworm and runtime packages'
grep -q '^VERSION_CODENAME=bookworm$' "$ROOT/etc/os-release"
grep -q "$VERSION" "$ROOT/etc/2pny/version"
for f in /usr/bin/nmcli /usr/sbin/NetworkManager /usr/sbin/hostapd /usr/sbin/dnsmasq /usr/sbin/iw; do test -x "$ROOT$f" || { echo "missing $f"; exit 1; }; done
test -x "$ROOT/usr/sbin/rfkill" || test -x "$ROOT/usr/bin/rfkill"

echo '[2/9] NetworkManager keyfile permissions'
for f in "$ROOT"/etc/NetworkManager/system-connections/*.nmconnection; do test "$(stat -c %a "$f")" = 600 || { echo "bad mode $f $(stat -c %a "$f")"; exit 1; }; done

echo '[3/9] Dedicated first-access engine'
test -x "$ROOT/usr/local/sbin/2pny-network-core"
test -x "$ROOT/usr/local/sbin/2pny-network-switch"
test -L "$ROOT/etc/systemd/system/multi-user.target.wants/2pny-network-core.service"
test "$(readlink "$ROOT/etc/systemd/system/2pny-firstboot.service")" = /dev/null
test "$(readlink "$ROOT/etc/systemd/system/2pny-setup-watch.service")" = /dev/null
test "$(readlink "$ROOT/etc/systemd/system/hostapd.service")" = /dev/null
test "$(readlink "$ROOT/etc/systemd/system/dnsmasq.service")" = /dev/null
bash -n "$ROOT/usr/local/sbin/2pny-network-core"
bash -n "$ROOT/usr/local/sbin/2pny-network-switch"

echo '[4/9] Open AP and explicit DHCP contracts'
grep -q '^ssid=2PNY-SETUP$' "$ROOT/usr/share/2pny/network/hostapd.template"
grep -q '^wpa=0$' "$ROOT/usr/share/2pny/network/hostapd.template"
! grep -q 'wpa_passphrase' "$ROOT/usr/share/2pny/network/hostapd.template"
grep -q 'dhcp-range=10.42.0.20,10.42.0.200' "$ROOT/usr/share/2pny/network/dnsmasq-ap.template"
grep -q 'dhcp-range=10.43.0.20,10.43.0.200' "$ROOT/usr/share/2pny/network/dnsmasq-eth.template"
grep -q 'address=/#/10.42.0.1' "$ROOT/usr/share/2pny/network/dnsmasq-ap.template"
grep -q 'address=/#/10.43.0.1' "$ROOT/usr/share/2pny/network/dnsmasq-eth.template"

echo '[5/9] No stale provisioned state'
test ! -e "$ROOT/var/lib/2pny/provisioned"

echo '[6/9] Chroot network self-test'
sudo mkdir -p "$ROOT/proc" "$ROOT/dev" "$ROOT/sys" "$ROOT/run" "$ROOT/var/lib/2pny"
sudo mount -t proc proc "$ROOT/proc"; sudo mount --bind /dev "$ROOT/dev"; sudo mount --bind /sys "$ROOT/sys"
sudo chroot "$ROOT" /usr/local/sbin/2pny-network-core --self-test

echo '[7/9] Panel runtime'
sudo chroot "$ROOT" /usr/local/bin/2pnyd >/tmp/2pnyd-018.log 2>&1 & PID=$!
OK=0; for _ in {1..40}; do curl -fsS http://127.0.0.1/healthz 2>/dev/null | grep -q '2PNY OK' && { OK=1; break; }; sleep .2; done
test "$OK" = 1 || { cat /tmp/2pnyd-018.log; exit 1; }
curl -fsS http://127.0.0.1/wizard >/dev/null
sudo ss -ltn | grep -E '(0\.0\.0\.0|\*|\[::\]):80\b'

echo '[8/9] RF/Talker Alias preserved'
test -x "$ROOT/usr/local/bin/MMDVM-Host"
grep -q '^DumpTAData=1$' "$ROOT/usr/local/sbin/2pny-rf-apply"
grep -q 'MemoryMax=96M' "$ROOT/etc/systemd/system/2pny-mmdvmhost.service"

echo '[9/9] done'
echo '2PNY 0.1.8 Bookworm hostapd/dnsmasq network core image: OK'
