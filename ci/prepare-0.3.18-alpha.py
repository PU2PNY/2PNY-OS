#!/usr/bin/env python3
"""Apply PU2PNY-OS 0.3.18-alpha after the complete 0.3.17 overlay.

REL-011 corrects the DStarGateway native audio data path. REL-012 adds the
explicitly requested SEC-025 D-Star radio administration controls before this
release is published. Everything else remains inherited/frozen.
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
install("src/2pny-radio-admin-0.3.17.py",
        "rootfs-overlay/usr/local/sbin/2pny-radio-admin",0o755)
install("src/2pny-radio-admin-0.3.17.path",
        "rootfs-overlay/etc/systemd/system/2pny-radio-admin.path",0o644)
install("src/2pny-radio-admin-0.3.17.service",
        "rootfs-overlay/etc/systemd/system/2pny-radio-admin.service",0o644)

wants=root/"rootfs-overlay/etc/systemd/system/multi-user.target.wants"
wants.mkdir(parents=True,exist_ok=True)
radio_link=wants/"2pny-radio-admin.path"
if radio_link.exists() or radio_link.is_symlink(): radio_link.unlink()
radio_link.symlink_to("../2pny-radio-admin.path")

# Stage and hook the exact pinned DStarGateway source patch before its build.
install("ci/patch-dstargateway-radio-admin-0.3.17.py",
        "rootfs-overlay/builder/patch-dstargateway-radio-admin-0.3.17.py",0o755)
builder=root/"builder/build-image.sh"
bs=builder.read_text()
stage_anchor='cp "$ROOT_DIR/rootfs-overlay/builder/patch-dmrgateway-hourly-0.2.9.py" "$ROOT_MNT/builder/"'
stage_line=stage_anchor+'\ncp "$ROOT_DIR/rootfs-overlay/builder/patch-dstargateway-radio-admin-0.3.17.py" "$ROOT_MNT/builder/"'
if "patch-dstargateway-radio-admin-0.3.17.py" not in bs:
    if stage_anchor not in bs: raise SystemExit("0.3.18: DStar patch staging anchor missing")
    bs=bs.replace(stage_anchor,stage_line,1)

if "PU2PNY_DSTAR_RADIO_ADMIN_0318" not in bs:
    lines=bs.splitlines()
    # Patch the pinned DStarGateway source before its own compile step. The old
    # generic "first make after libboost" anchor could land after the gateway
    # had already been built/cleaned, leaving no RepeaterHandler.cpp in /tmp.
    make_i=None
    for i,line in enumerate(lines):
        if "make -C DStarGateway" in line:
            make_i=i;break
    if make_i is None:
        raise SystemExit("0.3.18: exact DStarGateway make anchor missing")
    hook=[
      '# PU2PNY_DSTAR_RADIO_ADMIN_0318',
      'DSTAR_RF_ADMIN_SRC="$(find /tmp -maxdepth 4 -type f -path "*/Common/RepeaterHandler.cpp" -print -quit)"',
      'test -n "$DSTAR_RF_ADMIN_SRC" || { echo "DStarGateway source for PU2PNY radio-admin patch not found" >&2; exit 1; }',
      'DSTAR_RF_ADMIN_ROOT="$(dirname "$(dirname "$DSTAR_RF_ADMIN_SRC")")"',
      'python3 /builder/patch-dstargateway-radio-admin-0.3.17.py "$DSTAR_RF_ADMIN_ROOT"',
    ]
    lines[make_i:make_i]=hook
    bs="\n".join(lines)+"\n"
builder.write_text(bs);os.chmod(builder,0o755)

(root/"rootfs-overlay/etc/2pny/version").write_text(version+"\n")

subprocess.run(["gofmt","-w",str(root/"src/2pnyd/main.go")],check=True)
subprocess.run(["go","test",str(root/"src/2pnyd/main.go")],check=True)
subprocess.run(["python3","-m","py_compile",
                str(root/"rootfs-overlay/usr/local/sbin/2pny-protocol-network-apply")],check=True)
subprocess.run(["python3","-m","py_compile",
                str(root/"rootfs-overlay/usr/local/sbin/2pny-radio-admin")],check=True)
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

# SEC-025 / REL-012.
radio=(root/"rootfs-overlay/usr/local/sbin/2pny-radio-admin").read_text()
radiopath=(root/"rootfs-overlay/etc/systemd/system/2pny-radio-admin.path").read_text()
radiosvc=(root/"rootfs-overlay/etc/systemd/system/2pny-radio-admin.service").read_text()
for marker in ('ARM_SECONDS=30','"OFF"','"REBOOT"','"PROFILE"','2pny-protocol-profiles'):
    assert marker in radio,marker
assert 'PathExists=/run/2pny/radio-admin-command.request' in radiopath
assert 'User=root' in radiosvc and 'ReadWritePaths=/run/2pny /var/lib/2pny' in radiosvc
assert radio_link.is_symlink() and os.readlink(radio_link)=="../2pny-radio-admin.path"
assert "PU2PNY_DSTAR_RADIO_ADMIN_0318" in builder.read_text()
assert "patch-dstargateway-radio-admin-0.3.17.py" in builder.read_text()
hotspot=(root/"rootfs-overlay/usr/share/2pny/hotspot.html").read_text()
for cmd in ("PNYARM","PNYOFF","PNYRBT","PNYDMR","PNYDST","PNYYSF","PNYP25","PNYNXD","PNYPOC"):
    assert cmd in hotspot,cmd

print("PREPARE_0318_OK")
