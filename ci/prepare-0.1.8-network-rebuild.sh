#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-.}"
cd "$ROOT"

python3 - <<'PY'
from pathlib import Path
root=Path('.')

# Version milestone: network layer rebuilt for Raspberry Pi OS Trixie.
for rel in ['builder/build-image.sh','src/2pnyd/main.go']:
    p=root/rel
    s=p.read_text()
    s=s.replace('0.1.7-hotfix4','0.1.8-alpha').replace('Alpha 0.1.7 hotfix4','Alpha 0.1.8')
    p.write_text(s)
(root/'rootfs-overlay/etc/2pny/version').write_text('0.1.8-alpha\n')

# NetworkManager is the authority. Profiles are generated again inside the
# target Trixie image with that image's own nmcli --offline (NM 1.52.x).
b=root/'builder/build-image.sh'
s=b.read_text()
if '2PNY_NATIVE_NETWORK_PROFILES_V1' not in s:
    lines=s.splitlines()
    pos=None
    for i,line in enumerate(lines):
        if 'Habilitando serviços' in line:
            pos=i
            break
    if pos is None:
        raise SystemExit('build-image service-enable anchor not found')
    insert=r'''
# 2PNY_NATIVE_NETWORK_PROFILES_V1
# Build first-access profiles with the target image's own NetworkManager parser.
echo "[5b/9] Gerando perfis nativos NetworkManager para Trixie..."
chroot "$ROOT_MNT" apt-get install -y --no-install-recommends nftables >/dev/null
install -d -m 0700 "$ROOT_MNT/etc/NetworkManager/system-connections"
umask 077
chroot "$ROOT_MNT" nmcli --offline connection add \
  type wifi con-name 2PNY-SETUP ssid 2PNY-SETUP \
  802-11-wireless.mode ap \
  802-11-wireless.band bg \
  802-11-wireless.channel 6 \
  802-11-wireless.powersave 2 \
  802-11-wireless-security.key-mgmt none \
  802-11-wireless-security.auth-alg open \
  802-11-wireless-security.pmf disable \
  ipv4.method shared \
  ipv4.addresses 10.42.0.1/24 \
  ipv4.never-default yes \
  ipv6.method disabled \
  connection.autoconnect yes \
  connection.autoconnect-priority 100 \
  connection.autoconnect-retries 0 \
  connection.mdns 2 \
  > "$ROOT_MNT/etc/NetworkManager/system-connections/2pny-setup.nmconnection"

chroot "$ROOT_MNT" nmcli --offline connection add \
  type ethernet con-name 2PNY-Ethernet-Setup \
  ipv4.method shared \
  ipv4.addresses 10.43.0.1/24 \
  ipv4.never-default yes \
  ipv6.method disabled \
  connection.autoconnect yes \
  connection.autoconnect-priority 90 \
  connection.autoconnect-retries 0 \
  connection.mdns 2 \
  > "$ROOT_MNT/etc/NetworkManager/system-connections/2pny-ethernet-setup.nmconnection"

chmod 0600 "$ROOT_MNT/etc/NetworkManager/system-connections/2pny-setup.nmconnection" \
           "$ROOT_MNT/etc/NetworkManager/system-connections/2pny-ethernet-setup.nmconnection"
chown root:root "$ROOT_MNT/etc/NetworkManager/system-connections/2pny-setup.nmconnection" \
                "$ROOT_MNT/etc/NetworkManager/system-connections/2pny-ethernet-setup.nmconnection"

# This is an appliance; cloud-init must not overwrite first-access networking.
mkdir -p "$ROOT_MNT/etc/cloud"
touch "$ROOT_MNT/etc/cloud/cloud-init.disabled"
rm -f "$ROOT_MNT/var/lib/systemd/rfkill/"*:wlan* 2>/dev/null || true

# Explicit boot enablement: network availability cannot depend on an overlay
# symlink accidentally surviving image construction.
mkdir -p "$ROOT_MNT/etc/systemd/system/multi-user.target.wants"
ln -sfn /lib/systemd/system/NetworkManager.service \
  "$ROOT_MNT/etc/systemd/system/multi-user.target.wants/NetworkManager.service"
for u in 2pnyd 2pny-firstboot 2pny-setup-watch; do
  ln -sfn "/etc/systemd/system/${u}.service" \
    "$ROOT_MNT/etc/systemd/system/multi-user.target.wants/${u}.service"
done
'''.splitlines()
    lines[pos:pos]=insert
    s='\n'.join(lines)+'\n'
