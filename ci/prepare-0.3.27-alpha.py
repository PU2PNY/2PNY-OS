#!/usr/bin/env python3
"""PU2PNY-OS 0.3.27 overlay: APRS message-only + BrandMeister credential UX.

All DMR/D-Star/YSF runtime helpers are inherited byte-for-byte from 0.3.26.
"""
from pathlib import Path
import os,re,shutil,subprocess,sys,tempfile

root=Path(sys.argv[1]).resolve()
repo=Path(__file__).resolve().parents[1]
version="0.3.27-alpha"

def install(src,dst,mode=0o644):
    target=root/dst
    target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(repo/src,target)
    os.chmod(target,mode)

for src,dst,mode in [
    ("src/2pnyd-main-0.3.27.go","src/2pnyd/main.go",0o644),
    ("src/hotspot-0.3.27.html","rootfs-overlay/usr/share/2pny/hotspot.html",0o644),
    ("src/aprs-0.3.27.html","rootfs-overlay/usr/share/2pny/aprs.html",0o644),
    ("src/2pny-aprs-0.3.27.py","rootfs-overlay/usr/local/sbin/2pny-aprs",0o755),
    ("src/ui-language-0.3.27.js","rootfs-overlay/usr/share/2pny/ui-language.js",0o644),
]:
    install(src,dst,mode)

(root/"rootfs-overlay/etc/2pny/version").write_text(version+"\n")

# Protected protocol baseline: exact helpers entering the image must not change.
pairs=[
 ("rootfs-overlay/usr/local/sbin/2pny-protocol-network-apply","src/2pny-protocol-network-apply-all-0.3.20.py"),
 ("rootfs-overlay/usr/local/libexec/2pny-dmr-apply","src/2pny-protocol-network-apply-0.3.21.py"),
]
for staged,source in pairs:
    if (root/staged).read_bytes()!=(repo/source).read_bytes():
        raise SystemExit("0.3.27 protected protocol helper changed: "+staged)

subprocess.run(["gofmt","-w",str(root/"src/2pnyd/main.go")],check=True)
subprocess.run(["go","test",str(root/"src/2pnyd/main.go")],check=True)
subprocess.run(["python3","-m","py_compile",str(root/"rootfs-overlay/usr/local/sbin/2pny-aprs")],check=True)
subprocess.run(["node","--check",str(root/"rootfs-overlay/usr/share/2pny/ui-language.js")],check=True)

for page in ("hotspot.html","aprs.html"):
    html=(root/"rootfs-overlay/usr/share/2pny"/page).read_text()
    for body in re.findall(r"<script(?:\s[^>]*)?>(.*?)</script>",html,re.I|re.S):
        if not body.strip(): continue
        with tempfile.NamedTemporaryFile("w",suffix=".js",delete=False) as tf:
            tf.write(body); tmp=tf.name
        try: subprocess.run(["node","--check",tmp],check=True)
        finally: os.unlink(tmp)

main=(root/"src/2pnyd/main.go").read_text()
hot=(root/"rootfs-overlay/usr/share/2pny/hotspot.html").read_text()
aprs=(root/"rootfs-overlay/usr/local/sbin/2pny-aprs").read_text()
aprsui=(root/"rootfs-overlay/usr/share/2pny/aprs.html").read_text().lower()

assert 'appVersion            = "0.3.27-alpha"' in main
assert 'id="bmSecurityPassword"' in hot and 'type="password"' in hot
assert 'hotspot_security_configured' in main
assert 'protocol-secrets", "dmr.secret"' in main
assert 'message_only' in main
assert 'cfg.get("latitude")' not in aprs and 'cfg.get("longitude")' not in aprs and 'beacon(cfg' not in aprs
for x in ('id="lat"','id="lon"','uselocation','aprs.fi','mapstub','radarcore'):
    assert x not in aprsui
print("PREPARE_0327_OK")
