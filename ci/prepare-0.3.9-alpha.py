#!/usr/bin/env python3
"""Apply PU2PNY-OS 0.3.9-alpha corrective overlay after 0.3.8.

This overlay preserves the complete inherited chain and replaces only components
implicated by the 0.3.8 physical-test cycle. DMR's proven helper, History and
Direct UI are deliberately inherited unchanged.
"""
from pathlib import Path
import os, re, shutil, subprocess, sys, tempfile

root=Path(sys.argv[1]).resolve()
repo=Path(__file__).resolve().parents[1]
version="0.3.9-alpha"

def install(src,dst,mode=0o644):
    target=root/dst
    target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(repo/src,target)
    os.chmod(target,mode)

# Backend and shared UI.
install("src/2pnyd-main-0.3.9.go","src/2pnyd/main.go")
for src,dst in (
    ("src/ui-common-0.3.9.js","rootfs-overlay/usr/share/2pny/ui-common-0.3.0.js"),
    ("src/ui-language-0.3.9.js","rootfs-overlay/usr/share/2pny/ui-language.js"),
    ("src/internet-0.3.9.html","rootfs-overlay/usr/share/2pny/internet.html"),
    ("src/expert-0.3.9.html","rootfs-overlay/usr/share/2pny/expert.html"),
    ("src/system-0.3.9.html","rootfs-overlay/usr/share/2pny/system.html"),
    ("src/display-0.3.9.html","rootfs-overlay/usr/share/2pny/display.html"),
):
    install(src,dst)

# Runtime helpers. DMR helper is intentionally not overlaid.
for src,dst in (
    ("src/2pny-protocol-network-apply-all-0.3.9.py","rootfs-overlay/usr/local/sbin/2pny-protocol-network-apply"),
    ("src/2pny-display-apply-0.3.9.py","rootfs-overlay/usr/local/sbin/2pny-display-apply"),
    ("src/2pny-display-status-0.3.9.py","rootfs-overlay/usr/local/sbin/2pny-display-status"),
    ("src/2pny-network-switch-0.3.9","rootfs-overlay/usr/local/sbin/2pny-network-switch"),
    ("src/2pny-network-core-0.3.9","rootfs-overlay/usr/local/sbin/2pny-network-core"),
    ("src/2pny-operational-apply-0.3.9.py","rootfs-overlay/usr/local/sbin/2pny-operational-apply"),
    ("src/2pny-timezone-apply-0.3.9.py","rootfs-overlay/usr/local/sbin/2pny-timezone-apply"),
    ("src/2pny-ssh-apply-0.3.9.py","rootfs-overlay/usr/local/sbin/2pny-ssh-apply"),
    ("src/2pny-display-apply-request-0.3.9.py","rootfs-overlay/usr/local/sbin/2pny-display-apply-request"),
):
    install(src,dst,0o755)

# Dedicated privileged units and request watches.
for src,dst in (
    ("src/2pny-timezone-apply-0.3.9.service","rootfs-overlay/etc/systemd/system/2pny-timezone-apply.service"),
    ("src/2pny-ssh-apply-0.3.9.service","rootfs-overlay/etc/systemd/system/2pny-ssh-apply.service"),
    ("src/2pny-operational-restore-0.3.9.service","rootfs-overlay/etc/systemd/system/2pny-operational-restore.service"),
    ("src/2pny-display-apply-request-0.3.9.service","rootfs-overlay/etc/systemd/system/2pny-display-apply-request.service"),
    ("src/2pny-timezone-apply-0.3.9.path","rootfs-overlay/etc/systemd/system/2pny-timezone-apply.path"),
    ("src/2pny-ssh-apply-0.3.9.path","rootfs-overlay/etc/systemd/system/2pny-ssh-apply.path"),
    ("src/2pny-operational-apply-0.3.9.path","rootfs-overlay/etc/systemd/system/2pny-operational-apply.path"),
    ("src/2pny-rflevel-apply-0.3.9.path","rootfs-overlay/etc/systemd/system/2pny-rflevel-apply.path"),
    ("src/2pny-display-apply-request-0.3.9.path","rootfs-overlay/etc/systemd/system/2pny-display-apply-request.path"),
):
    install(src,dst,0o644)

(root/"rootfs-overlay/etc/2pny/version").write_text(version+"\n")

# Boot restore and narrow privileged request watchers must be enabled.
wants=root/"rootfs-overlay/etc/systemd/system/multi-user.target.wants"
wants.mkdir(parents=True,exist_ok=True)
for unit in (
    "2pny-operational-restore.service",
    "2pny-timezone-apply.path",
    "2pny-ssh-apply.path",
    "2pny-operational-apply.path",
    "2pny-rflevel-apply.path",
    "2pny-display-apply-request.path",
):
    link=wants/unit
    if link.exists() or link.is_symlink(): link.unlink()
    os.symlink("../"+unit,link)

# Canonical setup network is 10.43.0.1. Historical overlays created a
# NetworkManager shared-dnsmasq fallback at 10.42.0.1; rewrite only that
# fallback so it cannot contradict the current network core.
dns=root/"rootfs-overlay/etc/NetworkManager/dnsmasq-shared.d/2pny-captive.conf"
dns.parent.mkdir(parents=True,exist_ok=True)
dns.write_text("""# PU2PNY captive setup fallback
# Keep this legacy interception path HTTP-only. Do not advertise the modern
# Captive-Portal DHCP option until PU2PNY can provide a per-device HTTPS API.
address=/#/10.43.0.1
address=/pu2pny.local/10.43.0.1
local=/pu2pny.local/
""")