b.write_text(s)

# Set regulatory domain before NetworkManager tries AP mode. Trixie/modern
# cfg80211 may otherwise refuse AP initiation while still in world domain.
reg=root/'rootfs-overlay/usr/local/sbin/2pny-regdom'
reg.write_text(r'''#!/bin/bash
set -u
rfkill unblock wifi >/dev/null 2>&1 || true
/usr/sbin/iw reg set BR >/dev/null 2>&1 || true
exit 0
''')
regsvc=root/'rootfs-overlay/etc/systemd/system/2pny-regdom.service'
regsvc.write_text('''[Unit]\nDescription=2PNY Wi-Fi regulatory domain\nDefaultDependencies=no\nAfter=systemd-udev-trigger.service\nBefore=NetworkManager.service\n\n[Service]\nType=oneshot\nExecStart=/usr/local/sbin/2pny-regdom\nRemainAfterExit=yes\n''')
drop=root/'rootfs-overlay/etc/systemd/system/NetworkManager.service.d'
drop.mkdir(parents=True,exist_ok=True)
(drop/'10-2pny-regdom.conf').write_text('''[Unit]\nWants=2pny-regdom.service\nAfter=2pny-regdom.service\n''')

# AP control now changes NetworkManager autoconnect too, otherwise NetworkManager
# would immediately resurrect an AP that the user explicitly disabled.
apctl=root/'rootfs-overlay/usr/local/sbin/2pny-ap-control'
apctl.write_text(r'''#!/bin/bash
set -u
ACTION="${1:-status}"
AP=2PNY-SETUP
MARKER=/var/lib/2pny/ap-disabled
active(){ nmcli -t -f NAME connection show --active 2>/dev/null | grep -Fxq "$1"; }
case "$ACTION" in
  status)
    active "$AP" && echo active || echo inactive
    ;;
  on)
    mkdir -p /var/lib/2pny
    rm -f "$MARKER"
    rfkill unblock wifi >/dev/null 2>&1 || true
    nmcli networking on >/dev/null 2>&1 || true
    nmcli radio wifi on >/dev/null 2>&1 || true
    nmcli connection modify "$AP" connection.autoconnect yes connection.autoconnect-retries 0 >/dev/null 2>&1 || true
    nmcli --wait 20 connection up "$AP" >/dev/null 2>&1 || exit 1
    echo 'AP 2PNY-SETUP ativo'
    ;;
  off)
    mkdir -p /var/lib/2pny
    touch "$MARKER"
    nmcli connection modify "$AP" connection.autoconnect no >/dev/null 2>&1 || true
    nmcli connection down "$AP" >/dev/null 2>&1 || true
    echo 'AP 2PNY-SETUP desativado'
    ;;
  *) echo 'uso: 2pny-ap-control status|on|off' >&2; exit 2;;
esac
''')

