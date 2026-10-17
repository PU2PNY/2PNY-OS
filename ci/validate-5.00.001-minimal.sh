#!/usr/bin/env bash
set -euo pipefail
ARCH="${1:-}"
XZ="${2:-}"
[[ "$ARCH" == arm32 || "$ARCH" == arm64 ]] || { echo 'usage: validate arm32|arm64 image.img.xz' >&2; exit 2; }
[[ -s "$XZ" ]] || { echo 'image missing' >&2; exit 2; }
xz -t "$XZ"
WORK="$(mktemp -d -p "${RUNNER_TEMP:-/tmp}" pu2pny-validate.XXXXXX)"
LOOP=''; MNT=''
cleanup(){ set +e; [[ -n "$MNT" ]] && sudo umount "$MNT" 2>/dev/null || true; [[ -n "$LOOP" ]] && sudo losetup -d "$LOOP" 2>/dev/null || true; rm -rf "$WORK"; }
trap cleanup EXIT
xz -dc "$XZ" > "$WORK/image.img"
LOOP="$(sudo losetup --find --show --partscan "$WORK/image.img")"
MNT="$WORK/root"; mkdir -p "$MNT"; sudo mount -o ro "${LOOP}p2" "$MNT"
[[ "$(sudo cat "$MNT/etc/2pny/version")" == '5.00.001' ]]
sudo grep -q 'Raspberry Pi' "$MNT/etc/os-release" || sudo grep -q 'Debian' "$MNT/etc/os-release"
for p in \
  usr/local/bin/MMDVM-Host \
  usr/local/bin/DMRGateway \
  usr/local/bin/2pnyd \
  usr/local/sbin/2pny-wifi-apply \
  usr/local/sbin/2pny-protocol-manager \
  usr/local/libexec/pu2pny/2pny-eventd \
  usr/local/libexec/pu2pny/2pny-network-manager \
  etc/systemd/system/2pny-eventd.service \
  etc/systemd/system/2pny-network-manager.service \
  usr/share/2pny; do
  sudo test -e "$MNT/$p" || { echo "missing $p" >&2; exit 3; }
done
sudo grep -Fq 'host-name=pu2pny' "$MNT/etc/avahi/avahi-daemon.conf"
sudo test -L "$MNT/etc/systemd/system/multi-user.target.wants/2pny-eventd.service"
sudo test -L "$MNT/etc/systemd/system/multi-user.target.wants/2pny-network-manager.service"
BIN_DESC="$(sudo file "$MNT/usr/local/bin/MMDVM-Host")"
if [[ "$ARCH" == arm64 ]]; then
  grep -Eqi 'aarch64|ARM aarch64|64-bit.*ARM' <<<"$BIN_DESC" || { echo "wrong ARM64 binary: $BIN_DESC" >&2; exit 4; }
else
  grep -Eqi 'ARM.*32-bit|ELF 32-bit.*ARM' <<<"$BIN_DESC" || { echo "wrong ARM32 binary: $BIN_DESC" >&2; exit 4; }
fi
# Minimal image must not contain desktop payloads inherited from full Raspberry Pi OS.
for forbidden in usr/bin/startx usr/bin/chromium usr/bin/libreoffice; do
  sudo test ! -e "$MNT/$forbidden" || { echo "unexpected desktop payload: $forbidden" >&2; exit 5; }
done
sudo systemd-analyze --root="$MNT" verify \
  "$MNT/etc/systemd/system/2pny-eventd.service" \
  "$MNT/etc/systemd/system/2pny-hardware-manager.service" \
  "$MNT/etc/systemd/system/2pny-network-manager.service" || exit 6
sudo umount "$MNT"; MNT=''
sudo e2fsck -fn "${LOOP}p2"
sudo losetup -d "$LOOP"; LOOP=''
sha256sum "$XZ"
stat -c '%s' "$XZ"
echo VALIDATE_500001_MINIMAL_OK