# Compile/syntax gates.
subprocess.run(["gofmt","-w",str(root/"src/2pnyd/main.go")],check=True)
subprocess.run(["go","test",str(root/"src/2pnyd/main.go")],check=True)
subprocess.run(["python3","-m","py_compile",
    str(root/"rootfs-overlay/usr/local/sbin/2pny-protocol-network-apply"),
    str(root/"rootfs-overlay/usr/local/sbin/2pny-display-apply"),
    str(root/"rootfs-overlay/usr/local/sbin/2pny-display-status"),
    str(root/"rootfs-overlay/usr/local/sbin/2pny-operational-apply"),
    str(root/"rootfs-overlay/usr/local/sbin/2pny-timezone-apply"),
    str(root/"rootfs-overlay/usr/local/sbin/2pny-ssh-apply"),
    str(root/"rootfs-overlay/usr/local/sbin/2pny-display-apply-request"),
],check=True)
subprocess.run(["bash","-n",
    str(root/"rootfs-overlay/usr/local/sbin/2pny-network-switch"),
    str(root/"rootfs-overlay/usr/local/sbin/2pny-network-core"),
],check=True)
subprocess.run(["node","--check",str(root/"rootfs-overlay/usr/share/2pny/ui-common-0.3.0.js")],check=True)
subprocess.run(["node","--check",str(root/"rootfs-overlay/usr/share/2pny/ui-language.js")],check=True)

# Parse every inline JS block we replace.
for html in ("internet.html","expert.html","system.html","display.html"):
    txt=(root/"rootfs-overlay/usr/share/2pny"/html).read_text()
    for body in re.findall(r"<script(?:\s[^>]*)?>(.*?)</script>",txt,re.I|re.S):
        if not body.strip(): continue
        with tempfile.NamedTemporaryFile("w",suffix=".js",delete=False) as tf:
            tf.write(body);name=tf.name
        try: subprocess.run(["node","--check",name],check=True)
        finally: os.unlink(name)

# 0.3.9 structural invariants from 0.3.8 physical feedback.
main=(root/"src/2pnyd/main.go").read_text()
proto=(root/"rootfs-overlay/usr/local/sbin/2pny-protocol-network-apply").read_text()
net=(root/"rootfs-overlay/usr/local/sbin/2pny-network-switch").read_text()
netcore=(root/"rootfs-overlay/usr/local/sbin/2pny-network-core").read_text()
display_status=(root/"rootfs-overlay/usr/local/sbin/2pny-display-status").read_text()
display_apply=(root/"rootfs-overlay/usr/local/sbin/2pny-display-apply").read_text()
ui=(root/"rootfs-overlay/usr/share/2pny/ui-common-0.3.0.js").read_text()
expert=(root/"rootfs-overlay/usr/share/2pny/expert.html").read_text()
internet=(root/"rootfs-overlay/usr/share/2pny/internet.html").read_text()
lang=(root/"rootfs-overlay/usr/share/2pny/ui-language.js").read_text()

assert '"0.3.9-alpha"' in main
assert 'udp_listener(20010)' in proto and 'udp_listener(4200)' in proto
assert 'local=cols[3]' in proto and 'local=cols[4]' not in proto
assert 'verify_host_bridge_config(proto)' in proto
assert 'deadline=time.time()+12' in proto
assert r'\\b127\\.0\\.0\\.1:20010' not in proto
assert 'for attempt in 1 2 3' in net and 'merge_scan_json' in net
assert "sed -i '/^dhcp-option-force=114,/d'" in netcore
assert 'if test ! -f "$STATE/provisioned"; then' in netcore
assert 'test -f "$STATE/provisioned" || return 0' in netcore
assert 'http://10.43.0.1/wizard?captive=1' in main
assert '5 GHz' in internet and 'bandgraph' in internet and 'effective_dns' in internet
assert "addEventListener('live'" in ui and "addEventListener('live'" in expert
assert "mmdvmhost-authoritative" in display_status
assert '"error": (0, "Erro / Error")' in display_status
assert 'ScreenLayout' in display_apply and 'não confirmou o layout Nextion solicitado' in display_apply
assert 'strings.TrimSuffix(service, ".service") + ".path"' in main
assert 'exec.Command("systemctl", "start", service)' not in main
assert 'effective_dns' in main
assert 'if(!base){base=text;originals.set(node,base)}' in lang
# UI-024 retired the temporary iframe injection. 0.3.9 corrective source
# must no longer require or reintroduce it.
assert 'function enhanceHotspot(){ return }' in ui
assert 'pny-protocol-frame' not in ui
assert "var live=q('liveBox')" in ui

# Preserve approved inherited areas: do not overlay DMR, Direct or History.
dmr=root/"rootfs-overlay/usr/local/libexec/2pny-dmr-apply"
assert dmr.exists()
assert "network_id=dmrid+essid if essid and len(dmrid)==7 else dmrid" in dmr.read_text()
assert (root/"rootfs-overlay/usr/share/2pny/direct.html").exists()
assert (root/"rootfs-overlay/usr/share/2pny/history.html").exists()

# No stale captive fallback may survive.
assert "10.42.0.1" not in dns.read_text()
assert "10.43.0.1" in dns.read_text()
assert "dhcp-option-force=114," not in dns.read_text()

print("PU2PNY-OS 0.3.9 corrective overlay applied")
