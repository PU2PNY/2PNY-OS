#!/usr/bin/env python3
from pathlib import Path
import os, shutil, subprocess, sys

root=Path(sys.argv[1]).resolve()
repo=Path(__file__).resolve().parents[1]
version="0.3.6-alpha"

def install(src,dst,mode):
    target=root/dst
    target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(repo/src,target)
    os.chmod(target,mode)

# 0.3.6 overlays the complete 0.3.5 image. The physically approved DMR
# binaries/helper are intentionally preserved; this cycle changes only shared
# UI/network/runtime pieces and non-DMR protocol configuration.
install("src/2pnyd-main-0.3.6.go","src/2pnyd/main.go",0o644)
for src,dst in (
 ("src/wizard-0.3.6.html","rootfs-overlay/usr/share/2pny/wizard.html"),
 ("src/dashboard-0.3.6.html","rootfs-overlay/usr/share/2pny/dashboard.html"),
 ("src/internet-0.3.6.html","rootfs-overlay/usr/share/2pny/internet.html"),
 ("src/hotspot-0.3.6.html","rootfs-overlay/usr/share/2pny/hotspot.html"),
 ("src/protocols-0.3.6.html","rootfs-overlay/usr/share/2pny/protocols.html"),
 ("src/history-0.3.6.html","rootfs-overlay/usr/share/2pny/history.html"),
 ("src/aprs-0.3.6.html","rootfs-overlay/usr/share/2pny/aprs.html"),
 ("src/display-0.3.6.html","rootfs-overlay/usr/share/2pny/display.html"),
 ("src/system-0.3.6.html","rootfs-overlay/usr/share/2pny/system.html"),
 ("src/expert-0.3.6.html","rootfs-overlay/usr/share/2pny/expert.html"),
 ("src/ui-common-0.3.6.js","rootfs-overlay/usr/share/2pny/ui-common-0.3.0.js"),
 ("src/ui-language-0.3.6.js","rootfs-overlay/usr/share/2pny/ui-language.js"),
):
    install(src,dst,0o644)

for src,dst in (
 ("src/2pny-network-switch-0.3.6","rootfs-overlay/usr/local/sbin/2pny-network-switch"),
 ("src/2pny-wifi-profiles-0.3.6","rootfs-overlay/usr/local/sbin/2pny-wifi-profiles"),
 ("src/2pny-auto-maintenance-0.3.6","rootfs-overlay/usr/local/sbin/2pny-auto-maintenance"),
 ("src/2pny-netdiag-0.3.6.py","rootfs-overlay/usr/local/sbin/2pny-netdiag"),
 ("src/2pny-protocol-network-apply-all-0.3.6.py","rootfs-overlay/usr/local/sbin/2pny-protocol-network-apply"),
 ("src/2pny-protocol-profiles-0.3.6.py","rootfs-overlay/usr/local/sbin/2pny-protocol-profiles"),
 ("src/2pny-update-manager-0.3.6.py","rootfs-overlay/usr/local/sbin/2pny-update-manager"),
 ("src/2pny-station-worker-0.3.6.py","rootfs-overlay/usr/local/sbin/2pny-station-worker"),
 ("src/2pny-display-core-0.3.6.py","rootfs-overlay/usr/local/sbin/2pny-display-core"),
):
    install(src,dst,0o755)

(root/"rootfs-overlay/etc/2pny").mkdir(parents=True,exist_ok=True)
(root/"rootfs-overlay/etc/2pny/version").write_text(version+"\n")

for rel in (
 "rootfs-overlay/usr/local/sbin/2pny-network-switch",
 "rootfs-overlay/usr/local/sbin/2pny-wifi-profiles",
 "rootfs-overlay/usr/local/sbin/2pny-auto-maintenance",
):
    subprocess.run(["bash","-n",str(root/rel)],check=True)
