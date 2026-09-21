#!/usr/bin/env python3
"""Apply PU2PNY-OS 0.3.8-alpha corrective overlay after 0.3.7.

This overlay is intentionally narrow: it keeps the complete 0.3.7 chain and
replaces only components implicated by the 0.3.7 physical test cycle.
"""
from pathlib import Path
import os, re, shutil, subprocess, sys, tempfile

root=Path(sys.argv[1]).resolve()
repo=Path(__file__).resolve().parents[1]
version="0.3.8-alpha"

def install(src,dst,mode=0o644):
    target=root/dst
    target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(repo/src,target)
    os.chmod(target,mode)

# Core and corrected UI.
install("src/2pnyd-main-0.3.8.go","src/2pnyd/main.go")
for src,dst in (
    ("src/ui-common-0.3.8.js","rootfs-overlay/usr/share/2pny/ui-common-0.3.0.js"),
    ("src/ui-language-0.3.8.js","rootfs-overlay/usr/share/2pny/ui-language.js"),
    ("src/internet-0.3.8.html","rootfs-overlay/usr/share/2pny/internet.html"),
    ("src/hotspot-0.3.8.html","rootfs-overlay/usr/share/2pny/hotspot.html"),
    ("src/protocols-0.3.8.html","rootfs-overlay/usr/share/2pny/protocols.html"),
    ("src/direct-0.3.8.html","rootfs-overlay/usr/share/2pny/direct.html"),
    ("src/aprs-0.3.8.html","rootfs-overlay/usr/share/2pny/aprs.html"),
    ("src/display-0.3.8.html","rootfs-overlay/usr/share/2pny/display.html"),
    ("src/expert-0.3.8.html","rootfs-overlay/usr/share/2pny/expert.html"),
):
    install(src,dst)

# Runtime helpers. DMR's proven helper is deliberately untouched.
for src,dst in (
    ("src/2pny-protocol-network-apply-all-0.3.8.py","rootfs-overlay/usr/local/sbin/2pny-protocol-network-apply"),
    ("src/2pny-display-apply-0.3.8.py","rootfs-overlay/usr/local/sbin/2pny-display-apply"),
    ("src/2pny-timezone-apply-0.3.8.py","rootfs-overlay/usr/local/sbin/2pny-timezone-apply"),
    ("src/2pny-rflevel-apply-0.3.8.py","rootfs-overlay/usr/local/sbin/2pny-rflevel-apply"),
    ("src/2pny-ssh-apply-0.3.8.py","rootfs-overlay/usr/local/sbin/2pny-ssh-apply"),
):
    install(src,dst,0o755)
for src,dst in (
    ("src/2pny-timezone-apply-0.3.8.service","rootfs-overlay/etc/systemd/system/2pny-timezone-apply.service"),
    ("src/2pny-rflevel-apply-0.3.8.service","rootfs-overlay/etc/systemd/system/2pny-rflevel-apply.service"),
    ("src/2pny-ssh-apply-0.3.8.service","rootfs-overlay/etc/systemd/system/2pny-ssh-apply.service"),
):
    install(src,dst,0o644)

(root/"rootfs-overlay/etc/2pny/version").write_text(version+"\n")

# Harden the daemon service without broadening its write access. Privileged
# changes use the dedicated one-shot units above.
svc=root/"rootfs-overlay/etc/systemd/system/2pnyd.service"
if svc.exists():
    text=svc.read_text()
    if "ReadWritePaths=/var/lib/2pny /run" not in text and "ReadWritePaths=" in text:
        raise SystemExit("0.3.8: unexpected 2pnyd ReadWritePaths")
    svc.write_text(text)

# Compile/syntax gates before the image build.
subprocess.run(["gofmt","-w",str(root/"src/2pnyd/main.go")],check=True)
subprocess.run(["go","test",str(root/"src/2pnyd/main.go")],check=True)
subprocess.run(["python3","-m","py_compile",
    str(root/"rootfs-overlay/usr/local/sbin/2pny-protocol-network-apply"),
    str(root/"rootfs-overlay/usr/local/sbin/2pny-display-apply"),
    str(root/"rootfs-overlay/usr/local/sbin/2pny-timezone-apply"),
    str(root/"rootfs-overlay/usr/local/sbin/2pny-rflevel-apply"),
    str(root/"rootfs-overlay/usr/local/sbin/2pny-ssh-apply"),
],check=True)
subprocess.run(["node","--check",str(root/"rootfs-overlay/usr/share/2pny/ui-common-0.3.0.js")],check=True)
subprocess.run(["node","--check",str(root/"rootfs-overlay/usr/share/2pny/ui-language.js")],check=True)

