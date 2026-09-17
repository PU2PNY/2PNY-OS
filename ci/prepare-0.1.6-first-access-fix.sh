#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-.}"
cd "$ROOT"

python3 - <<'PY'
from pathlib import Path
import os
import re
root = Path('.')

# ---------------------------------------------------------------------------
# 1) Fix the MMDVMHost build on Trixie. The earlier build removed apt indexes
# before the second package install, so git/libmosquitto-dev were invisible.
# ---------------------------------------------------------------------------
p = root/'builder/build-image.sh'
s = p.read_text()
needle = 'echo "[4b/9] Compilando MMDVMHost nativo (${MMDVMHOST_COMMIT:0:12})..."\nchroot "$ROOT_MNT" env DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends g++ make git libmosquitto-dev'
replacement = 'echo "[4b/9] Compilando MMDVMHost nativo (${MMDVMHOST_COMMIT:0:12})..."\nchroot "$ROOT_MNT" env DEBIAN_FRONTEND=noninteractive apt-get update\nchroot "$ROOT_MNT" env DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends g++ make git libmosquitto-dev'
if needle in s:
    s = s.replace(needle, replacement, 1)
p.write_text(s)

# ---------------------------------------------------------------------------
# 2) Deterministic first-access networking.
#    - Wi-Fi setup AP: 10.42.0.1/24
#    - Direct Ethernet with no upstream DHCP: 10.42.0.1/24
#    - Ethernet connected to a router: normal DHCP, while setup AP remains up.
#    We never run two 10.42.0.1 interfaces simultaneously.
# ---------------------------------------------------------------------------
conn = root/'rootfs-overlay/etc/NetworkManager/system-connections'
conn.mkdir(parents=True, exist_ok=True)
(conn/'2pny-ethernet.nmconnection').write_text('''[connection]\nid=2PNY-Ethernet\nuuid=7ec42a49-a77d-49f7-a181-2a4f00000001\ntype=ethernet\nautoconnect=true\nautoconnect-priority=20\nmdns=2\n\n[ethernet]\n\n[ipv4]\nmethod=auto\ndhcp-timeout=6\nmay-fail=true\n\n[ipv6]\nmethod=auto\naddr-gen-mode=default\n\n[proxy]\n''')
(conn/'2pny-ethernet-setup.nmconnection').write_text('''[connection]\nid=2PNY-Ethernet-Setup\nuuid=7ec42a49-a77d-49f7-a181-2a4f00000003\ntype=ethernet\nautoconnect=false\nmdns=2\n\n[ethernet]\n\n[ipv4]\nmethod=shared\naddress1=10.42.0.1/24\n\n[ipv6]\nmethod=disabled\n\n[proxy]\n''')
(conn/'2pny-setup.nmconnection').write_text('''[connection]\nid=2PNY-SETUP\nuuid=5d9da2d9-3b48-4936-8201-2a4f00000002\ntype=wifi\nautoconnect=false\nautoconnect-priority=100\nmdns=2\n\n[wifi]\nmode=ap\nband=bg\nchannel=6\nssid=2PNY-SETUP\n\n[wifi-security]\nkey-mgmt=wpa-psk\npsk=2pnysetup\n\n[ipv4]\nmethod=shared\naddress1=10.42.0.1/24\n\n[ipv6]\nmethod=disabled\n\n[proxy]\n''')

# Appliance image: cloud-init must not rewrite network state on first boot.
cloud = root/'rootfs-overlay/etc/cloud'
cloud.mkdir(parents=True, exist_ok=True)
(cloud/'cloud-init.disabled').write_text('2PNY appliance image: provisioning is owned by 2PNY OS.\n')

# Avahi is convenience only, never a dependency of the setup flow.
avahi = root/'rootfs-overlay/etc/avahi'
avahi.mkdir(parents=True, exist_ok=True)
(avahi/'avahi-daemon.conf').write_text('''[server]\nuse-ipv4=yes\nuse-ipv6=yes\nratelimit-interval-usec=1000000\nratelimit-burst=1000\n\n[publish]\npublish-addresses=yes\npublish-workstation=yes\npublish-hinfo=no\npublish-domain=no\n''')
services = avahi/'services'
services.mkdir(parents=True, exist_ok=True)
(services/'2pny-http.service').write_text('''<?xml version="1.0" standalone='no'?><!--*-nxml-*-->\n<!DOCTYPE service-group SYSTEM "avahi-service.dtd">\n<service-group>\n  <name replace-wildcards="yes">2PNY OS on %h</name>\n  <service>\n    <type>_http._tcp</type>\n    <port>80</port>\n    <txt-record>path=/</txt-record>\n  </service>\n</service-group>\n''')

