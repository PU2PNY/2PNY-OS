#!/usr/bin/env python3
"""PU2PNY-OS 0.3.25: network-only corrective overlay over 0.3.24.

Protected baseline: RF/protocol/clock/voice/UI behavior remains inherited.
The Wi-Fi association/reconnect implementation from 0.3.23 is not modified.
"""
from pathlib import Path
import os,re,shutil,subprocess,sys,tempfile

root=Path(sys.argv[1]).resolve()
repo=Path(__file__).resolve().parents[1]
version="0.3.25-alpha"

def install(src,dst,mode=0o644):
    target=root/dst
    target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(repo/src,target)
    os.chmod(target,mode)

# Scope is intentionally restricted to first-access routing and mDNS.
for src,dst,mode in [
    ("src/2pnyd-main-0.3.25.go","src/2pnyd/main.go",0o644),
    ("src/wizard-0.3.25.html","rootfs-overlay/usr/share/2pny/wizard.html",0o644),
    ("src/2pny-mdns-guard-0.3.25","rootfs-overlay/usr/local/sbin/2pny-mdns-guard",0o755),
    ("src/2pny-mdns-guard-0.3.25.service","rootfs-overlay/etc/systemd/system/2pny-mdns-guard.service",0o644),
]:
    install(src,dst,mode)

# Ensure the already-existing mDNS guard is also executed once after boot/network.
wants=root/"rootfs-overlay/etc/systemd/system/multi-user.target.wants"
wants.mkdir(parents=True,exist_ok=True)
link=wants/"2pny-mdns-guard.service"
if link.exists() or link.is_symlink():
    link.unlink()
link.symlink_to("../2pny-mdns-guard.service")

(root/"rootfs-overlay/etc/2pny/version").write_text(version+"\n")

# Protected Wi-Fi runtime must be byte-for-byte the 0.3.23 implementation.
staged_switch=root/"rootfs-overlay/usr/local/sbin/2pny-network-switch"
protected_switch=repo/"src/2pny-network-switch-0.3.16"
if staged_switch.read_bytes()!=protected_switch.read_bytes():
    raise SystemExit("0.3.25 scope violation: protected 0.3.23 Wi-Fi switch changed")

# The Wi-Fi connect/reconnect section of the wizard must also remain exact.
def block(text,start,end):
    a=text.index(start); b=text.index(end,a)
    return text[a:b]
old_wiz=(repo/"src/wizard-0.3.21.html").read_text()
new_wiz=(repo/"src/wizard-0.3.25.html").read_text()
start="function selectedSSID(){"
end="q('refreshEthernet').onclick="
if block(old_wiz,start,end)!=block(new_wiz,start,end):
    raise SystemExit("0.3.25 scope violation: protected Wi-Fi wizard flow changed")

subprocess.run(["gofmt","-w",str(root/"src/2pnyd/main.go")],check=True)
subprocess.run(["go","test",str(root/"src/2pnyd/main.go")],check=True)
subprocess.run(["bash","-n",str(root/"rootfs-overlay/usr/local/sbin/2pny-mdns-guard")],check=True)

# Inline wizard JS must parse.
html=(root/"rootfs-overlay/usr/share/2pny/wizard.html").read_text()
for body in re.findall(r"<script(?:\s[^>]*)?>(.*?)</script>",html,re.I|re.S):
    if not body.strip(): continue
    with tempfile.NamedTemporaryFile("w",suffix=".js",delete=False) as tf:
        tf.write(body); tmp=tf.name
    try: subprocess.run(["node","--check",tmp],check=True)
    finally: os.unlink(tmp)

main=(root/"src/2pnyd/main.go").read_text()
mdns=(root/"rootfs-overlay/usr/local/sbin/2pny-mdns-guard").read_text()
assert 'appVersion            = "0.3.25-alpha"' in main
assert 'else if cachedConnectivitySnapshot().Internet {' in main
assert 'fileExists(filepath.Join(dataDir, "uplink-ssid")) && cachedConnectivitySnapshot().Internet' not in main
assert "ethernetAutoAdvanced" in html
assert "c.internet&&c.ethernet" in html
assert "new URLSearchParams(location.search).get('step')!=='1'" in html
assert "host-name\",\"pu2pny" in mdns
assert "5353" in mdns and "mdns-state" in mdns
assert link.is_symlink()

print("PREPARE_0325_OK")
