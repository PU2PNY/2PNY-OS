#!/usr/bin/env bash
set -euo pipefail

VERSION="0.1.9-hotfix1-alpha"
TAG="v0.1.9-hotfix1-alpha"
ROOT="$GITHUB_WORKSPACE/legacy-source/2pny-os"

bash "$ROOT/bootstrap.sh"
for f in \
  ci/prepare-0.1.2.sh \
  ci/prepare-0.1.3.sh \
  ci/prepare-0.1.4-ui.sh \
  ci/prepare-0.1.5-hardware.sh \
  ci/prepare-0.1.5-fixes.sh \
  ci/prepare-0.1.6-rf.sh \
  ci/prepare-0.1.6-build-fix.sh \
  ci/prepare-0.1.7-modules.sh \
  ci/prepare-0.1.7-hotfix1-ethernet.sh \
  ci/prepare-0.1.7-hotfix2-listener-prep.sh \
  ci/prepare-0.1.7-hotfix2-captive-responsive.sh \
  ci/prepare-0.1.7-hotfix2-review-fixes.sh \
  ci/prepare-0.1.7-hotfix2-route-dedupe.sh \
  ci/prepare-0.1.7-hotfix3-network-stability.sh \
  ci/prepare-0.1.7-hotfix3-compat-talkeralias.sh \
  ci/prepare-0.1.7-hotfix4-dual-network.sh \
  ci/prepare-0.1.7-hotfix4-validator-fix.sh \
  ci/prepare-0.1.7-hotfix5-bookworm-network.sh \
  ci/prepare-0.1.7-hotfix5-base-fix.sh \
  ci/prepare-0.1.7-hotfix5-validator-compat.sh \
  ci/prepare-0.1.8-anchor-compat.sh \
  ci/prepare-0.1.8-network-core.sh \
  ci/prepare-0.1.8-builder-service-fix.sh \
  ci/prepare-0.1.9-pu2pny-hardware-ui.sh \
  ci/prepare-0.1.9-network-pid-fix.sh \
  ci/prepare-0.1.9-build-metadata-fix.sh \
  ci/prepare-0.1.9-hotfix1-hardware-status.sh; do
  bash "$GITHUB_WORKSPACE/$f" "$ROOT"
done

cd "$ROOT"
gofmt -w src/2pnyd/main.go
go test ./...
bash -n rootfs-overlay/usr/local/sbin/2pny-network-core
bash -n rootfs-overlay/usr/local/sbin/2pny-network-switch
bash -n rootfs-overlay/usr/local/sbin/2pny-ap-control
bash -n rootfs-overlay/usr/local/sbin/2pny-hardware-drivers
bash -n rootfs-overlay/usr/local/sbin/2pny-mdns-alias
python3 -m py_compile rootfs-overlay/usr/local/sbin/2pny-hardware-probe
rm -rf rootfs-overlay/usr/local/sbin/__pycache__
grep -Fq "fetch('/api/hardware/status'" src/2pnyd/main.go
grep -Fq 'http.HandleFunc("/api/hardware/status", hardwareStatusHandler)' src/2pnyd/main.go
grep -Fq 'http.HandleFunc("/api/hardware", hardwareHandler)' src/2pnyd/main.go
grep -Fq 'candidate_reason' rootfs-overlay/usr/local/sbin/2pny-hardware-probe
grep -Fq "$VERSION" src/2pnyd/main.go