# Reduce SD writes. Diagnostics stay in RAM; a tiny boot-status file is written
# only at state transitions for field recovery without SSH.
jd = root/'rootfs-overlay/etc/systemd/journald.conf.d'
jd.mkdir(parents=True, exist_ok=True)
(jd/'2pny.conf').write_text('''[Journal]\nStorage=volatile\nRuntimeMaxUse=16M\nRuntimeMaxFileSize=4M\nRateLimitIntervalSec=30s\nRateLimitBurst=500\n''')

# 2pnyd must be available before the setup network appears and must not wait for
# network-online/DHCP. It serves on all interfaces through :80.
svcdir = root/'rootfs-overlay/etc/systemd/system'
svcdir.mkdir(parents=True, exist_ok=True)
(svcdir/'2pnyd.service').write_text('''[Unit]\nDescription=2PNY Core and local web panel\nAfter=local-fs.target NetworkManager.service\nWants=NetworkManager.service\nBefore=2pny-firstboot.service\nStartLimitIntervalSec=0\n\n[Service]\nType=simple\nExecStart=/usr/local/bin/2pnyd\nRestart=always\nRestartSec=1\nNoNewPrivileges=yes\nPrivateTmp=yes\nProtectHome=yes\nProtectSystem=strict\nReadWritePaths=/var/lib/2pny /run\nMemoryMax=64M\nTasksMax=64\n\n[Install]\nWantedBy=multi-user.target\n''')
(svcdir/'2pny-firstboot.service').write_text('''[Unit]\nDescription=2PNY deterministic first-access provisioning\nAfter=NetworkManager.service 2pnyd.service\nWants=NetworkManager.service 2pnyd.service\nConditionPathExists=!/var/lib/2pny/provisioned\nStartLimitIntervalSec=0\n\n[Service]\nType=oneshot\nExecStart=/usr/local/sbin/2pny-firstboot\nRemainAfterExit=yes\nRestart=on-failure\nRestartSec=2\nTimeoutStartSec=60\n\n[Install]\nWantedBy=multi-user.target\n''')

# Explicit enablement/masking in the overlay. This avoids depending on chroot
# enablement side effects during image construction.
def symlink(path, target):
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        path.unlink()
    except FileNotFoundError:
        pass
    path.symlink_to(target)

wants = svcdir/'multi-user.target.wants'
symlink(wants/'2pnyd.service', '/etc/systemd/system/2pnyd.service')
symlink(wants/'2pny-firstboot.service', '/etc/systemd/system/2pny-firstboot.service')
symlink(wants/'NetworkManager.service', '/usr/lib/systemd/system/NetworkManager.service')
symlink(wants/'avahi-daemon.service', '/usr/lib/systemd/system/avahi-daemon.service')
symlink(svcdir/'NetworkManager-wait-online.service', '/dev/null')