# Parse every inline script with Node's syntax checker.
for html in ("internet.html","hotspot.html","protocols.html","direct.html","aprs.html","display.html","expert.html"):
    txt=(root/"rootfs-overlay/usr/share/2pny"/html).read_text()
    for n,body in enumerate(re.findall(r"<script(?:\s[^>]*)?>(.*?)</script>",txt,re.I|re.S)):
        if not body.strip(): continue
        with tempfile.NamedTemporaryFile("w",suffix=".js",delete=False) as tf:
            tf.write(body);name=tf.name
        try: subprocess.run(["node","--check",name],check=True)
        finally: os.unlink(name)

# Structural invariants from the physical test findings.
main=(root/"src/2pnyd/main.go").read_text()
ui=(root/"rootfs-overlay/usr/share/2pny/ui-common-0.3.0.js").read_text()
lang=(root/"rootfs-overlay/usr/share/2pny/ui-language.js").read_text()
internet=(root/"rootfs-overlay/usr/share/2pny/internet.html").read_text()
hotspot=(root/"rootfs-overlay/usr/share/2pny/hotspot.html").read_text()
protocols=(root/"rootfs-overlay/usr/share/2pny/protocols.html").read_text()
direct=(root/"rootfs-overlay/usr/share/2pny/direct.html").read_text()
aprs=(root/"rootfs-overlay/usr/share/2pny/aprs.html").read_text()
display=(root/"rootfs-overlay/usr/share/2pny/display.html").read_text()
expert=(root/"rootfs-overlay/usr/share/2pny/expert.html").read_text()
pa=(root/"rootfs-overlay/usr/local/sbin/2pny-protocol-network-apply").read_text()
da=(root/"rootfs-overlay/usr/local/sbin/2pny-display-apply").read_text()

assert '"0.3.8-alpha"' in main
assert '/api/rf/power' in main and '2pny-timezone-apply.service' in main and '2pny-ssh-apply.service' in main
assert 'wifi_signal' in main and 'wifi_quality' in main
assert 'Hotspot / Protocolos' in ui and '/protocols/embed' in main
assert 'Saúde da comunicação' in ui and '/api/live/events' in ui
assert 'data-showpass' in internet and 'wifiChannelGraph' in internet
assert 'Configuração integrada' in ui and 'troca rápida use Ao Vivo' in hotspot
assert "seen[key]" in protocols
assert 'Pareie um PU2PNY antes de chamar' in direct and 'q(\'call\').disabled' in direct
assert 'Etapa 1/5' in aprs and 'Você não precisa digitar passcode' in aprs
assert 'displayDirty' in display and 'effective_layout' in da and 'ScreenLayout' in da
assert 'new EventSource(\'/api/live/events\')' in expert and '/api/rf/power' in expert
assert 'RFLevel' in expert and 'radioexpert' in expert
assert 'WiresXCommandPassthrough=0' in pa and 'Reconnect=0' in pa and 'porta 4200' in pa and 'porta 20010' in pa
assert "characterData:true" in lang and "loose={" in lang

# Translation gate: all operational pages must load the common layer, which
# injects the selected-language catalog. The catalog must contain all three.
for html in ("internet.html","hotspot.html","protocols.html","direct.html","aprs.html","display.html","expert.html",
             "dashboard.html","history.html","system.html"):
    p=root/"rootfs-overlay/usr/share/2pny"/html
    if p.exists():
        t=p.read_text()
        assert '/ui-common-0.3.0.js' in t, html+" missing common UI/i18n loader"
assert "value=\"pt\"" in ui and "value=\"en\"" in ui and "value=\"es\"" in ui

# Preserve the proven DMR helper byte-for-byte from the inherited build tree;
# 0.3.8 never overlays it.
dmr=root/"rootfs-overlay/usr/local/libexec/2pny-dmr-apply"
assert dmr.exists() and "network_id=dmrid+essid if essid and len(dmrid)==7 else dmrid" in dmr.read_text()

print("PU2PNY-OS 0.3.8 corrective overlay applied")
