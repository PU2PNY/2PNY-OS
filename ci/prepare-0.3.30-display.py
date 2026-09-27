#!/usr/bin/env python3
"""PU2PNY-OS 0.3.30-alpha display-only overlay.

Installs only display runtime/UI files and patches only the display override
handler plus release version metadata. Protected RF/protocol/network/APRS/
Direct helpers are hashed before and after and must remain byte-identical.
"""
from pathlib import Path
import hashlib, os, re, shutil, subprocess, sys, tempfile

root=Path(sys.argv[1]).resolve()
repo=Path(__file__).resolve().parents[1]
version="0.3.30-alpha"

def sha(path):
    p=Path(path)
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() and p.is_file() else None

protected=[
    "rootfs-overlay/usr/local/sbin/2pny-protocol-network-apply",
    "rootfs-overlay/usr/local/libexec/2pny-dmr-apply",
    "rootfs-overlay/usr/local/sbin/2pny-station-worker",
    "rootfs-overlay/usr/local/sbin/2pny-network-switch",
    "rootfs-overlay/usr/local/sbin/2pny-wifi-profiles",
    "rootfs-overlay/usr/local/sbin/2pny-aprs",
    "rootfs-overlay/usr/local/bin/2pny-direct-core",
]
before={p:sha(root/p) for p in protected}

def install(src,dst,mode=0o644):
    target=root/dst
    target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(repo/src,target)
    os.chmod(target,mode)

install("src/2pny-display-core-0.3.30.py","rootfs-overlay/usr/local/sbin/2pny-display-core",0o755)
install("src/2pny-display-detector-0.3.30.py","rootfs-overlay/usr/local/sbin/2pny-display-detector",0o755)
install("src/2pny-display-apply-0.3.30.py","rootfs-overlay/usr/local/sbin/2pny-display-apply",0o755)
install("src/display-0.3.30.html","rootfs-overlay/usr/share/2pny/display.html",0o644)

main=root/"src/2pnyd/main.go"
text=main.read_text()
old_version='appVersion            = "0.3.29-alpha"'
new_version='appVersion            = "0.3.30-alpha"'
if text.count(old_version)!=1:
    raise SystemExit("0.3.30 appVersion anchor missing/ambiguous")
text=text.replace(old_version,new_version,1)

default_old='if in.Layout == 2 || in.Layout == 3 { in.Renderer = "mmdvmhost-native" } else { in.Renderer = "pu2pny-modern-v2" }'
default_new='if in.Layout == 0 || in.Layout == 2 || in.Layout == 3 { in.Renderer = "mmdvmhost-native" } else { in.Renderer = "pu2pny-modern-v2" }'
if text.count(default_old)!=1:
    raise SystemExit("0.3.30 renderer default condition missing/ambiguous")
text=text.replace(default_old,default_new,1)

forced_old='''\t\tif in.Enabled {
\t\t\t// DISPLAY-018: this endpoint controls Nextion through the modem.
\t\t\t// Hardware validation regressed with the MQTT/vector bridge, so the
\t\t\t// proven MMDVMHost-native writer is authoritative here.
\t\t\tin.Renderer = "mmdvmhost-native"
\t\t\tif in.Layout != 2 && in.Layout != 3 { in.Layout = 2 }
\t\t} else if in.Renderer == "pu2pny-modern-v2" {
\t\t\tin.Layout = 9
\t\t} else if in.Layout != 2 && in.Layout != 3 {
\t\t\tin.Layout = 2
\t\t}
'''
new_block='''\t\t// DISPLAY-024: honor the explicit display renderer selection. Both modes
\t\t// keep MMDVMHost as the modem UART owner; 2pny-display-apply guarantees
\t\t// exactly one logical writer and rolls back a failed transition.
\t\tif in.Enabled {
\t\t\tif in.Renderer == "pu2pny-modern-v2" {
\t\t\t\tin.Layout = 9
\t\t\t} else if in.Layout != 0 && in.Layout != 2 && in.Layout != 3 {
\t\t\t\tin.Layout = 2
\t\t\t}
\t\t} else if in.Renderer == "pu2pny-modern-v2" {
\t\t\tin.Layout = 9
\t\t} else if in.Layout != 0 && in.Layout != 2 && in.Layout != 3 {
\t\t\tin.Layout = 2
\t\t}
'''
if text.count(forced_old)!=1:
    raise SystemExit("0.3.30 forced-renderer block missing/ambiguous")
text=text.replace(forced_old,new_block,1)

main.write_text(text)

(root/"rootfs-overlay/etc/2pny/version").write_text(version+"\n")

after={p:sha(root/p) for p in protected}
changed=[p for p in protected if before[p]!=after[p]]
if changed:
    raise SystemExit("0.3.30 protected runtime changed: "+", ".join(changed))

subprocess.run(["gofmt","-w",str(main)],check=True)
subprocess.run(["go","test",str(main)],check=True)
for p in (
    root/"rootfs-overlay/usr/local/sbin/2pny-display-core",
    root/"rootfs-overlay/usr/local/sbin/2pny-display-detector",
    root/"rootfs-overlay/usr/local/sbin/2pny-display-apply",
):
    subprocess.run(["python3","-m","py_compile",str(p)],check=True)
for cache in root.rglob("__pycache__"):
    shutil.rmtree(cache,ignore_errors=True)
html=(root/"rootfs-overlay/usr/share/2pny/display.html").read_text()
for body in re.findall(r"<script(?:\s[^>]*)?>(.*?)</script>",html,re.I|re.S):
    if not body.strip(): continue
    with tempfile.NamedTemporaryFile("w",suffix=".js",delete=False) as tf:
        tf.write(body); tmp=tf.name
    try: subprocess.run(["node","--check",tmp],check=True)
    finally: os.unlink(tmp)

assert 'value="mmdvmhost-native"' in html
assert 'ScreenLayout 0' in html and 'ScreenLayout 2' in html and 'ScreenLayout 3' in html
assert "hardwareProof" in html and "firmware_version" in html and "flash_size_bytes" in html
print("DISPLAY_0330_PREPARE_OK")
print("PROTECTED_IDENTICAL")
