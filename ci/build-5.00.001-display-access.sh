#!/usr/bin/env bash
set -euo pipefail
[[ "$#" -eq 2 ]] || { echo 'usage: build.sh arm32|arm64 base-sha256' >&2; exit 2; }
ARCH="$1"; BASE_SHA="$2"
[[ "$ARCH" == arm32 || "$ARCH" == arm64 ]] || exit 2
[[ "$BASE_SHA" =~ ^[0-9a-f]{64}$ ]] || exit 2
REPO="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO"
if [[ "$ARCH" == arm32 ]]; then GOARCH_TARGET=arm; GOARM_TARGET=6; else GOARCH_TARGET=arm64; GOARM_TARGET=0; fi
python3 ci/patch-backend-5.00.000.py src/2pnyd-main-0.3.27.go /tmp/go-500000.go
python3 ci/patch-display-5.00.001.py go /tmp/go-500000.go /tmp/go-500001.go
python3 ci/patch-display-5.00.001.py display-apply src/2pny-display-apply-0.3.30.py /tmp/display-apply-500001.py
gofmt -w /tmp/go-500001.go
go test /tmp/go-500001.go
GOOS=linux GOARCH="$GOARCH_TARGET" GOARM="$GOARM_TARGET" CGO_ENABLED=0 \
  go build -trimpath -ldflags='-s -w' -o /tmp/2pnyd-500001 /tmp/go-500001.go
if [[ "$ARCH" == arm32 ]]; then
  file /tmp/2pnyd-500001 | grep -Eq 'ELF 32-bit.*ARM'
else
  file /tmp/2pnyd-500001 | grep -Eqi 'aarch64|ARM aarch64'
fi
grep -Fq 'appVersion            = "5.00.001"' /tmp/go-500001.go
grep -Fq 'rfAccessPolicyHandler' /tmp/go-500001.go
python3 -m py_compile /tmp/display-apply-500001.py

BASE="PU2PNY-OS-5.00.000-$ARCH.img.xz"
curl -fL --retry 3 --retry-delay 2 \
  "https://github.com/PU2PNY/2PNY-OS/releases/download/v5.00.000/$BASE" -o /tmp/pu2pny-base.img.xz
printf '%s  %s\n' "$BASE_SHA" /tmp/pu2pny-base.img.xz | sha256sum -c -
xz -t /tmp/pu2pny-base.img.xz
xz -dc /tmp/pu2pny-base.img.xz > /tmp/pu2pny-recovery.img
ROOT="$(mktemp -d /tmp/pu2pny-500001-root.XXXXXX)"
LOOP=''
cleanup(){
  set +e
  mountpoint -q "$ROOT" && sudo umount "$ROOT"
  [[ -n "$LOOP" ]] && sudo losetup -d "$LOOP" 2>/dev/null || true
  rmdir "$ROOT" 2>/dev/null || true
}
trap cleanup EXIT
LOOP="$(sudo losetup --find --show --partscan /tmp/pu2pny-recovery.img)"
PART="$LOOP"p2
sudo mount "$PART" "$ROOT"
[[ "$(sudo cat "$ROOT/etc/2pny/version")" == '5.00.000' ]]

protect_manifest(){
  local out="$1" p
  : > "$out"
  for p in \
    usr/local/bin/MMDVM-Host \
    usr/local/bin/DMRGateway \
    usr/local/bin/NextionDriver-pu2pny \
    usr/local/bin/MMDVM-Display \
    etc/systemd/system/2pny-mmdvmhost.service \
    usr/local/sbin/2pny-protocol-manager \
    usr/local/sbin/2pny-wifi-apply \
    usr/local/libexec/2pny-dmr-apply \
    usr/local/sbin/2pny-protocol-network-apply \
    var/lib/2pny/mmdvm/MMDVM-Host.ini; do
    if sudo test -e "$ROOT/$p"; then (cd "$ROOT" && sudo sha256sum "$p") >> "$out"; else printf 'ABSENT  %s\n' "$p" >> "$out"; fi
  done
}
protect_manifest /tmp/protected.before
sudo bash ci/patch-image-5.00.001-recovery.sh "$ROOT" /tmp/2pnyd-500001 /tmp/display-apply-500001.py
protect_manifest /tmp/protected.after
diff -u /tmp/protected.before /tmp/protected.after
sudo systemd-analyze --root="$ROOT" verify 2pny-rf-access.service 2pny-rf-access.path 2pny-mmdvmhost.service
sudo test -x "$ROOT/usr/local/libexec/pu2pny/2pny-rf-access"
sudo test -s "$ROOT/usr/share/2pny/rf-access.html"
sudo grep -Fq 'Acesso RF: Privado' "$ROOT/usr/share/2pny/hotspot.html"
[[ "$(sudo cat "$ROOT/etc/2pny/version")" == '5.00.001' ]]
printf 'version=5.00.001\nbase_version=5.00.000\nbase_sha256=%s\nsource_commit=%s\narch=%s\nrf_baseline_hashes=IDENTICAL\nhw_displays=PENDENTE\ndisplay_hw_prior=FAIL_REPORTADO\nclassification=ALPHA_CANDIDATA_TESTE_FISICO\n' \
  "$BASE_SHA" "$GITHUB_SHA" "$ARCH" > "BUILD-INFO-$ARCH.txt"
cp /tmp/protected.before "PROTECTED-HASHES-$ARCH.txt"
sync
sudo umount "$ROOT"
sudo e2fsck -fn "$PART"
sudo mount -o ro "$PART" "$ROOT"
[[ "$(sudo cat "$ROOT/etc/2pny/version")" == '5.00.001' ]]
protect_manifest /tmp/protected.readonly
diff -u /tmp/protected.before /tmp/protected.readonly
sudo test -L "$ROOT/etc/systemd/system/multi-user.target.wants/2pny-rf-access.path"
sudo umount "$ROOT"
sudo losetup -d "$LOOP"; LOOP=''
rmdir "$ROOT"; trap - EXIT
OUTPUT="PU2PNY-OS-5.00.001-$ARCH.img.xz"
xz -T0 -6 -c /tmp/pu2pny-recovery.img > "$OUTPUT"
test -s "$OUTPUT"
xz -t "$OUTPUT"
sha256sum "$OUTPUT" > "$OUTPUT.sha256"
cat "$OUTPUT.sha256" >> "BUILD-INFO-$ARCH.txt"
cat "$OUTPUT.sha256"
stat -c '%n %s' "$OUTPUT"
echo BUILD_500001_RECOVERY_OK