sudo -E VERSION="$VERSION" ./builder/build-image.sh
OLD="$(sudo find dist -maxdepth 1 -type f -name '*.img.xz' -print -quit)"
test -n "$OLD"
IMAGE="dist/PU2PNY-OS-${VERSION}-arm64.img.xz"
if [[ "$OLD" != "$IMAGE" ]]; then sudo mv "$OLD" "$IMAGE"; fi
sudo rm -f dist/*.img.xz.sha256
sudo sha256sum "$IMAGE" | sudo tee "${IMAGE}.sha256" >/dev/null
sudo chown "$USER:$USER" "$IMAGE" "${IMAGE}.sha256" dist/BUILD-INFO.txt
xz -t "$IMAGE"
sha256sum -c "${IMAGE}.sha256"
bash "$GITHUB_WORKSPACE/ci/validate-0.1.9-image.sh" "$IMAGE" "$VERSION"

cat > RELEASE-NOTES.md <<'EOF'
PU2PNY OS 0.1.9 Hotfix1 Alpha — Raspberry Pi 4 ARM64.

Critical hardware wizard fix:
- fixed the wizard polling the old /api/hardware response format;
- added dedicated /api/hardware/status while preserving the legacy endpoint;
- Raspberry model, serial ports, HAT and I2C can appear while serial probing continues;
- /dev/serial0 is exposed only as a candidate when MMDVM GET_VERSION does not answer;
- the UI no longer falsely remains blank until timeout because of the endpoint mismatch;
- existing 0.1.9 network, AP, responsive UI, RF rollback, MMDVMHost and Talker Alias behavior is preserved.

First access:
Wi-Fi: 2PNY-SETUP -> http://10.42.0.1
Direct Ethernet: http://10.43.0.1
Normal LAN: http://pu2pny.local
EOF

# Remove any incomplete or previous release with this exact tag.
for rid in $(gh api "repos/$GITHUB_REPOSITORY/releases?per_page=100" --jq ".[] | select(.tag_name == \"$TAG\") | .id" 2>/dev/null || true); do
  gh api --method DELETE "repos/$GITHUB_REPOSITORY/releases/$rid" >/dev/null || true
done
gh api --method DELETE "repos/$GITHUB_REPOSITORY/git/refs/tags/$TAG" >/dev/null 2>&1 || true

REL_ID="$(gh api --method POST "repos/$GITHUB_REPOSITORY/releases" \
  -f tag_name="$TAG" \
  -f target_commitish="$GITHUB_SHA" \
  -f name='PU2PNY OS 0.1.9 Hotfix1 Alpha' \
  -F body=@RELEASE-NOTES.md \
  -F draft=true \
  -F prerelease=true \
  --jq '.id')"
test -n "$REL_ID"

upload_asset() {
  local file="$1" ctype="$2" name local_size remote_size ids attempt
  name="$(basename "$file")"
  local_size="$(stat -c%s "$file")"
  for attempt in 1 2 3; do
    remote_size="$(gh api "repos/$GITHUB_REPOSITORY/releases/$REL_ID/assets" --jq ".[] | select(.name == \"$name\" and .state == \"uploaded\") | .size" 2>/dev/null | head -n1 || true)"
    if [[ "$remote_size" == "$local_size" ]]; then
      echo "asset already complete: $name"
      return 0
    fi
    ids="$(gh api "repos/$GITHUB_REPOSITORY/releases/$REL_ID/assets" --jq ".[] | select(.name == \"$name\") | .id" 2>/dev/null || true)"
    for id in $ids; do gh api --method DELETE "repos/$GITHUB_REPOSITORY/releases/assets/$id" >/dev/null || true; done
    echo "upload $name attempt $attempt"
    if timeout 480s curl --fail-with-body --show-error --silent \
      --connect-timeout 30 --max-time 450 \
      -X POST \
      -H "Authorization: Bearer $GH_TOKEN" \
      -H "Accept: application/vnd.github+json" \
      -H "X-GitHub-Api-Version: 2022-11-28" \
      -H "Content-Type: $ctype" \
      --data-binary "@$file" \
      -o "/tmp/upload-${name}.json" \
      "https://uploads.github.com/repos/$GITHUB_REPOSITORY/releases/$REL_ID/assets?name=$name"; then
      remote_size="$(gh api "repos/$GITHUB_REPOSITORY/releases/$REL_ID/assets" --jq ".[] | select(.name == \"$name\" and .state == \"uploaded\") | .size" | head -n1)"
      [[ "$remote_size" == "$local_size" ]] && return 0
    fi
    remote_size="$(gh api "repos/$GITHUB_REPOSITORY/releases/$REL_ID/assets" --jq ".[] | select(.name == \"$name\" and .state == \"uploaded\") | .size" 2>/dev/null | head -n1 || true)"
    [[ "$remote_size" == "$local_size" ]] && return 0
    sleep 5
  done
  echo "failed to upload $name" >&2
  return 1
}

upload_asset "$IMAGE" 'application/x-xz'
upload_asset "${IMAGE}.sha256" 'text/plain'
upload_asset dist/BUILD-INFO.txt 'text/plain'

LOCAL_SHA="$(sha256sum "$IMAGE" | awk '{print $1}')"
REMOTE_DIGEST="$(gh api "repos/$GITHUB_REPOSITORY/releases/$REL_ID/assets" --jq ".[] | select(.name == \"$(basename "$IMAGE")\") | .digest" | head -n1)"
if [[ -n "$REMOTE_DIGEST" && "$REMOTE_DIGEST" != "null" ]]; then
  test "$REMOTE_DIGEST" = "sha256:$LOCAL_SHA"
fi

gh api --method PATCH "repos/$GITHUB_REPOSITORY/releases/$REL_ID" -F draft=false -F prerelease=true >/dev/null
gh api "repos/$GITHUB_REPOSITORY/releases/tags/$TAG" --jq '{tag:.tag_name,draft:.draft,prerelease:.prerelease,assets:[.assets[]|{name,size,digest,state}]}'
