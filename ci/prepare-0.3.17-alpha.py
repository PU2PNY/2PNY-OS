#!/usr/bin/env python3
"""Apply PU2PNY-OS 0.3.17-alpha focused D-Star/timezone overlay after 0.3.16."""
from pathlib import Path
import os,re,shutil,subprocess,sys,tempfile

root=Path(sys.argv[1]).resolve()
repo=Path(__file__).resolve().parents[1]
version="0.3.17-alpha"

def install(src,dst,mode=0o644):
    target=root/dst
    target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(repo/src,target)
    os.chmod(target,mode)

# REL-010: only reported 0.3.16 regressions are replaced.
for src,dst,mode in (
    ("src/2pnyd-main-0.3.17.go","src/2pnyd/main.go",0o644),
    ("src/hotspot-0.3.17.html","rootfs-overlay/usr/share/2pny/hotspot.html",0o644),
    ("src/2pny-protocol-network-apply-all-0.3.17.py","rootfs-overlay/usr/local/sbin/2pny-protocol-network-apply",0o755),
    ("src/2pny-station-worker-0.3.17.py","rootfs-overlay/usr/local/sbin/2pny-station-worker",0o755),
    ("src/2pny-live-core-0.3.17.py","rootfs-overlay/usr/local/lib/2pny-live-core.py",0o755),
    ("src/2pny-timezone-apply-0.3.17.py","rootfs-overlay/usr/local/sbin/2pny-timezone-apply",0o755),
    ("src/2pny-timezone-apply-0.3.17.path","rootfs-overlay/etc/systemd/system/2pny-timezone-apply.path",0o644),
    ("src/2pny-timezone-apply-0.3.17.service","rootfs-overlay/etc/systemd/system/2pny-timezone-apply.service",0o644),
):
    install(src,dst,mode)

(root/"rootfs-overlay/etc/2pny/version").write_text(version+"\n")

# Source syntax/compile.
subprocess.run(["gofmt","-w",str(root/"src/2pnyd/main.go")],check=True)
subprocess.run(["go","test",str(root/"src/2pnyd/main.go")],check=True)
for rel in (
    "rootfs-overlay/usr/local/sbin/2pny-protocol-network-apply",
    "rootfs-overlay/usr/local/sbin/2pny-station-worker",
    "rootfs-overlay/usr/local/lib/2pny-live-core.py",
    "rootfs-overlay/usr/local/sbin/2pny-timezone-apply",
):
    subprocess.run(["python3","-m","py_compile",str(root/rel)],check=True)
cache=root/"rootfs-overlay/usr/local/sbin/__pycache__"
if cache.exists():shutil.rmtree(cache)

# Hotspot inline JS.
wiz=(root/"rootfs-overlay/usr/share/2pny/hotspot.html").read_text()
for body in re.findall(r"<script(?:\s[^>]*)?>(.*?)</script>",wiz,re.I|re.S):
    if not body.strip():continue
    with tempfile.NamedTemporaryFile("w",suffix=".js",delete=False) as tf:
        tf.write(body);name=tf.name
    try:subprocess.run(["node","--check",name],check=True)
    finally:os.unlink(name)

main=(root/"src/2pnyd/main.go").read_text()
proto=(root/"rootfs-overlay/usr/local/sbin/2pny-protocol-network-apply").read_text()
station=(root/"rootfs-overlay/usr/local/sbin/2pny-station-worker").read_text()
hotspot=(root/"rootfs-overlay/usr/share/2pny/hotspot.html").read_text()
tz=(root/"rootfs-overlay/usr/local/sbin/2pny-timezone-apply").read_text()
tzpath=(root/"rootfs-overlay/etc/systemd/system/2pny-timezone-apply.path").read_text()
tzsvc=(root/"rootfs-overlay/etc/systemd/system/2pny-timezone-apply.service").read_text()

assert '"0.3.17-alpha"' in main

# PROTO-024: local module C is invariant; remote module remains reflector-only.
assert '"Module":"C" if proto=="DSTAR"' in proto
assert 'Band=C' in proto
assert 'LocalPort":"20011"' in proto and 'GatewayPort":"20010"' in proto
assert 'Reflector={reflector}' in proto
assert 'ReflectorReconnect=Never' in proto
assert 'ReflectorReconnect=Fixed' not in proto
assert 'ReloadTime=72' in proto and 'ReloadTimer=72' not in proto
assert 'D-Star.Module local não confirmou C' in proto

# Native commands/voice use the already-installed gateway and audio pack.
assert 'audio_path="/usr/share/2pny/audio/dstar/"' in proto

# LIVE-017/UI-032.
assert 'last_command' in station and 'Link command from' in station
assert 'Unlink command issued via' in station
assert 'last_command_target' in main and 'link_state' in main
assert 'id="dstarCommands"' in hotspot
for marker in ('_______I','_______E','_______U','_______L','XLX026DL','CQCQCQ'):
    assert marker in hotspot,marker
assert "stDstarLocal" in hotspot and "'C'" in hotspot

# SEC-024.
assert 'runTimezoneRequest' in main
assert 'timezone-request-"+requestID+".json' in main
assert 'timezone-result-"+requestID+".json' in main
assert 'request_id' in main
assert 'PathExistsGlob=/run/2pny/timezone-request-*.json' in tzpath
assert 'timedatectl","set-timezone"' in tz
assert 'request_id' in tz and 'effective_timezone' in tz
assert 'User=root' in tzsvc and 'ExecStart=/usr/local/sbin/2pny-timezone-apply' in tzsvc
assert 'ReadWritePaths=/run/2pny /etc/timezone' in tzsvc

# Frozen 0.3.16 baseline: check representative files/components are untouched by
# this overlay and still present after the full chain.
for required in (
    root/"rootfs-overlay/usr/local/libexec/2pny-dmr-apply",
    root/"rootfs-overlay/usr/local/sbin/2pny-network-switch",
    root/"rootfs-overlay/usr/local/sbin/2pny-aprs",
    root/"rootfs-overlay/usr/local/sbin/2pny-display-apply",
    root/"rootfs-overlay/usr/local/bin/2pny-direct-core",
):
    assert required.exists(),required

print("PREPARE_0317_OK")