# Rewrite first boot as an explicit state machine. Direct Ethernet only becomes
# a DHCP server when no upstream DHCP server was found, preventing DHCP leakage
# onto a normal LAN.
fb = root/'rootfs-overlay/usr/local/sbin/2pny-firstboot'
fb.write_text(r'''#!/bin/bash
set -u
STATE=/var/lib/2pny
LOG=/run/2pny-firstboot.log
STATUS=/boot/firmware/2PNY-STATUS.txt
mkdir -p "$STATE"
exec >>"$LOG" 2>&1

status_write() {
  local stage="$1"
  {
    echo "2PNY OS 0.1.6-alpha"
    echo "stage=${stage}"
    echo "time=$(date -Is)"
    echo "hostname=$(hostname)"
    echo "provisioned=$([[ -f "$STATE/provisioned" ]] && echo yes || echo no)"
    echo
    echo "[connections]"
    nmcli -t -f NAME,TYPE,DEVICE connection show --active 2>/dev/null || true
    echo
    echo "[ipv4]"
    ip -4 -br address show 2>/dev/null || true
  } >"${STATUS}.tmp" 2>/dev/null || true
  mv -f "${STATUS}.tmp" "$STATUS" 2>/dev/null || true
}

echo "[$(date -Is)] 2PNY deterministic first boot"
hostnamectl set-hostname 2pny 2>/dev/null || true
systemctl start NetworkManager.service 2>/dev/null || true
systemctl start 2pnyd.service 2>/dev/null || true
systemctl start avahi-daemon.service 2>/dev/null || true
status_write starting

if [[ -f "$STATE/provisioned" ]]; then
  nmcli connection down 2PNY-SETUP >/dev/null 2>&1 || true
  nmcli connection down 2PNY-Ethernet-Setup >/dev/null 2>&1 || true
  nmcli --wait 6 connection up 2PNY-Ethernet >/dev/null 2>&1 || true
  status_write provisioned
  exit 0
fi

raspi-config nonint do_wifi_country BR 2>/dev/null || iw reg set BR 2>/dev/null || true
for f in /var/lib/systemd/rfkill/*:wlan; do [[ -e "$f" ]] && echo 0 >"$f" 2>/dev/null || true; done
rfkill unblock wifi 2>/dev/null || true
nmcli radio wifi on 2>/dev/null || true

# Interfaces normally appear almost immediately; cap the wait at 10 seconds.
for _ in {1..20}; do
  nmcli -t -f DEVICE,TYPE device status >/dev/null 2>&1 && break
  sleep .5
done

ETH_IF="$(nmcli -t -f DEVICE,TYPE device status 2>/dev/null | awk -F: '$2=="ethernet"{print $1;exit}')"
WIFI_IF="$(nmcli -t -f DEVICE,TYPE device status 2>/dev/null | awk -F: '$2=="wifi"{print $1;exit}')"
SETUP_MODE=""
LAN_ADDR=""

# If Ethernet has carrier, first try normal DHCP for a router-connected cable.
# Only if that fails do we turn Ethernet into the 10.42.0.1 setup network.
if [[ -n "${ETH_IF:-}" && "$(cat "/sys/class/net/${ETH_IF}/carrier" 2>/dev/null || echo 0)" == "1" ]]; then
  nmcli connection down 2PNY-Ethernet-Setup >/dev/null 2>&1 || true
  nmcli --wait 6 connection up 2PNY-Ethernet ifname "$ETH_IF" >/dev/null 2>&1 || true
  LAN_ADDR="$(nmcli -g IP4.ADDRESS device show "$ETH_IF" 2>/dev/null | head -n1 | cut -d/ -f1)"
  if [[ -z "$LAN_ADDR" || "$LAN_ADDR" == 169.254.* ]]; then
    nmcli connection down 2PNY-Ethernet >/dev/null 2>&1 || true
    if nmcli --wait 6 connection up 2PNY-Ethernet-Setup ifname "$ETH_IF" >/dev/null 2>&1; then
      SETUP_MODE="ethernet"
      echo "Direct Ethernet setup active: http://10.42.0.1"
    fi
  fi
fi

# Wi-Fi setup is the default path. Never start it while direct Ethernet owns
# 10.42.0.1, avoiding duplicate-address/subnet ambiguity.
if [[ "$SETUP_MODE" != "ethernet" && -n "${WIFI_IF:-}" ]]; then
  ip link set "$WIFI_IF" up 2>/dev/null || true
  rfkill unblock wifi 2>/dev/null || true
  nmcli radio wifi on 2>/dev/null || true
  if nmcli --wait 6 connection up 2PNY-SETUP ifname "$WIFI_IF" >/dev/null 2>&1; then
    SETUP_MODE="wifi"
  else
    # One clean fallback recreation; no long retry loops.
    nmcli connection delete 2PNY-SETUP >/dev/null 2>&1 || true
    if nmcli --wait 8 device wifi hotspot ifname "$WIFI_IF" con-name 2PNY-SETUP ssid 2PNY-SETUP band bg channel 6 password 2pnysetup >/dev/null 2>&1; then
      nmcli connection modify 2PNY-SETUP ipv4.method shared ipv4.addresses 10.42.0.1/24 ipv6.method disabled connection.autoconnect no connection.mdns yes >/dev/null 2>&1 || true
      SETUP_MODE="wifi"
    fi
  fi
fi

# If Wi-Fi is unavailable and a direct Ethernet cable appeared late, use the
# same 10.42.0.1 setup address as a final recovery path.
if [[ -z "$SETUP_MODE" && -n "${ETH_IF:-}" && "$(cat "/sys/class/net/${ETH_IF}/carrier" 2>/dev/null || echo 0)" == "1" ]]; then
  nmcli connection down 2PNY-Ethernet >/dev/null 2>&1 || true
  if nmcli --wait 6 connection up 2PNY-Ethernet-Setup ifname "$ETH_IF" >/dev/null 2>&1; then
    SETUP_MODE="ethernet"
  fi
fi

systemctl restart avahi-daemon.service 2>/dev/null || true
systemctl restart 2pnyd.service 2>/dev/null || true
sleep .4
status_write "ready-${SETUP_MODE:-lan}"

if [[ "$SETUP_MODE" == "wifi" ]]; then
  echo "2PNY-SETUP ready: SSID=2PNY-SETUP http://10.42.0.1"
elif [[ "$SETUP_MODE" == "ethernet" ]]; then
  echo "Direct Ethernet setup ready: http://10.42.0.1"
elif [[ -n "$LAN_ADDR" ]]; then
  echo "Router Ethernet available before provisioning: http://${LAN_ADDR}"
else
  echo "No setup path became reachable; systemd will retry."
  exit 1
fi
exit 0
''')

