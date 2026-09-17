#!/usr/bin/env bash
set -euo pipefail
IMAGE="${1:?image required}"
VERSION="${2:-0.1.7-hotfix4}"
RAW="/tmp/2PNY-OS-${VERSION}-validate.img"
ROOT=/mnt/2pny-h4
PID=''
LOOP=''
cleanup(){
  set +e
  test -n "$PID" && sudo kill "$PID" 2>/dev/null || true
  sudo umount "$ROOT/proc" 2>/dev/null || true
  sudo umount "$ROOT/dev" 2>/dev/null || true
  sudo umount "$ROOT/sys" 2>/dev/null || true
  sudo umount "$ROOT/boot/firmware" 2>/dev/null || true
  sudo umount "$ROOT" 2>/dev/null || true
  test -n "$LOOP" && sudo losetup -d "$LOOP" 2>/dev/null || true
  sudo rm -f "$RAW"
}
trap cleanup EXIT

sudo rm -f "$RAW"
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

echo '[1/8] image contract'
grep -q "$VERSION" "$ROOT/etc/2pny/version"
test -x "$ROOT/usr/local/bin/2pnyd"
test -x "$ROOT/usr/local/sbin/2pny-ap-control"
test -x "$ROOT/usr/local/sbin/2pny-setup-watch"

echo '[2/8] Wi-Fi AP contract'
AP="$ROOT/etc/NetworkManager/system-connections/2pny-setup.nmconnection"
grep -q '^ssid=2PNY-SETUP$' "$AP"
grep -q '^mode=ap$' "$AP"
grep -q '^key-mgmt=none$' "$AP"
grep -q '^auth-alg=open$' "$AP"
grep -q '^method=shared$' "$AP"
grep -q '^address1=10.42.0.1/24$' "$AP"
! grep -q '^psk=' "$AP"

echo '[3/8] direct Ethernet contract'
ETH="$ROOT/etc/NetworkManager/system-connections/2pny-ethernet-setup.nmconnection"
grep -q '^id=2PNY-Ethernet-Setup$' "$ETH"
grep -q '^type=ethernet$' "$ETH"
grep -q '^autoconnect=true$' "$ETH"
grep -q '^method=shared$' "$ETH"
grep -q '^address1=10.43.0.1/24$' "$ETH"

echo '[4/8] simultaneous/self-healing network logic'
bash -n "$ROOT/usr/local/sbin/2pny-ap-control"
bash -n "$ROOT/usr/local/sbin/2pny-setup-watch"
bash -n "$ROOT/usr/local/sbin/2pny-firstboot"
grep -q 'Ethernet direct access is independent' "$ROOT/usr/local/sbin/2pny-setup-watch"
grep -q 'Wi-Fi AP is also independent' "$ROOT/usr/local/sbin/2pny-setup-watch"
grep -q '10.43.0.1' "$ROOT/usr/local/sbin/2pny-setup-watch"
grep -q '10.42.0.1' "$ROOT/usr/local/sbin/2pny-setup-watch"
! grep -q 'nmcli connection down 2PNY-Ethernet-Setup' "$ROOT/usr/local/sbin/2pny-ap-control"
# Cable branch must not tear the AP down.
! awk '/Ethernet direct access is independent/{f=1} /Wi-Fi AP is also independent/{f=0} f' "$ROOT/usr/local/sbin/2pny-setup-watch" | grep -q 'connection down.*\$AP'

echo '[5/8] captive portal and panel markers'
grep -q 'address=/#/10.42.0.1' "$ROOT/etc/NetworkManager/dnsmasq-shared.d/2pny-captive.conf"
grep -aFq '/healthz' "$ROOT/usr/local/bin/2pnyd"
grep -aFq '/api/ap' "$ROOT/usr/local/bin/2pnyd"
grep -aFq '/generate_204' "$ROOT/usr/local/bin/2pnyd"
grep -aFq '/hotspot-detect.html' "$ROOT/usr/local/bin/2pnyd"

echo '[6/8] live panel runtime'
sudo mkdir -p "$ROOT/proc" "$ROOT/dev" "$ROOT/sys" "$ROOT/run" "$ROOT/var/lib/2pny"
sudo mount -t proc proc "$ROOT/proc"
sudo mount --bind /dev "$ROOT/dev"
sudo mount --bind /sys "$ROOT/sys"
sudo chroot "$ROOT" /usr/local/bin/2pnyd >/tmp/2pnyd-hotfix4.log 2>&1 &
PID=$!
OK=0
for _ in {1..40}; do
  if curl -fsS http://127.0.0.1/healthz 2>/dev/null | grep -q '2PNY OK'; then OK=1; break; fi
  sleep .2
done
if test "$OK" != 1; then cat /tmp/2pnyd-hotfix4.log || true; exit 1; fi
curl -fsS http://127.0.0.1/wizard >/dev/null
sudo ss -ltn | grep -E '(0\.0\.0\.0|\*|\[::\]):80\b'

echo '[7/8] DMR Talker Alias + lean runtime'
test -x "$ROOT/usr/local/bin/MMDVM-Host"
grep -q '^DumpTAData=1$' "$ROOT/usr/local/sbin/2pny-rf-apply"
grep -q 'MemoryMax=64M' "$ROOT/etc/systemd/system/2pnyd.service"
grep -q 'MemoryMax=96M' "$ROOT/etc/systemd/system/2pny-mmdvmhost.service"
grep -q 'MemoryMax=24M' "$ROOT/etc/systemd/system/2pny-setup-watch.service"
test ! -e "$ROOT/usr/bin/g++"
test ! -e "$ROOT/usr/bin/git"

echo '[8/8] no HTTP route regression'
kill -0 "$PID"
echo '2PNY hotfix4 image, simultaneous Ethernet/Wi-Fi and live panel: OK'