for rel in (
 "rootfs-overlay/usr/local/sbin/2pny-netdiag",
 "rootfs-overlay/usr/local/sbin/2pny-protocol-network-apply",
 "rootfs-overlay/usr/local/sbin/2pny-protocol-profiles",
 "rootfs-overlay/usr/local/sbin/2pny-update-manager",
 "rootfs-overlay/usr/local/sbin/2pny-station-worker",
 "rootfs-overlay/usr/local/sbin/2pny-display-core",
):
    subprocess.run(["python3","-m","py_compile",str(root/rel)],check=True)
    cache=(root/rel).parent/"__pycache__"
    if cache.exists():shutil.rmtree(cache)

main=(root/"src/2pnyd/main.go").read_text()
sw=(root/"rootfs-overlay/usr/local/sbin/2pny-network-switch").read_text()
wp=(root/"rootfs-overlay/usr/local/sbin/2pny-wifi-profiles").read_text()
nd=(root/"rootfs-overlay/usr/local/sbin/2pny-netdiag").read_text()
pa=(root/"rootfs-overlay/usr/local/sbin/2pny-protocol-network-apply").read_text()
profiles=(root/"rootfs-overlay/usr/local/sbin/2pny-protocol-profiles").read_text()
updater=(root/"rootfs-overlay/usr/local/sbin/2pny-update-manager").read_text()
station=(root/"rootfs-overlay/usr/local/sbin/2pny-station-worker").read_text()
internet=(root/"rootfs-overlay/usr/share/2pny/internet.html").read_text()
protocols=(root/"rootfs-overlay/usr/share/2pny/protocols.html").read_text()
system=(root/"rootfs-overlay/usr/share/2pny/system.html").read_text()
aprs=(root/"rootfs-overlay/usr/share/2pny/aprs.html").read_text()
expert=(root/"rootfs-overlay/usr/share/2pny/expert.html").read_text()
history=(root/"rootfs-overlay/usr/share/2pny/history.html").read_text()
dash=(root/"rootfs-overlay/usr/share/2pny/dashboard.html").read_text()
wiz=(root/"rootfs-overlay/usr/share/2pny/wizard.html").read_text()
common=(root/"rootfs-overlay/usr/share/2pny/ui-common-0.3.0.js").read_text()
lang=(root/"rootfs-overlay/usr/share/2pny/ui-language.js").read_text()
display=(root/"rootfs-overlay/usr/local/sbin/2pny-display-core").read_text()

assert '"0.3.6-alpha"' in main
assert 'friendlyNetworkError' in main and '/api/protocol/profiles' in main and '2pny-update-manager' in main
assert '${paused:-0}' in sw and 'set type managed' in sw
assert 'Rede Wi-Fi 2' in wp
assert 'quality_label' in nd and 'Melhor opção' in nd
assert '[Gateway]' in pa and '[Repeater_1]' in pa and '[HostsFiles]' in pa
assert 'Ensure the server selected' in pa and '"connected":False' in pa
assert 'protocol-profiles.json' in profiles and 'rollback' in profiles
assert 'ALLOWED_PREFIX' in updater and 'sha256(pkg)' in updater and 'rollback' in updater
assert 'DExtra|D-Plus|DCS' in station and 'Link has failed, polls lost' in station
assert 'Rede Wi‑Fi 1 e Rede Wi‑Fi 2' in internet and 'wifiSecondManual' in internet
assert 'Perfil do protocolo' in protocols and 'Gateway ativo / aguardando rede' in protocols
assert 'installUpdate' in system and 'Guardar versão atual para rollback' in system
assert 'navigator.geolocation' in aprs
assert '/wizard?step=1' not in expert and '/wizard?step=3' not in expert
assert 'qrz.com/db/' in history and 'radioid.net/api/dmr/user/' in history
assert 'qrz.com/db/' in dash and 'radioid.net/api/dmr/user/' in dash
assert 'Ex.: PU2ABC' in wiz and 'Ex.: 7240000' in wiz and '>Radio ID<' in wiz
assert 'function operation' in common
assert 'MutationObserver' in lang and "'Melhor opção'" in lang
assert 'RF>NET' in display and 'NET>RF' in display
print("PU2PNY-OS 0.3.6 corrective/feature overlay applied")
