#!/usr/bin/env bash
set -euo pipefail

ARCH="${1:-}"
OUT_DIR="${2:-$PWD/out}"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
[[ "$ARCH" == "arm32" || "$ARCH" == "arm64" ]] || { echo "usage: $0 arm32|arm64 [out-dir]" >&2; exit 2; }
mkdir -p "$OUT_DIR"
OUT_DIR="$(realpath "$OUT_DIR")"

PI32_SHA='59b67461533c2eef3564bc48eb3ce5c16e5c62ee'
PI64_SHA='d346cd53562b3c6b4f94c9155175f814258c456d'
MMDVM_SHA='a819ae64edd5de5a7468b24e47d673a53f94fc9f'
DMRGW_SHA='ad172eae396fed562e14c92375d63479e9fe689a'
DONOR_ARM32_SHA='97ce1886567288cca361d21c63a14e78ae0ffe20cff2eafeb3529b84c2e59ef2'
DONOR_ARM64_SHA='55402edeb87a748decc88f86092b15ebd0ed6bd45c59cdb40e9cf21c75117797'

if [[ "$ARCH" == arm32 ]]; then
  PI_SHA="$PI32_SHA"
  DONOR_SHA="$DONOR_ARM32_SHA"
  DONOR_NAME='PU2PNY-OS-5.00.000-arm32.img.xz'
else
  PI_SHA="$PI64_SHA"
  DONOR_SHA="$DONOR_ARM64_SHA"
  DONOR_NAME='PU2PNY-OS-5.00.000-arm64.img.xz'
fi
DONOR_URL="https://github.com/PU2PNY/2PNY-OS/releases/download/v5.00.000/${DONOR_NAME}"
WORK="$(mktemp -d -p "${RUNNER_TEMP:-/tmp}" pu2pny-500001-${ARCH}.XXXXXX)"
cleanup(){
  set +e
  if [[ -n "${DONOR_MNT:-}" ]]; then sudo umount "$DONOR_MNT" 2>/dev/null || true; fi
  if [[ -n "${DONOR_LOOP:-}" ]]; then sudo losetup -d "$DONOR_LOOP" 2>/dev/null || true; fi
  rm -rf "$WORK"
}
trap cleanup EXIT

PI="$WORK/pi-gen"
git clone --filter=blob:none https://github.com/RPi-Distro/pi-gen.git "$PI"
git -C "$PI" checkout --detach "$PI_SHA"
[[ "$(git -C "$PI" rev-parse HEAD)" == "$PI_SHA" ]]

# Payload donor: application/UI only. The donor root filesystem is never used as OS base.
DONOR_XZ="$WORK/$DONOR_NAME"
curl -fL --retry 4 --retry-delay 3 "$DONOR_URL" -o "$DONOR_XZ"
echo "$DONOR_SHA  $DONOR_XZ" | sha256sum -c -
xz -t "$DONOR_XZ"
xz -dc "$DONOR_XZ" > "$WORK/donor.img"
DONOR_LOOP="$(sudo losetup --find --show --partscan "$WORK/donor.img")"
DONOR_MNT="$WORK/donor-root"
mkdir -p "$DONOR_MNT"
sudo mount "${DONOR_LOOP}p2" "$DONOR_MNT"

STAGE="$PI/stage2"
sudo rm -rf "$STAGE"
mkdir -p "$STAGE/00-pu2pny/files/rootfs" "$STAGE/00-pu2pny/files/build"
cat > "$STAGE/prerun.sh" <<'EOF'
#!/bin/bash -e
if [ ! -d "${ROOTFS_DIR}" ]; then copy_previous; fi
EOF
chmod +x "$STAGE/prerun.sh"
# pi-gen sources EXPORT_IMAGE as shell. Keep no suffix so release names stay canonical.
cat > "$STAGE/EXPORT_IMAGE" <<'EOF'
IMG_SUFFIX=""
if [ "${USE_QEMU}" = "1" ]; then
  export IMG_SUFFIX="${IMG_SUFFIX}-qemu"
fi
EOF

ROOTPAY="$STAGE/00-pu2pny/files/rootfs"
# Copy only application payload. No donor /usr/lib, /lib, /boot, package DB or kernel is inherited.
for p in usr/share/2pny etc/2pny; do
  if sudo test -e "$DONOR_MNT/$p"; then
    sudo mkdir -p "$ROOTPAY/$(dirname "$p")"
    sudo cp -a "$DONOR_MNT/$p" "$ROOTPAY/$p"
  fi
