#!/usr/bin/env bash
set -euo pipefail
ARCH="${1:?arm32 or arm64}"; BASE_SHA="${2:?immutable published image SHA256}"
[[ "$ARCH" == arm32 || "$ARCH" == arm64 ]] || exit 2
[[ "$BASE_SHA" =~ ^[a-f0-9]{64}$ ]] || exit 2
WORK="$(mktemp -d)"; ROOT="$WORK/root"; LOOP=''
cleanup(){
  set +e
  mountpoint -q "$ROOT" && sudo umount "$ROOT"
  [[ -n "$LOOP" ]] && sudo losetup -d "$LOOP"
  rm -rf "$WORK"
}
trap cleanup EXIT
curl -fL --retry 3 "https://github.com/PU2PNY/2PNY-OS/releases/download/v5.00.001/PU2PNY-OS-5.00.001-$ARCH.img.xz" -o "$WORK/base.xz"
printf '%s  %s\n' "$BASE_SHA" "$WORK/base.xz" | sha256sum -c -
xz -t "$WORK/base.xz"
xz -dc "$WORK/base.xz" > "$WORK/image.img"
mkdir "$ROOT"
LOOP="$(sudo losetup --find --show --partscan "$WORK/image.img")"
sudo mount "${LOOP}p2" "$ROOT"
# Full content manifest, not just a hand-picked list: only display paths/version may differ.
manifest(){ (cd "$ROOT" && sudo find . -xdev -type f ! -path './lost+found/*' -print0 | sort -z | sudo xargs -0 sha256sum); }
manifest > "$WORK/before"
sudo bash ci/patch-image-5.00.002-display.sh "$ROOT"
manifest > "$WORK/after"
python3 ci/verify-5.00.002-scope.py "$WORK/before" "$WORK/after"
file "$ROOT/usr/local/bin/MMDVM-Display" | tee "ARCH-$ARCH.txt"
if [[ "$ARCH" == arm64 ]]; then grep -qi aarch64 "ARCH-$ARCH.txt"; else grep -Eq '32-bit.*ARM' "ARCH-$ARCH.txt"; fi
sudo systemd-analyze --root="$ROOT" verify 2pny-display.service 2pny-display-adapter.service 2pny-nextiondriver.service
sync
sudo umount "$ROOT"
sudo e2fsck -fn "${LOOP}p2"
sudo mount -o ro "${LOOP}p2" "$ROOT"
[[ "$(cat "$ROOT/etc/2pny/version")" == '5.00.002' ]]
cmp runtime/display/apply.py "$ROOT/usr/local/sbin/2pny-display-apply"
manifest > "$WORK/readonly"
cmp "$WORK/after" "$WORK/readonly"
sudo umount "$ROOT"
sudo losetup -d "$LOOP"; LOOP=''
OUTPUT="PU2PNY-OS-5.00.002-$ARCH.img.xz"
xz -T2 -6 -c "$WORK/image.img" > "$OUTPUT"
xz -t "$OUTPUT"
sha256sum "$OUTPUT" > "$OUTPUT.sha256"
printf 'version=5.00.002\nbase_version=5.00.001\nbase_sha256=%s\nsource_commit=%s\narch=%s\nscope=DISPLAY_ONLY_VERIFIED_FULL_FILE_MANIFEST\nvalidation=SW_CI\nhw_display=PENDENTE\n' "$BASE_SHA" "$GITHUB_SHA" "$ARCH" > "BUILD-INFO-$ARCH.txt"
cat "$OUTPUT.sha256" >> "BUILD-INFO-$ARCH.txt"
cp "$WORK/before" "BASELINE-MANIFEST-$ARCH.txt"
cp "$WORK/after" "IMAGE-MANIFEST-$ARCH.txt"
echo DISPLAY_500002_IMAGE_OK