# ---------------------------------------------------------------------------
# 3) Browser flow: no absolute mDNS redirect, no blank-page transition.
# ---------------------------------------------------------------------------
p = root/'src/2pnyd/main.go'
s = p.read_text()
for old in [
    'http://2pny.local/wizard',
    'http://2pny.local/',
    'http://2pny.local',
]:
    s = s.replace(old, '/wizard')
s = s.replace('"next":"/wizard/wizard"', '"next":"/wizard"')
s = s.replace('"next": "/wizard/wizard"', '"next": "/wizard"')

# Explicitly reject loopback-only HTTP binding if it ever appears in the base.
s = s.replace('127.0.0.1:80', ':80').replace('localhost:80', ':80')

# mDNS is optional convenience only; status polling remains on the current host.
s = s.replace("let u=['/api/setup-status','/wizardapi/setup-status'];", "let u=['/api/setup-status'];")
s = s.replace("let u=['/api/setup-status','http://2pny.local/api/setup-status'];", "let u=['/api/setup-status'];")

# When Wi-Fi setup is being torn down, keep the rendered page stable instead of
# navigating to a hostname that may not yet resolve. On an already-routed LAN,
# relative /wizard is safe.
pat = re.compile(r"async function watchSetup\(\)\{.*?\}\\nasync function save\(\)", re.S)
if pat.search(s):
    js = r'''async function watchSetup(){let m=document.getElementById('msg'),deadline=Date.now()+30000,miss=0;while(Date.now()<deadline){let st=await probeSetup();if(st&&st.state==='connected'){m.className='ok';if(location.hostname==='10.42.0.1'){m.innerHTML='<b>✓ Rede configurada.</b><br>O 2PNY-SETUP será desligado. Reconecte este dispositivo à sua rede normal e abra o IP recebido pelo 2PNY.<br><small>2pny.local é apenas uma conveniência opcional.</small>';return}m.innerHTML='<b>✓ Conectado.</b><br>Abrindo a próxima etapa...';await waitms(500);window.location.href='/wizard';return}if(st&&st.state==='error'){m.className='err';m.innerHTML='<b>Não conectou.</b><br>'+st.message+'<br><br>O acesso de configuração será restaurado em <b>10.42.0.1</b>.';return}if(!st){miss++;if(miss>=3){m.className='ok';m.innerHTML='<b>Configuração salva.</b><br>A rede de configuração foi encerrada. Reconecte este dispositivo à rede normal e abra o IP do 2PNY.';return}}else{miss=0;m.className='ok';m.innerHTML='<b>Conectando...</b><br>'+(st.message||'Aguardando a nova rede...')+'<br><small>Não feche esta tela até a rede mudar.</small>'}await waitms(900)}m.className='ok';m.innerHTML='<b>Configuração salva.</b><br>Reconecte à sua rede normal e abra o IP recebido pelo 2PNY.'}
async function save()'''
    s = pat.sub(js, s, count=1)