done
sudo mkdir -p "$ROOTPAY/usr/local/sbin" "$ROOTPAY/etc/systemd/system" "$ROOTPAY/etc"
while IFS= read -r -d '' f; do sudo cp -a "$f" "$ROOTPAY/usr/local/sbin/"; done < <(sudo find "$DONOR_MNT/usr/local/sbin" -maxdepth 1 -type f -name '2pny-*' -print0 2>/dev/null || true)
while IFS= read -r -d '' f; do sudo cp -a "$f" "$ROOTPAY/etc/systemd/system/"; done < <(sudo find "$DONOR_MNT/etc/systemd/system" -maxdepth 1 \( -type f -o -type l \) -name '2pny-*.service' -print0 2>/dev/null || true)
for cfg in etc/MMDVMHost.ini etc/DMRGateway.ini; do
  if sudo test -f "$DONOR_MNT/$cfg"; then sudo cp -a "$DONOR_MNT/$cfg" "$ROOTPAY/$cfg"; fi
done
sudo chown -R "$(id -u):$(id -g)" "$STAGE/00-pu2pny/files"
sudo umount "$DONOR_MNT"; DONOR_MNT=''
sudo losetup -d "$DONOR_LOOP"; DONOR_LOOP=''
rm -f "$WORK/donor.img"

# Source-controlled 5.x runtime and backend source.
mkdir -p "$ROOTPAY/usr/local/libexec/pu2pny" "$ROOTPAY/usr/local/sbin" "$ROOTPAY/etc/2pny"
install -m 0755 "$REPO_ROOT/runtime/5x/2pny-eventd.py" "$ROOTPAY/usr/local/libexec/pu2pny/2pny-eventd"
install -m 0755 "$REPO_ROOT/runtime/5x/2pny-hardware-manager.py" "$ROOTPAY/usr/local/libexec/pu2pny/2pny-hardware-manager"
install -m 0755 "$REPO_ROOT/runtime/5x/2pny-network-manager.py" "$ROOTPAY/usr/local/libexec/pu2pny/2pny-network-manager"
install -m 0755 "$REPO_ROOT/runtime/5x/2pny-wifi-apply.py" "$ROOTPAY/usr/local/sbin/2pny-wifi-apply"
install -m 0755 "$REPO_ROOT/runtime/5x/2pny-protocol-manager.py" "$ROOTPAY/usr/local/sbin/2pny-protocol-manager"
cp "$REPO_ROOT/src/2pnyd-main-0.3.27.go" "$STAGE/00-pu2pny/files/build/2pnyd.go"
printf '5.00.001\n' > "$ROOTPAY/etc/2pny/version"

cat > "$STAGE/00-pu2pny/00-packages" <<'EOF'
network-manager avahi-daemon python3-minimal iw rfkill iproute2 ca-certificates curl jq xz-utils libmosquitto1
EOF

cat > "$STAGE/00-pu2pny/01-run.sh" <<'EOF'
#!/bin/bash -e
rsync -a "${STAGE_DIR}/00-pu2pny/files/rootfs/" "${ROOTFS_DIR}/"
install -d "${ROOTFS_DIR}/opt/pu2pny-build"
install -m 0644 "${STAGE_DIR}/00-pu2pny/files/build/2pnyd.go" "${ROOTFS_DIR}/opt/pu2pny-build/2pnyd.go"
EOF
chmod +x "$STAGE/00-pu2pny/01-run.sh"

cat > "$STAGE/00-pu2pny/02-run-chroot.sh" <<EOF
#!/bin/bash -e
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install --no-install-recommends -y build-essential git libmosquitto-dev golang-go
rm -rf /tmp/MMDVM-Host /tmp/DMRGateway
git clone https://github.com/g4klx/MMDVM-Host.git /tmp/MMDVM-Host
git -C /tmp/MMDVM-Host checkout --detach '$MMDVM_SHA'
make -C /tmp/MMDVM-Host -j1
install -m 0755 /tmp/MMDVM-Host/MMDVM-Host /usr/local/bin/MMDVM-Host
git clone https://github.com/g4klx/DMRGateway.git /tmp/DMRGateway
git -C /tmp/DMRGateway checkout --detach '$DMRGW_SHA'
make -C /tmp/DMRGateway -j1
install -m 0755 /tmp/DMRGateway/DMRGateway /usr/local/bin/DMRGateway
sed -i 's/appVersion            = "0.3.27-alpha"/appVersion            = "5.00.001-alpha"/' /opt/pu2pny-build/2pnyd.go
CGO_ENABLED=0 go build -trimpath -ldflags='-s -w' -o /usr/local/bin/2pnyd /opt/pu2pny-build/2pnyd.go
rm -rf /opt/pu2pny-build /tmp/MMDVM-Host /tmp/DMRGateway
apt-get purge -y build-essential git libmosquitto-dev golang-go || true
apt-get autoremove --purge -y || true
apt-get clean
rm -rf /var/lib/apt/lists/* /var/cache/apt/* /tmp/*
mkdir -p /var/lib/2pny /run/pu2pny /etc/systemd/system
hostnamectl --static set-hostname pu2pny 2>/dev/null || echo pu2pny >/etc/hostname
if grep -qE '^#?host-name=' /etc/avahi/avahi-daemon.conf; then
  sed -i -E 's/^#?host-name=.*/host-name=pu2pny/' /etc/avahi/avahi-daemon.conf