# Watcher is now only recovery/diagnostics. NetworkManager itself owns boot
# activation through autoconnect profiles, so watcher failure cannot remove access.
watch=root/'rootfs-overlay/usr/local/sbin/2pny-setup-watch'
watch.write_text(r'''#!/bin/bash
set -u
STATE=/var/lib/2pny
AP=2PNY-SETUP
ETH=2PNY-Ethernet-Setup
MARKER="$STATE/ap-disabled"
DIAG=/boot/firmware/2PNY-NETWORK.txt
mkdir -p "$STATE"
log(){ logger -t 2pny-setup-watch -- "$*" 2>/dev/null || true; }
active(){ nmcli -t -f NAME connection show --active 2>/dev/null | grep -Fxq "$1"; }
write_diag(){
  {
    echo '2PNY OS 0.1.8-alpha - NETWORK'
    echo "time=$(date -Is)"
    echo '[radio]'
    nmcli radio 2>&1 || true
    echo '[devices]'
    nmcli -t -f DEVICE,TYPE,STATE,CONNECTION device status 2>&1 || true
    echo '[active]'
    nmcli -t -f NAME,TYPE,DEVICE connection show --active 2>&1 || true
    echo '[ipv4]'
    ip -4 -br address show 2>&1 || true
    echo '[rfkill]'
    rfkill list 2>&1 || true
    echo '[regdom]'
    iw reg get 2>&1 || true
  } >"${DIAG}.tmp" 2>/dev/null || true
  mv -f "${DIAG}.tmp" "$DIAG" 2>/dev/null || true
}

while [[ ! -f "$STATE/provisioned" ]]; do
  nmcli networking on >/dev/null 2>&1 || true
  nmcli connection modify "$ETH" connection.autoconnect yes connection.autoconnect-retries 0 >/dev/null 2>&1 || true

  if [[ -f "$MARKER" ]]; then
    nmcli connection modify "$AP" connection.autoconnect no >/dev/null 2>&1 || true
    active "$AP" && nmcli connection down "$AP" >/dev/null 2>&1 || true
  else
    rfkill unblock wifi >/dev/null 2>&1 || true
    nmcli radio wifi on >/dev/null 2>&1 || true
    nmcli connection modify "$AP" connection.autoconnect yes connection.autoconnect-retries 0 >/dev/null 2>&1 || true
    if ! active "$AP"; then
      if ! nmcli --wait 20 connection up "$AP" >/dev/null 2>&1; then
        log 'AP activation failed; NetworkManager will retry automatically'
      fi
    fi
  fi

  # Ethernet shared profile autoconnects when carrier appears. Explicit retry is
  # cheap and covers drivers that announce carrier after NetworkManager boot.
  if ! active "$ETH"; then
    for c in /sys/class/net/*/carrier; do
      [[ -r "$c" ]] || continue
      dev="$(basename "$(dirname "$c")")"
      [[ "$dev" == lo || "$dev" == wlan* ]] && continue
      if [[ "$(cat "$c" 2>/dev/null || echo 0)" == 1 ]]; then
        nmcli --wait 10 connection up "$ETH" ifname "$dev" >/dev/null 2>&1 || true
        break
      fi
    done
  fi

  write_diag
  [[ "${2PNY_WATCH_ONCE:-0}" == 1 ]] && exit 0
  sleep 10
done
write_diag
exit 0
''')

svc=root/'rootfs-overlay/etc/systemd/system/2pny-setup-watch.service'
svc.write_text('''[Unit]\nDescription=2PNY first-access network recovery and diagnostics\nAfter=NetworkManager.service\nWants=NetworkManager.service\nConditionPathExists=!/var/lib/2pny/provisioned\nStartLimitIntervalSec=0\n\n[Service]\nType=simple\nExecStart=/usr/local/sbin/2pny-setup-watch\nRestart=always\nRestartSec=5\nNoNewPrivileges=yes\nPrivateTmp=yes\nMemoryMax=96M\nTasksMax=64\n\n[Install]\nWantedBy=multi-user.target\n''')

