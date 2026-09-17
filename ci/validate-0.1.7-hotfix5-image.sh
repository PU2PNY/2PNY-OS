#!/usr/bin/env bash
set -euo pipefail
IMAGE="${1:?image required}"
VERSION="${2:-0.1.7-hotfix5}"
RAW="/tmp/2PNY-OS-${VERSION}-validate.img"
ROOT=/mnt/2pny-h5
PID=''; LOOP=''
cleanup(){ set +e; test -n "$PID" && sudo kill "$PID" 2>/dev/null || true; sudo umount "$ROOT/proc" "$ROOT/dev" "$ROOT/sys" "$ROOT/boot/firmware" "$ROOT" 2>/dev/null || true; test -n "$LOOP" && sudo losetup -d "$LOOP" 2>/dev/null || true; sudo rm -f "$RAW"; }
trap cleanup EXIT
xz -t "$IMAGE"
EXPECTED=$(awk '{print $1}' "${IMAGE}.sha256"); ACTUAL=$(sha256sum "$IMAGE"|awk '{print $1}'); test "$EXPECTED" = "$ACTUAL"
sudo sh -c "xz -dc '$IMAGE' > '$RAW'"
LOOP=$(sudo losetup --find --partscan --show "$RAW")
for _ in {1..20}; do test -b "${LOOP}p2" && break; sleep .25; done
sudo mkdir -p "$ROOT"; sudo mount "${LOOP}p2" "$ROOT"; sudo mkdir -p "$ROOT/boot/firmware"; sudo mount "${LOOP}p1" "$ROOT/boot/firmware"

echo '[1/8] Bookworm base'
grep -q '^VERSION_CODENAME=bookworm$' "$ROOT/etc/os-release"
grep -q "$VERSION" "$ROOT/etc/2pny/version"
test -x "$ROOT/usr/bin/nmcli"; test -x "$ROOT/usr/sbin/NetworkManager"; test -x "$ROOT/usr/sbin/dnsmasq"; test -x "$ROOT/usr/sbin/rfkill" || test -x "$ROOT/usr/bin/rfkill"

echo '[2/8] NetworkManager appliance ownership'
grep -q '^no-auto-default=\*$' "$ROOT/etc/NetworkManager/conf.d/20-2pny-appliance.conf"
! grep -q '\[wifi-security\]' "$ROOT/etc/NetworkManager/system-connections/2pny-setup.nmconnection"
grep -q '^address1=10.42.0.1/24$' "$ROOT/etc/NetworkManager/system-connections/2pny-setup.nmconnection"
grep -q '^address1=10.43.0.1/24$' "$ROOT/etc/NetworkManager/system-connections/2pny-ethernet-setup.nmconnection"

echo '[3/8] first-access services'
test -L "$ROOT/etc/systemd/system/multi-user.target.wants/2pnyd.service"
test -L "$ROOT/etc/systemd/system/multi-user.target.wants/2pny-firstboot.service"
test -L "$ROOT/etc/systemd/system/multi-user.target.wants/2pny-setup-watch.service"
bash -n "$ROOT/usr/local/sbin/2pny-firstboot"; bash -n "$ROOT/usr/local/sbin/2pny-setup-watch"; bash -n "$ROOT/usr/local/sbin/2pny-ap-control"

echo '[4/8] no stale provisioned state'
test ! -e "$ROOT/var/lib/2pny/provisioned"

echo '[5/8] panel runtime'
sudo mkdir -p "$ROOT/proc" "$ROOT/dev" "$ROOT/sys" "$ROOT/run" "$ROOT/var/lib/2pny"
sudo mount -t proc proc "$ROOT/proc"; sudo mount --bind /dev "$ROOT/dev"; sudo mount --bind /sys "$ROOT/sys"
sudo chroot "$ROOT" /usr/local/bin/2pnyd >/tmp/2pnyd-h5.log 2>&1 & PID=$!
OK=0; for _ in {1..40}; do curl -fsS http://127.0.0.1/healthz 2>/dev/null | grep -q '2PNY OK' && { OK=1; break; }; sleep .2; done
test "$OK" = 1 || { cat /tmp/2pnyd-h5.log; exit 1; }
curl -fsS http://127.0.0.1/wizard >/dev/null
sudo ss -ltn | grep -E '(0\.0\.0\.0|\*|\[::\]):80\b'

echo '[6/8] RF/Talker Alias'
test -x "$ROOT/usr/local/bin/MMDVM-Host"; grep -q '^DumpTAData=1$' "$ROOT/usr/local/sbin/2pny-rf-apply"

echo '[7/8] lean runtime'
grep -q 'MemoryMax=64M' "$ROOT/etc/systemd/system/2pnyd.service"; grep -q 'MemoryMax=96M' "$ROOT/etc/systemd/system/2pny-mmdvmhost.service"

echo '[8/8] done'
echo '2PNY hotfix5 Bookworm image and deterministic first-access contract: OK'