else
  sed -i '/^\[server\]/a host-name=pu2pny' /etc/avahi/avahi-daemon.conf
fi
systemctl enable NetworkManager.service avahi-daemon.service 2>/dev/null || true
systemctl disable ssh.service 2>/dev/null || true
# The temporary pi-gen password is never a shipped credential.
if id pu2pny >/dev/null 2>&1; then passwd -l pu2pny; fi
# 5.x core services are regenerated here to avoid inheriting old service semantics.
cat >/etc/systemd/system/2pny-eventd.service <<'UNIT'
[Unit]
Description=PU2PNY-OS 5.x local event bus
After=local-fs.target
[Service]
Type=simple
ExecStart=/usr/local/libexec/pu2pny/2pny-eventd
Restart=on-failure
RestartSec=2
NoNewPrivileges=yes
PrivateTmp=yes
ProtectHome=yes
RuntimeDirectory=pu2pny
[Install]
WantedBy=multi-user.target
UNIT
cat >/etc/systemd/system/2pny-hardware-manager.service <<'UNIT'
[Unit]
Description=PU2PNY-OS 5.x conservative hardware inventory
After=local-fs.target
[Service]
Type=oneshot
ExecStart=/usr/local/libexec/pu2pny/2pny-hardware-manager
NoNewPrivileges=yes
PrivateTmp=yes
RuntimeDirectory=pu2pny
[Install]
WantedBy=multi-user.target
UNIT
cat >/etc/systemd/system/2pny-network-manager.service <<'UNIT'
[Unit]
Description=PU2PNY-OS 5.x event-driven network state
After=NetworkManager.service 2pny-eventd.service
Wants=NetworkManager.service 2pny-eventd.service
[Service]
Type=simple
ExecStart=/usr/local/libexec/pu2pny/2pny-network-manager
Restart=on-failure
RestartSec=3
NoNewPrivileges=yes
PrivateTmp=yes
RuntimeDirectory=pu2pny
[Install]
WantedBy=multi-user.target
UNIT
systemctl enable 2pny-eventd.service 2pny-hardware-manager.service 2pny-network-manager.service
# Keep one canonical RF engine. Existing known-good unit payload, if present, remains authoritative.
if [ -f /etc/systemd/system/2pny-mmdvmhost.service ] && [ ! -e /etc/systemd/system/mmdvmhost.service ]; then ln -s 2pny-mmdvmhost.service /etc/systemd/system/mmdvmhost.service; fi
# Dashboard is enabled only if its unit survived the application-payload import.
if [ -f /etc/systemd/system/2pny-dashboard.service ]; then systemctl enable 2pny-dashboard.service || true; fi
EOF
chmod +x "$STAGE/00-pu2pny/02-run-chroot.sh"

cat > "$PI/config" <<EOF
IMG_NAME='PU2PNY-OS-5.00.001-${ARCH}'
PI_GEN_RELEASE='PU2PNY-OS 5.00.001 Minimal'
RELEASE='trixie'
TARGET_HOSTNAME='pu2pny'
LOCALE_DEFAULT='pt_BR.UTF-8'
KEYBOARD_KEYMAP='br'
KEYBOARD_LAYOUT='Portuguese (Brazil)'
TIMEZONE_DEFAULT='America/Sao_Paulo'
ENABLE_SSH=0
DEPLOY_COMPRESSION='xz'
COMPRESSION_LEVEL=9
FIRST_USER_NAME='pu2pny'
DISABLE_FIRST_BOOT_USER_RENAME=1
WPA_COUNTRY='BR'
EOF
# pi-gen requires an initial value to create the account; stage2 locks it before export.
echo "FIRST_USER_PASS='PU2PNY-BUILD-ONLY'" >> "$PI/config"

# Skip all later Raspberry Pi OS stages. stage2 is our custom minimal appliance stage.
for d in stage3 stage4 stage5; do [[ -d "$PI/$d" ]] && touch "$PI/$d/SKIP"; done

cd "$PI"
sudo ./build.sh

IMG="$(find deploy -maxdepth 1 -type f -name 'PU2PNY-OS-5.00.001-*.img.xz' | head -n1)"
[[ -n "$IMG" && -s "$IMG" ]] || { echo 'minimal image missing' >&2; exit 3; }
xz -t "$IMG"
cp "$IMG" "$OUT_DIR/PU2PNY-OS-5.00.001-${ARCH}.img.xz"
sha256sum "$OUT_DIR/PU2PNY-OS-5.00.001-${ARCH}.img.xz" > "$OUT_DIR/PU2PNY-OS-5.00.001-${ARCH}.img.xz.sha256"
stat -c '%n %s bytes' "$OUT_DIR/PU2PNY-OS-5.00.001-${ARCH}.img.xz"
cat "$OUT_DIR/PU2PNY-OS-5.00.001-${ARCH}.img.xz.sha256"
echo BUILD_500001_MINIMAL_OK
