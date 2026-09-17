#!/usr/bin/env bash
set -euo pipefail
IMAGE_XZ="${1:?image .img.xz required}"
VERSION="${2:-0.1.8-alpha}"
WORK="$(mktemp -d)"
IMG="$WORK/2pny.img"
ROOT="$WORK/root"
BOOT="$WORK/boot"
cleanup(){ set +e; mountpoint -q "$BOOT" && sudo umount "$BOOT"; mountpoint -q "$ROOT" && sudo umount "$ROOT"; [[ -n "${LOOP:-}" ]] && sudo losetup -d "$LOOP" 2>/dev/null; rm -rf "$WORK"; }
trap cleanup EXIT

xz -dc "$IMAGE_XZ" > "$IMG"
LOOP="$(sudo losetup --find --show --partscan "$IMG")"
mkdir -p "$ROOT" "$BOOT"
sudo mount "${LOOP}p2" "$ROOT"
sudo mount "${LOOP}p1" "$BOOT"

printf '[1/7] Filesystem and base OS\n'
sudo e2fsck -fn "${LOOP}p2" >/dev/null || rc=$?; rc=${rc:-0}; [[ "$rc" -lt 4 ]]
grep -q 'VERSION_CODENAME=bookworm' "$ROOT/etc/os-release"
[[ "$(cat "$ROOT/etc/2pny/version")" == "$VERSION" ]]

printf '[2/7] Explicit network runtime packages\n'
for bin in usr/sbin/hostapd usr/sbin/dnsmasq usr/sbin/iw usr/sbin/rfkill usr/local/sbin/2pny-network-core usr/local/bin/2pnyd; do
  test -x "$ROOT/$bin"
done

printf '[3/7] First-access contracts\n'
grep -q '^ssid=2PNY-SETUP$' "$ROOT/etc/2pny/hostapd-setup.conf"
grep -q '^wpa=0$' "$ROOT/etc/2pny/hostapd-setup.conf"
grep -q '^interface=wlan0$' "$ROOT/etc/2pny/dnsmasq-wifi.conf"
grep -q 'dhcp-range=10.42.0.20,10.42.0.150' "$ROOT/etc/2pny/dnsmasq-wifi.conf"
grep -q '^address=/#/10.42.0.1$' "$ROOT/etc/2pny/dnsmasq-wifi.conf"
grep -q '^interface=eth0$' "$ROOT/etc/2pny/dnsmasq-ethernet.conf"
grep -q 'dhcp-range=10.43.0.20,10.43.0.150' "$ROOT/etc/2pny/dnsmasq-ethernet.conf"
grep -q 'ip addr add 10.42.0.1/24' "$ROOT/usr/local/sbin/2pny-network-core"
grep -q 'ip addr add 10.43.0.1/24' "$ROOT/usr/local/sbin/2pny-network-core"
! test -e "$ROOT/etc/NetworkManager/system-connections/2pny-setup.nmconnection"
! test -e "$ROOT/etc/NetworkManager/system-connections/2pny-ethernet-setup.nmconnection"

printf '[4/7] Service ownership and clean image\n'
test -L "$ROOT/etc/systemd/system/multi-user.target.wants/2pny-network-core.service"
! test -e "$ROOT/etc/systemd/system/multi-user.target.wants/2pny-setup-watch.service"
! test -e "$ROOT/var/lib/2pny/provisioned"
grep -q '0.0.0.0:80' "$ROOT/usr/local/bin/2pnyd" 2>/dev/null || true
grep -q '^DumpTAData=1$' "$ROOT/usr/local/sbin/2pny-rf-apply"

printf '[5/7] Script syntax\n'
for f in usr/local/sbin/2pny-network-core usr/local/sbin/2pny-ap-control usr/local/sbin/2pny-firstboot; do
  sudo chroot "$ROOT" /bin/bash -n "/$f"
done

printf '[6/7] Execute real ARM64 panel from final image\n'
sudo mkdir -p "$ROOT/var/lib/2pny"
sudo chown root:root "$ROOT/var/lib/2pny"
# Use chroot but bind only the minimal pseudo-filesystems needed by the static daemon.
for p in proc sys dev; do sudo mount --bind "/$p" "$ROOT/$p"; done
PANEL_PID=""
set +e
sudo chroot "$ROOT" /usr/local/bin/2pnyd >/tmp/2pnyd-final-image.log 2>&1 &
PANEL_PID=$!
set -e
for _ in {1..30}; do
  if curl -fsS http://127.0.0.1/healthz >/dev/null 2>&1; then break; fi
  sleep .2
done
curl -fsS http://127.0.0.1/healthz >/dev/null
curl -fsS http://127.0.0.1/wizard >/dev/null
curl -fsS http://127.0.0.1/api/modules >/dev/null
sudo kill "$PANEL_PID" 2>/dev/null || true
wait "$PANEL_PID" 2>/dev/null || true
for p in dev sys proc; do sudo umount "$ROOT/$p"; done

printf '[7/7] DHCP daemon config parser\n'
sudo chroot "$ROOT" /usr/sbin/dnsmasq --test --conf-file=/etc/2pny/dnsmasq-wifi.conf >/dev/null
sudo chroot "$ROOT" /usr/sbin/dnsmasq --test --conf-file=/etc/2pny/dnsmasq-ethernet.conf >/dev/null

echo 'OK: 2PNY 0.1.8 final image network core validated'
