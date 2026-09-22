#!/usr/bin/env python3
"""Apply PU2PNY-OS 0.3.18-alpha after the complete 0.3.17 overlay.

REL-011 is intentionally tiny: only the DStarGateway native audio data path
and the release version change. Everything else remains byte-for-byte inherited.
"""
from pathlib import Path
import os, shutil, subprocess, sys

root=Path(sys.argv[1]).resolve()
repo=Path(__file__).resolve().parents[1]
version="0.3.18-alpha"

def install(src,dst,mode=0o644):
    target=root/dst
    target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(repo/src,target)
    os.chmod(target,mode)

install("src/2pnyd-main-0.3.18.go","src/2pnyd/main.go")
install("src/2pny-protocol-network-apply-all-0.3.18.py",
        "rootfs-overlay/usr/local/sbin/2pny-protocol-network-apply",0o755)
(root/"rootfs-overlay/etc/2pny/version").write_text(version+"\n")

subprocess.run(["gofmt","-w",str(root/"src/2pnyd/main.go")],check=True)
subprocess.run(["go","test",str(root/"src/2pnyd/main.go")],check=True)
subprocess.run(["python3","-m","py_compile",
                str(root/"rootfs-overlay/usr/local/sbin/2pny-protocol-network-apply")],check=True)
cache=root/"rootfs-overlay/usr/local/sbin/__pycache__"
if cache.exists():shutil.rmtree(cache)

main=(root/"src/2pnyd/main.go").read_text()
proto=(root/"rootfs-overlay/usr/local/sbin/2pny-protocol-network-apply").read_text()

assert '"0.3.18-alpha"' in main
assert 'audio_path="/usr/local/share/dstargateway.d/"' in proto
assert 'audio_path="/usr/share/2pny/audio/dstar/"' not in proto

# All PROTO-024 corrections from 0.3.17 remain intact.
assert '"Module":"C" if proto=="DSTAR"' in proto
assert 'Band=C' in proto
assert 'ReflectorReconnect=Never' in proto
assert 'ReloadTime=72' in proto and 'ReloadTimer=72' not in proto
assert 'LocalPort":"20011"' in proto and 'GatewayPort":"20010"' in proto
assert 'HBPort=20010' in proto and 'Port=20011' in proto
assert 'D-Star.Module local não confirmou C' in proto

print("PREPARE_0318_OK")
