#!/usr/bin/env bash
# REL-015 permanent release gate: run before every version-specific final validator.
set -euo pipefail

if (( EUID != 0 )); then
  exec sudo bash "$0" "$@"
fi

IMAGE="${1:?image required}"
VERSION="${2:?version required}"
SHA_FILE="$IMAGE.sha256"
RAW="/tmp/pu2pny-preflight-${VERSION}.img"
ROOT="/mnt/pu2pny-preflight"
LOOP=""

cleanup() {
  set +e
  mountpoint -q "$ROOT" && umount "$ROOT" 2>/dev/null || true
  test -n "$LOOP" && losetup -d "$LOOP" 2>/dev/null || true
  rm -f "$RAW"
}
trap cleanup EXIT
trap 'echo "PREVALIDATION_FAILED line=$LINENO command=$BASH_COMMAND" >&2' ERR

echo '[preflight 1/6] compressed image + checksum'
test -s "$IMAGE"
test -s "$SHA_FILE"
xz -t "$IMAGE"
EXPECTED="$(awk '{print $1}' "$SHA_FILE")"
ACTUAL="$(sha256sum "$IMAGE" | awk '{print $1}')"
test -n "$EXPECTED"
test "$EXPECTED" = "$ACTUAL"

echo '[preflight 2/6] mount generated image read-only'
rm -f "$RAW"
xz -dc "$IMAGE" > "$RAW"
LOOP="$(losetup --find --partscan --show --read-only "$RAW")"
for _ in {1..80}; do
  test -b "${LOOP}p2" && break
  sleep .25
done
test -b "${LOOP}p2"
mkdir -p "$ROOT"
mount -o ro "${LOOP}p2" "$ROOT"

echo '[preflight 3/6] identity + essential runtime'
grep -Fxq "$VERSION" "$ROOT/etc/2pny/version"
grep -Fxq 'pu2pny' "$ROOT/etc/hostname"
for p in   "$ROOT/usr/local/bin/2pnyd"   "$ROOT/usr/local/bin/MMDVM-Host"   "$ROOT/usr/local/bin/DMRGateway"   "$ROOT/usr/local/bin/dstargateway"   "$ROOT/usr/local/bin/YSFGateway"   "$ROOT/usr/local/libexec/2pny-dmr-apply"   "$ROOT/usr/local/sbin/2pny-protocol-network-apply"   "$ROOT/usr/share/2pny/dashboard.html"   "$ROOT/usr/share/2pny/hotspot.html"   "$ROOT/usr/share/2pny/internet.html"   "$ROOT/usr/share/2pny/expert.html"; do
  test -s "$p"
done

echo '[preflight 4/6] browser identity + critical UI'
for page in "$ROOT"/usr/share/2pny/*.html; do
  test -f "$page" || continue
  if grep -Fqi '<head' "$page"; then
    grep -Fq '<title>PU2PNY-OS</title>' "$page"
  fi
done
grep -Fq "document.title='PU2PNY-OS'" "$ROOT/usr/share/2pny/ui-common-0.3.0.js"

echo '[preflight 5/6] DMR baseline + D-Star voice package'
strings "$ROOT/usr/local/bin/DMRGateway" | grep -Fq 'PU2PNY, XLX module control'
strings "$ROOT/usr/local/bin/DMRGateway" | grep -Fq 'PU2PNY, XLX status voice requested'
test -s "$ROOT/usr/local/share/dstargateway.d/en_GB.ambe"
test -s "$ROOT/usr/local/share/dstargateway.d/en_GB.indx"
grep -Fq 'audio_path="/usr/local/share/dstargateway.d/"' "$ROOT/usr/local/sbin/2pny-protocol-network-apply"

echo '[preflight 6/6] protocol services + no provisioned runtime state'
for svc in   2pny-mmdvmhost.service   2pny-dmrgateway.service   2pny-dstargateway.service   2pny-ysfgateway.service; do
  test -s "$ROOT/etc/systemd/system/$svc"
done
for p in   "$ROOT/var/lib/2pny/provisioned"   "$ROOT/var/lib/2pny/rf-configured"   "$ROOT/var/lib/2pny/network-radio.json"; do
  test ! -e "$p"
done

echo 'PU2PNY_PREVALIDATION_OK'
