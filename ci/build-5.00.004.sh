#!/usr/bin/env bash
set -euo pipefail
ARCH="${1:?arm32 or arm64}"
BASE_SHA="${2:?published v5.00.003 sha256}"
[[ "$ARCH" == arm32 || "$ARCH" == arm64 ]] || exit 2
[[ "$BASE_SHA" =~ ^[a-f0-9]{64}$ ]] || exit 2
WORK="$(mktemp -d)"
ROOT="$WORK/root"
LOOP=''
cleanup() {
 set +e
 mountpoint -q "$ROOT" && sudo umount "$ROOT"
 [[ -n "$LOOP" ]] && sudo losetup -d "$LOOP"
 rm -rf "$WORK"
}
trap cleanup EXIT
curl -fL --retry 3 "https://github.com/PU2PNY/2PNY-OS/releases/download/v5.00.003/PU2PNY-OS-5.00.003-$ARCH.img.xz" -o "$WORK/base.img.xz"
printf '%s  %s\n' "$BASE_SHA" "$WORK/base.img.xz" | sha256sum -c -
xz -t "$WORK/base.img.xz"
xz -dc "$WORK/base.img.xz" > "$WORK/image.img"
mkdir "$ROOT"
LOOP="$(sudo losetup --find --show --partscan "$WORK/image.img")"
sudo mount "${LOOP}p2" "$ROOT"
manifest() { (cd "$ROOT" && sudo find . -xdev -type f ! -path './lost+found/*' -print0 | sort -z | sudo xargs -0 sha256sum); }
manifest > "$WORK/before"
sudo bash ci/patch-image-5.00.004.sh "$ROOT"
manifest > "$WORK/after"
python3 - "$WORK/before" "$WORK/after" <<'PY'
import pathlib,sys
def read(path):
  result={}
  for line in pathlib.Path(path).read_text().splitlines():
    if '  ' not in line: continue
    digest,name=line.split('  ',1)
    result[name]=digest
  return result
before,after=map(read,sys.argv[1:])
allow={
 './etc/2pny/version',
 './usr/local/bin/2pnyd',
 './usr/local/sbin/2pny-audit',
}
changed={name for name in set(before)|set(after) if before.get(name)!=after.get(name)}
unexpected=changed-allow
if unexpected: raise SystemExit('Unexpected image changes: '+repr(sorted(unexpected)))
for item in ('./etc/2pny/version','./usr/local/sbin/2pny-audit'):
  assert item in changed
print('FULL_MANIFEST_SCOPE_PASS',len(changed))
PY
sudo bash -n "$ROOT/usr/local/sbin/2pny-audit"
[[ "$(cat "$ROOT/etc/2pny/version")" == "5.00.004" ]]
cmp runtime/diagnostics/2pny-audit-v5.sh "$ROOT/usr/local/sbin/2pny-audit"
sync
sudo umount "$ROOT"
sudo e2fsck -fn "${LOOP}p2"
sudo mount -o ro "${LOOP}p2" "$ROOT"
manifest > "$WORK/readonly"
cmp "$WORK/after" "$WORK/readonly"
sudo umount "$ROOT"
sudo losetup -d "$LOOP"
LOOP=''
OUT="PU2PNY-OS-5.00.004-$ARCH.img.xz"
xz -T2 -6 -c "$WORK/image.img" > "$OUT"
test -s "$OUT"
xz -t "$OUT"
sha256sum "$OUT" > "$OUT.sha256"
printf 'version=5.00.004\nbase_version=5.00.003\nbase_sha256=%s\nsource_commit=%s\narch=%s\nvalidation=SW_CI\nhw=NOT_VERIFIED\n' "$BASE_SHA" "$GITHUB_SHA" "$ARCH" > "BUILD-INFO-$ARCH.txt"
cat "$OUT.sha256" >> "BUILD-INFO-$ARCH.txt"
cp "$WORK/before" "BASELINE-MANIFEST-$ARCH.txt"
cp "$WORK/after" "IMAGE-MANIFEST-$ARCH.txt"
echo "PU2PNY_500003_IMAGE_OK $ARCH"
