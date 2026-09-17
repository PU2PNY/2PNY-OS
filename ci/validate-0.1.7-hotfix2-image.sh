#!/usr/bin/env bash
set -euo pipefail
IMAGE="${1:?image required}"
VERSION="${2:-0.1.7-hotfix2}"
RAW="${IMAGE%.xz}.validate"
ROOT=/mnt/2pny-h2
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
  rm -f "$RAW"
}
trap cleanup EXIT

xz -t "$IMAGE"
EXPECTED=$(awk '{print $1}' "${IMAGE}.sha256")
ACTUAL=$(sha256sum "$IMAGE" | awk '{print $1}')
test "$EXPECTED" = "$ACTUAL"
xz -dc "$IMAGE" > "$RAW"
LOOP=$(sudo losetup --find --partscan --show "$RAW")
for _ in {1..20}; do test -b "${LOOP}p2" && break; sleep .25; done
sudo mkdir -p "$ROOT"
sudo mount "${LOOP}p2" "$ROOT"
sudo mkdir -p "$ROOT/boot/firmware"
sudo mount "${LOOP}p1" "$ROOT/boot/firmware"

echo '[1/6] image contract'
grep -q "$VERSION" "$ROOT/etc/2pny/version"
test -x "$ROOT/usr/local/bin/2pnyd"
test -x "$ROOT/usr/local/sbin/2pny-ap-control"
test -x "$ROOT/usr/local/sbin/2pny-setup-watch"

echo '[2/6] open captive AP'
grep -q 'address1=10.42.0.1/24' "$ROOT/etc/NetworkManager/system-connections/2pny-setup.nmconnection"
! grep -q '\[wifi-security\]' "$ROOT/etc/NetworkManager/system-connections/2pny-setup.nmconnection"
grep -q 'address=/#/10.42.0.1' "$ROOT/etc/NetworkManager/dnsmasq-shared.d/2pny-captive.conf"
bash -n "$ROOT/usr/local/sbin/2pny-ap-control"

echo '[3/6] responsive/captive binary markers'
grep -aFq '/healthz' "$ROOT/usr/local/bin/2pnyd"
grep -aFq '/api/ap' "$ROOT/usr/local/bin/2pnyd"
grep -aFq '/generate_204' "$ROOT/usr/local/bin/2pnyd"
grep -aFq '/hotspot-detect.html' "$ROOT/usr/local/bin/2pnyd"
grep -aFq '2pny-responsive-hotfix2' "$ROOT/usr/local/bin/2pnyd"
grep -aFq '2pny-ap-runtime-v1' "$ROOT/usr/local/bin/2pnyd"

echo '[4/6] display discovery'
python3 -c 'import sys; p=sys.argv[1]; compile(open(p,encoding="utf-8").read(),p,"exec")' "$ROOT/usr/local/sbin/2pny-hardware-probe"
grep -q 'probe_configured_display' "$ROOT/usr/local/sbin/2pny-hardware-probe"

echo '[5/6] panel runtime'
sudo mkdir -p "$ROOT/proc" "$ROOT/dev" "$ROOT/sys" "$ROOT/run" "$ROOT/var/lib/2pny"
sudo mount -t proc proc "$ROOT/proc"
sudo mount --bind /dev "$ROOT/dev"
sudo mount --bind /sys "$ROOT/sys"
sudo chroot "$ROOT" /usr/local/bin/2pnyd >/tmp/2pnyd-hotfix2.log 2>&1 &
PID=$!
OK=0
for _ in {1..30}; do
  if curl -fsS http://127.0.0.1/healthz 2>/dev/null | grep -q '2PNY OK'; then OK=1; break; fi
  sleep .2
done
if test "$OK" != 1; then cat /tmp/2pnyd-hotfix2.log || true; exit 1; fi
curl -fsS http://127.0.0.1/wizard >/dev/null
CODE=$(curl -sS -o /dev/null -w '%{http_code}' http://127.0.0.1/generate_204)
test "$CODE" = 302
sudo ss -ltn | grep -E '(0\.0\.0\.0|\*|\[::\]):80\b'

echo '[6/6] RF and lean runtime preserved'
test -x "$ROOT/usr/local/bin/MMDVM-Host"
grep -q 'MemoryMax=64M' "$ROOT/etc/systemd/system/2pnyd.service"
grep -q 'MemoryMax=96M' "$ROOT/etc/systemd/system/2pny-mmdvmhost.service"
test ! -e "$ROOT/usr/bin/g++"
test ! -e "$ROOT/usr/bin/git"

echo '2PNY hotfix2 image and live panel: OK'
