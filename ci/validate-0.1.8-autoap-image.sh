#!/usr/bin/env bash
set -euo pipefail
IMG_XZ="${1:?image.xz required}"
VERSION="${2:-0.1.8-alpha}"
WORK="$(mktemp -d)"
cleanup(){ sudo umount "$WORK/root" "$WORK/boot" 2>/dev/null || true; [[ -n "${LOOP:-}" ]] && sudo losetup -d "$LOOP" 2>/dev/null || true; rm -rf "$WORK"; }
trap cleanup EXIT
xz -dc "$IMG_XZ" > "$WORK/image.img"
LOOP="$(sudo losetup --find --show --partscan "$WORK/image.img")"
mkdir -p "$WORK/root" "$WORK/boot"
sudo mount "${LOOP}p2" "$WORK/root"
sudo mount "${LOOP}p1" "$WORK/boot"
R="$WORK/root"

echo '[1/8] Base OS and binaries'
grep -qi 'bookworm' "$R/etc/os-release"
test -x "$R/usr/local/bin/2pnyd"
test -x "$R/usr/local/sbin/2pny-networkd"
test -x "$R/usr/sbin/hostapd"
test -x "$R/usr/sbin/dnsmasq"

echo '[2/8] Explicit AutoAP contracts'
test -L "$R/etc/systemd/system/multi-user.target.wants/2pny-networkd.service"
test -f "$R/etc/hostapd/hostapd-2pny.conf"
test -f "$R/etc/dnsmasq.d/2pny-setup.conf"
grep -q '^ssid=2PNY-SETUP$' "$R/etc/hostapd/hostapd-2pny.conf"
! grep -Eq 'wpa=|wpa_passphrase|wpa_key_mgmt' "$R/etc/hostapd/hostapd-2pny.conf"
grep -q '10.42.0.20,10.42.0.80' "$R/etc/dnsmasq.d/2pny-setup.conf"
grep -q '10.43.0.20,10.43.0.80' "$R/etc/dnsmasq.d/2pny-setup.conf"
grep -q '10.42.0.1' "$R/usr/local/sbin/2pny-networkd"
grep -q '10.43.0.1' "$R/usr/local/sbin/2pny-networkd"

echo '[3/8] Version/panel'
grep -q "$VERSION" "$R/etc/2pny/version"
test -x "$R/usr/local/bin/2pnyd"

echo '[4/8] No stale state'
test ! -e "$R/var/lib/2pny/provisioned"
test ! -e "$R/var/lib/2pny/ap-disabled"

echo '[5/8] MMDVM/Talker Alias preserved'
grep -q '^DumpTAData=1$' "$R/usr/local/sbin/2pny-rf-apply"
test -f "$R/etc/systemd/system/2pny-mmdvmhost.service"

echo '[6/8] NetworkManager keyfile permissions'
if [ -d "$R/etc/NetworkManager/system-connections" ]; then
  while IFS= read -r -d '' f; do
    mode="$(stat -c '%a' "$f")"
    case "$mode" in 600|400) ;; *) echo "bad keyfile mode $mode: $f" >&2; exit 1;; esac
  done < <(find "$R/etc/NetworkManager/system-connections" -type f -name '*.nmconnection' -print0)
fi

echo '[7/8] Filesystem integrity'
sudo umount "$WORK/boot" "$WORK/root"
sudo e2fsck -fn "${LOOP}p2"
sudo mount "${LOOP}p2" "$WORK/root"
sudo mount "${LOOP}p1" "$WORK/boot"

echo '[8/8] Execute panel from final ARM64 rootfs'
PORT=18080
sudo env LISTEN_ADDR="127.0.0.1:$PORT" "$R/usr/local/bin/2pnyd" >"$WORK/2pnyd.log" 2>&1 &
PID=$!
for _ in {1..40}; do
  curl -fsS "http://127.0.0.1:$PORT/healthz" >/dev/null 2>&1 && break
  sleep .25
done
curl -fsS "http://127.0.0.1:$PORT/healthz" >/dev/null
curl -fsS "http://127.0.0.1:$PORT/wizard" >/dev/null
kill "$PID" 2>/dev/null || true
wait "$PID" 2>/dev/null || true

echo 'OK: 2PNY 0.1.8 final image contracts validated'