# Firstboot explicitly reloads the profiles and attempts AP immediately, but exits
# successfully even when hardware is slow: native autoconnect + watcher continue.
fb=root/'rootfs-overlay/usr/local/sbin/2pny-firstboot'
fb.write_text(r'''#!/bin/bash
set -u
STATE=/var/lib/2pny
STATUS=/boot/firmware/2PNY-STATUS.txt
mkdir -p "$STATE"
status(){
  {
    echo '2PNY OS 0.1.8-alpha'
    echo "stage=$1"
    echo "time=$(date -Is)"
    nmcli -t -f DEVICE,TYPE,STATE,CONNECTION device status 2>&1 || true
    ip -4 -br address show 2>&1 || true
  } >"${STATUS}.tmp" 2>/dev/null || true
  mv -f "${STATUS}.tmp" "$STATUS" 2>/dev/null || true
}
hostnamectl set-hostname 2pny >/dev/null 2>&1 || true
/usr/local/sbin/2pny-regdom >/dev/null 2>&1 || true
systemctl start NetworkManager.service >/dev/null 2>&1 || true
systemctl start avahi-daemon.service >/dev/null 2>&1 || true
systemctl start 2pnyd.service >/dev/null 2>&1 || true
if [[ -f "$STATE/provisioned" ]]; then status provisioned; exit 0; fi
nmcli networking on >/dev/null 2>&1 || true
nmcli radio wifi on >/dev/null 2>&1 || true
nmcli connection reload >/dev/null 2>&1 || true
nmcli connection modify 2PNY-SETUP connection.autoconnect yes connection.autoconnect-retries 0 >/dev/null 2>&1 || true
nmcli connection modify 2PNY-Ethernet-Setup connection.autoconnect yes connection.autoconnect-retries 0 >/dev/null 2>&1 || true
nmcli --wait 20 connection up 2PNY-SETUP >/dev/null 2>&1 || true
systemctl start 2pny-setup-watch.service >/dev/null 2>&1 || true
status network-started
exit 0
''')

# Source contract: no boot networking may depend exclusively on the watcher.
v=root/'builder/validate-source.sh'
vs=v.read_text().replace('0.1.7-hotfix4','0.1.8-alpha')
if '# 2PNY_0_1_8_NATIVE_NETWORK' not in vs:
    vs += r'''
# 2PNY_0_1_8_NATIVE_NETWORK
echo "[2PNY] Validate Trixie native NetworkManager first access"
grep -q '2PNY_NATIVE_NETWORK_PROFILES_V1' builder/build-image.sh
grep -q '802-11-wireless-security.pmf disable' builder/build-image.sh
grep -q 'connection.autoconnect yes' builder/build-image.sh
grep -q 'connection.autoconnect-retries 0' builder/build-image.sh
grep -q '10.42.0.1/24' builder/build-image.sh
grep -q '10.43.0.1/24' builder/build-image.sh
grep -q 'cloud-init.disabled' builder/build-image.sh
grep -q 'MemoryMax=96M' rootfs-overlay/etc/systemd/system/2pny-setup-watch.service
grep -q 'NetworkManager will retry automatically' rootfs-overlay/usr/local/sbin/2pny-setup-watch
grep -q '2PNY-NETWORK.txt' rootfs-overlay/usr/local/sbin/2pny-setup-watch
grep -q 'connection.autoconnect no' rootfs-overlay/usr/local/sbin/2pny-ap-control
grep -q '0.1.8-alpha' src/2pnyd/main.go
bash -n rootfs-overlay/usr/local/sbin/2pny-regdom
bash -n rootfs-overlay/usr/local/sbin/2pny-firstboot
bash -n rootfs-overlay/usr/local/sbin/2pny-setup-watch
bash -n rootfs-overlay/usr/local/sbin/2pny-ap-control
'''
v.write_text(vs)
PY

chmod 0755 \
  rootfs-overlay/usr/local/sbin/2pny-regdom \
  rootfs-overlay/usr/local/sbin/2pny-firstboot \
  rootfs-overlay/usr/local/sbin/2pny-setup-watch \
  rootfs-overlay/usr/local/sbin/2pny-ap-control

bash -n rootfs-overlay/usr/local/sbin/2pny-regdom
bash -n rootfs-overlay/usr/local/sbin/2pny-firstboot
bash -n rootfs-overlay/usr/local/sbin/2pny-setup-watch
bash -n rootfs-overlay/usr/local/sbin/2pny-ap-control

echo '2PNY 0.1.8 native Trixie networking applied'
