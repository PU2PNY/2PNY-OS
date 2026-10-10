#!/bin/bash
set -euo pipefail

BASE_IMAGE_XZ="${1:?base ARM32 image xz required}"
OUT_BIN="${2:?output NextionDriver path required}"
OUT_SRC="${3:?output hardened source directory required}"
UPSTREAM_COMMIT="03b904270c9cb54f720d71753fc209afb1d9598f"

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORK="$(mktemp -d)"
IMG="$WORK/buildroot.img"
ROOT="$WORK/root"
LOOP=""
cleanup() {
  set +e
  mountpoint -q "$ROOT" && sudo umount "$ROOT"
  test -z "$LOOP" || sudo losetup -d "$LOOP" 2>/dev/null || true
  rm -rf "$WORK"
}
trap cleanup EXIT

rm -rf "$OUT_SRC"
git clone --quiet https://github.com/on7lds/NextionDriver.git "$OUT_SRC"
git -C "$OUT_SRC" checkout --quiet --detach "$UPSTREAM_COMMIT"
test "$(git -C "$OUT_SRC" rev-parse HEAD)" = "$UPSTREAM_COMMIT"
python3 "$REPO_ROOT/ci/harden-nextiondriver-0.3.31.118.py" "$OUT_SRC"
grep -Fq '/run/2pny-nextiondriver/ttyNextionDriver' "$OUT_SRC/NextionDriver.h"
! grep -REn '\b(system|popen)[[:space:]]*\(' --include='*.c' "$OUT_SRC"

xz -dc "$BASE_IMAGE_XZ" > "$IMG"
LOOP="$(sudo losetup --find --show --partscan "$IMG")"
sleep 1
ROOTDEV="$(lsblk -lnpo NAME,FSTYPE "$LOOP" | awk '$2=="ext4"{print $1;exit}')"
test -n "$ROOTDEV"
mkdir -p "$ROOT"
sudo mount "$ROOTDEV" "$ROOT"
test "$(sudo chroot "$ROOT" /usr/bin/dpkg --print-architecture)" = armhf

sudo rm -rf "$ROOT/tmp/nextiondriver-build"
sudo cp -a "$OUT_SRC" "$ROOT/tmp/nextiondriver-build"
sudo chroot "$ROOT" /bin/bash -c 'set -euo pipefail; export DEBIAN_FRONTEND=noninteractive; apt-get update; apt-get install -y --no-install-recommends gcc make; make -C /tmp/nextiondriver-build clean; make -C /tmp/nextiondriver-build -j2'

sudo cp "$ROOT/tmp/nextiondriver-build/NextionDriver" "$OUT_BIN"
sudo chown "$(id -u):$(id -g)" "$OUT_BIN"
chmod 0755 "$OUT_BIN"
file "$OUT_BIN" | grep -Eq 'ELF 32-bit.*ARM'
! file "$OUT_BIN" | grep -Eqi 'aarch64|ARM64'
strings "$OUT_BIN" | grep -Fq '/run/2pny-nextiondriver/ttyNextionDriver'
! strings "$OUT_BIN" | grep -Fq '/dev/ttyNextionDriver'
readelf -Ws "$OUT_BIN" | grep -Eq '[[:space:]](system|popen)@' && { echo 'forbidden libc shell symbol linked' >&2; exit 1; } || true
sudo chroot "$ROOT" /tmp/nextiondriver-build/NextionDriver -V | grep -Fq 'NextionDriver version'

# The final image is never modified by this build: this temporary buildroot is discarded.
echo ARM32_NEXTIONDRIVER_BUILD_OK