# Do not recreate the Wi-Fi AP if direct Ethernet setup currently owns
# 10.42.0.1. That would create duplicate addresses on two interfaces.
anchor = 'func restoreSetupAP(iface string) {\n'
if anchor in s and '2PNY-Ethernet-Setup' not in s[s.find(anchor):s.find(anchor)+500]:
    guard = anchor + '\tb, _ := exec.Command("nmcli", "-t", "-f", "NAME", "connection", "show", "--active").Output()\n\tif strings.Contains(string(b), "2PNY-Ethernet-Setup") { return }\n'
    s = s.replace(anchor, guard, 1)

# After provisioning, setup-only links are removed and normal Ethernet returns
# to DHCP. Replace the existing Avahi-only finalization once, then add helper.
if 'func finishProvisionedNetwork()' not in s:
    old = 'exec.Command("systemctl","restart","avahi-daemon.service").Run()'
    if old in s:
        s = s.replace(old, 'finishProvisionedNetwork()', 1)
    helper_anchor = 'func connectConfiguredWiFi(ssid,password string) error {'
    helper = '''func finishProvisionedNetwork() {\n\texec.Command("nmcli", "connection", "down", "2PNY-SETUP").Run()\n\texec.Command("nmcli", "connection", "down", "2PNY-Ethernet-Setup").Run()\n\texec.Command("nmcli", "--wait", "8", "connection", "up", "2PNY-Ethernet").Run()\n\texec.Command("systemctl", "restart", "avahi-daemon.service").Run()\n}\n\n'''
    if helper_anchor in s:
        s = s.replace(helper_anchor, helper + helper_anchor, 1)

# Give the POST response time to render before the AP is intentionally dropped.
s = s.replace('time.Sleep(4*time.Second); writeSetupState("connecting","Conectando ao Wi-Fi...")', 'time.Sleep(2*time.Second); writeSetupState("connecting","Conectando ao Wi-Fi...")')

p.write_text(s)

# ---------------------------------------------------------------------------
# 4) Validation: fail on the exact regressions seen on physical 0.1.5.
# ---------------------------------------------------------------------------
v = root/'builder/validate-source.sh'
vs = v.read_text()
marker = '# 2PNY_FIRST_ACCESS_0_1_6_HARDENED_CHECK'
if marker not in vs:
    vs += r'''
# 2PNY_FIRST_ACCESS_0_1_6_HARDENED_CHECK
bash -n rootfs-overlay/usr/local/sbin/2pny-firstboot
grep -q 'address1=10.42.0.1/24' rootfs-overlay/etc/NetworkManager/system-connections/2pny-setup.nmconnection
grep -q 'address1=10.42.0.1/24' rootfs-overlay/etc/NetworkManager/system-connections/2pny-ethernet-setup.nmconnection
grep -q 'method=auto' rootfs-overlay/etc/NetworkManager/system-connections/2pny-ethernet.nmconnection
test -f rootfs-overlay/etc/cloud/cloud-init.disabled
test -L rootfs-overlay/etc/systemd/system/NetworkManager-wait-online.service
test "$(readlink rootfs-overlay/etc/systemd/system/NetworkManager-wait-online.service)" = '/dev/null'
test -L rootfs-overlay/etc/systemd/system/multi-user.target.wants/2pnyd.service
test -L rootfs-overlay/etc/systemd/system/multi-user.target.wants/2pny-firstboot.service
! grep -q 'network-online.target' rootfs-overlay/etc/systemd/system/2pnyd.service
! grep -q "window.location.href='http://2pny.local" src/2pnyd/main.go
! grep -q 'http://2pny.local/api/setup-status' src/2pnyd/main.go
! grep -q '127.0.0.1:80' src/2pnyd/main.go
grep -q '2PNY-STATUS.txt' rootfs-overlay/usr/local/sbin/2pny-firstboot
grep -q 'DEBIAN_FRONTEND=noninteractive apt-get update' builder/build-image.sh
'''
v.write_text(vs)
PY

gofmt -w src/2pnyd/main.go
chmod 0755 rootfs-overlay/usr/local/sbin/2pny-firstboot builder/validate-source.sh
chmod 0600 rootfs-overlay/etc/NetworkManager/system-connections/*.nmconnection

echo '2PNY 0.1.6 hardened first-access, direct-Ethernet setup, no-mDNS dependency and Trixie build fix applied'
