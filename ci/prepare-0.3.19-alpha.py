#!/usr/bin/env python3
"""Apply the focused PU2PNY-OS 0.3.19-alpha maintenance overlay.

Everything not explicitly changed by REL-013/REL-014 stays inherited from 0.3.18.
"""
from pathlib import Path
import os, re, shutil, subprocess, sys

root=Path(sys.argv[1]).resolve()
repo=Path(__file__).resolve().parents[1]
version="0.3.19-alpha"

def install(src,dst,mode=0o644):
    target=root/dst
    target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(repo/src,target)
    os.chmod(target,mode)

install("src/2pnyd-main-0.3.19.go","src/2pnyd/main.go")
install("src/ui-common-0.3.19.js","rootfs-overlay/usr/share/2pny/ui-common-0.3.0.js")
install("src/internet-0.3.19.html","rootfs-overlay/usr/share/2pny/internet.html")
install("src/hotspot-0.3.19.html","rootfs-overlay/usr/share/2pny/hotspot.html")
install("src/dashboard-0.3.19.html","rootfs-overlay/usr/share/2pny/dashboard.html")
install("src/expert-0.3.19.html","rootfs-overlay/usr/share/2pny/expert.html")
install("src/system-0.3.19.html","rootfs-overlay/usr/share/2pny/system.html")
install("src/display-0.3.19.html","rootfs-overlay/usr/share/2pny/display.html")
install("src/2pny-timezone-apply-0.3.19.py","rootfs-overlay/usr/local/sbin/2pny-timezone-apply",0o755)
install("src/2pny-display-core-0.3.19.py","rootfs-overlay/usr/local/sbin/2pny-display-core",0o755)
install("src/2pny-display-online-detect-0.3.19","rootfs-overlay/usr/local/sbin/2pny-display-online-detect",0o755)
install("src/2pny-display-online-detect-0.3.19.service","rootfs-overlay/etc/systemd/system/2pny-display-online-detect.service")
install("src/2pny-protocol-network-apply-all-0.3.19.py","rootfs-overlay/usr/local/sbin/2pny-protocol-network-apply",0o755)
install("src/2pny-protocol-network-apply-0.3.19.py","rootfs-overlay/usr/local/libexec/2pny-dmr-apply",0o755)
install("src/2pny-mode-apply-0.3.19","rootfs-overlay/usr/local/sbin/2pny-mode-apply",0o755)

# UI-035: every browser tab uses the product name only, including inherited pages.
ui_dir=root/"rootfs-overlay/usr/share/2pny"
for page in ui_dir.glob("*.html"):
    html=page.read_text()
    normalized,count=re.subn(r"(?is)<title>.*?</title>","<title>PU2PNY-OS</title>",html,count=1)
    if count==0 and re.search(r"(?is)<head[^>]*>",normalized):
        normalized=re.sub(r"(?is)(<head[^>]*>)",r"\1<title>PU2PNY-OS</title>",normalized,count=1)
    if normalized!=html:
        page.write_text(normalized)

wants=root/"rootfs-overlay/etc/systemd/system/multi-user.target.wants"
wants.mkdir(parents=True,exist_ok=True)
link=wants/"2pny-display-online-detect.service"
if link.exists() or link.is_symlink(): link.unlink()
link.symlink_to("../2pny-display-online-detect.service")

(root/"rootfs-overlay/etc/2pny/version").write_text(version+"\n")

subprocess.run(["gofmt","-w",str(root/"src/2pnyd/main.go")],check=True)
subprocess.run(["go","test",str(root/"src/2pnyd/main.go")],check=True)
for p in (
    root/"rootfs-overlay/usr/local/sbin/2pny-timezone-apply",
    root/"rootfs-overlay/usr/local/sbin/2pny-display-core",
    root/"rootfs-overlay/usr/local/sbin/2pny-protocol-network-apply",
    root/"rootfs-overlay/usr/local/libexec/2pny-dmr-apply",
):
    subprocess.run(["python3","-m","py_compile",str(p)],check=True)
subprocess.run(["bash","-n",str(root/"rootfs-overlay/usr/local/sbin/2pny-display-online-detect")],check=True)
subprocess.run(["bash","-n",str(root/"rootfs-overlay/usr/local/sbin/2pny-mode-apply")],check=True)
cache=root/"rootfs-overlay/usr/local/sbin/__pycache__"
if cache.exists(): shutil.rmtree(cache)

main=(root/"src/2pnyd/main.go").read_text()
internet=(root/"rootfs-overlay/usr/share/2pny/internet.html").read_text()
hotspot=(root/"rootfs-overlay/usr/share/2pny/hotspot.html").read_text()
dash=(root/"rootfs-overlay/usr/share/2pny/dashboard.html").read_text()
expert=(root/"rootfs-overlay/usr/share/2pny/expert.html").read_text()
system=(root/"rootfs-overlay/usr/share/2pny/system.html").read_text()
ui=(root/"rootfs-overlay/usr/share/2pny/ui-common-0.3.0.js").read_text()
assert "document.title='PU2PNY-OS'" in ui
for page in ui_dir.glob("*.html"):
    html=page.read_text()
    if re.search(r"(?is)<head[^>]*>",html):
        assert re.search(r"(?is)<title>\s*PU2PNY-OS\s*</title>",html),str(page)
displaycore=(root/"rootfs-overlay/usr/local/sbin/2pny-display-core").read_text()
tz=(root/"rootfs-overlay/usr/local/sbin/2pny-timezone-apply").read_text()
proto=(root/"rootfs-overlay/usr/local/sbin/2pny-protocol-network-apply").read_text()
dmr=(root/"rootfs-overlay/usr/local/libexec/2pny-dmr-apply").read_text()
mode=(root/"rootfs-overlay/usr/local/sbin/2pny-mode-apply").read_text()

assert '"0.3.19-alpha"' in main
compact="".join(main.split())
assert 'exec.Command("nmcli","device","reapply",iface)' not in compact
assert '"connection","up",conn,"ifname",iface' in compact
assert '/api/diagnostics/errors' in main
assert 'connection.autoconnect-retries 3' in (root/"rootfs-overlay/usr/local/sbin/2pny-network-switch").read_text()
assert 'rede conectada' in internet and 'Nenhuma segunda rede encontrada' in internet
assert 'Canal em uso:' in internet and ' melhor' in internet and ' atual' in internet
assert '<h3>Conexão via cabo</h3>' in internet and '<h3>Caminho da conexão</h3>' in internet
assert '<h1>Protocolos</h1>' in hotspot and 'Hotspot / Protocolos' not in hotspot
assert 'toFixed(6)' in hotspot and "replace(',','.')" in hotspot
for marker in ('_______I','_______E','_______U','_______L','XLX026DL','REF030CL','DUP+/DUP−'):
    assert marker in hotspot,marker
assert "Salvando perfil" in hotspot and "Atualizando perfil" in hotspot
assert 'slotFact' in dash and 'ccFact' in dash and 'TOT restante' in dash
assert 'dstarLinked' in dash and "nr.link_state==='linked'" in dash
assert 'expertLiveSection' in expert and 'generateSSHKey' in expert and 'pu2pny-erros.txt' in expert
assert "setInterval(function(){show(last)},250)" in system
assert "location.pathname==='/aprs'" in ui and '5000' in ui
assert 'range(0,101,10)' in displaycore and 'PU2PNY-OS' in displaycore
assert 'drain pending requests' in tz
assert '"Module":"C" if proto=="DSTAR"' in proto
assert 'Band=C' in proto and 'LocalPort":"20011"' in proto and 'GatewayPort":"20010"' in proto
assert 'ReflectorReconnect=Never' in proto
# REL-014 / RF-019 / PROTO-027 / PROTO-028
assert 'CYSFReflectors::findByName' in proto and 'startup_name' in proto
assert 'setsec(cp,"General",{"Duplex":"1" if usemode=="repeater" else "0"})' in proto
assert 'duplex=1 if usemode=="repeater" else 0' in dmr
assert 'slot1=True if duplex' in dmr and 'slot2=True if duplex' in dmr
assert 'route_slots=(1,2) if duplex' in dmr and 'Slot={remote_slot}' in dmr
assert 'out.append("Duplex="+duplex)' in mode
assert "RX '+a+' MHz · TX '+bb+' MHz" in dash and 'toFixed(6)' in dash
assert link.is_symlink() and os.readlink(link)=="../2pny-display-online-detect.service"
print("PREPARE_0319_OK")
