#!/usr/bin/env python3
"""Apply the PU2PNY-OS 0.3.7-alpha overlay after the complete 0.3.6 chain.

Scope:
- preserves all 0.3.6 Wi-Fi/RF/DMR/APRS/update corrections;
- adds PU2PNY Direct control/relay client without touching RF when idle;
- installs Moderno V2 display renderer;
- installs D-Star upstream audio data and dgwvoicetransmit so the pinned
  DStarGateway can actually emit its native link-status audio;
- keeps hardware claims out of build-time validation.
"""
from pathlib import Path
import os, shutil, subprocess, sys

root=Path(sys.argv[1]).resolve()
repo=Path(__file__).resolve().parents[1]
version="0.3.7-alpha"

def install(src,dst,mode):
    target=root/dst
    target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(repo/src,target)
    os.chmod(target,mode)

# Backend/UI/runtime overlays. DMR helper/binary is deliberately untouched.
install("src/2pnyd-main-0.3.7.go","src/2pnyd/main.go",0o644)
for src,dst in (
    ("src/direct-0.3.7.html","rootfs-overlay/usr/share/2pny/direct.html"),
    ("src/display-0.3.7.html","rootfs-overlay/usr/share/2pny/display.html"),
    ("src/ui-common-0.3.7.js","rootfs-overlay/usr/share/2pny/ui-common-0.3.0.js"),
):
    install(src,dst,0o644)

for src,dst in (
    ("src/2pny-display-core-0.3.7.py","rootfs-overlay/usr/local/sbin/2pny-display-core"),
    ("src/2pny-protocol-network-apply-all-0.3.7.py","rootfs-overlay/usr/local/sbin/2pny-protocol-network-apply"),
    ("src/2pny-direct-start-0.3.7","rootfs-overlay/usr/local/sbin/2pny-direct-start"),
    ("src/2pny-direct-recover-0.3.7","rootfs-overlay/usr/local/sbin/2pny-direct-recover"),
    ("src/2pny-direct-core-0.3.7.service","rootfs-overlay/etc/systemd/system/2pny-direct.service"),
):
    install(src,dst,0o755 if not src.endswith(".service") else 0o644)

# Stage Direct Go sources into the build tree, then build natively for the ARM64
# image runner. No CGO/native dependency is needed.
direct_dir=root/"src/direct-core"
direct_dir.mkdir(parents=True,exist_ok=True)
for name in ("direct_types.go","direct_session.go","direct_transport.go","direct_radio.go","direct_main.go"):
    shutil.copy2(repo/"src/direct-core"/name,direct_dir/name)
subprocess.run(["gofmt","-w",*(str(direct_dir/n) for n in ("direct_types.go","direct_session.go","direct_transport.go","direct_radio.go","direct_main.go"))],check=True)
subprocess.run(["go","test",*(str(direct_dir/n) for n in ("direct_types.go","direct_session.go","direct_transport.go","direct_radio.go","direct_main.go"))],check=True)
target=root/"rootfs-overlay/usr/local/bin/2pny-direct-core"
target.parent.mkdir(parents=True,exist_ok=True)
env=os.environ.copy();env.update({"GOOS":"linux","GOARCH":"arm64","CGO_ENABLED":"0"})
subprocess.run(["go","build","-trimpath","-o",str(target),*(str(direct_dir/n) for n in ("direct_types.go","direct_session.go","direct_transport.go","direct_radio.go","direct_main.go"))],check=True,env=env)
os.chmod(target,0o755)

# Enable Direct service. Before provisioning ConditionPathExists prevents it
# from starting; the local panel can also start it on demand after onboarding.
wants=root/"rootfs-overlay/etc/systemd/system/multi-user.target.wants"
wants.mkdir(parents=True,exist_ok=True)
link=wants/"2pny-direct.service"
if link.exists() or link.is_symlink(): link.unlink()
link.symlink_to("../2pny-direct.service")

(root/"rootfs-overlay/var/lib/2pny/direct").mkdir(parents=True,exist_ok=True)
(root/"rootfs-overlay/etc/2pny/version").write_text(version+"\n")

# D-Star voice fix: the pinned F4FXL gateway already triggers its AudioUnit
# on link state changes, but 0.3.6 only installed dstargateway and did not
# carry the upstream AMBE/INDX audio data into the image.
builder=root/"builder/build-image.sh"
s=builder.read_text()
old='make -j"$JOBS" DStarGateway/dstargateway'
new='make -j"$JOBS" DStarGateway/dstargateway DGWVoiceTransmit/dgwvoicetransmit'
if old not in s and new not in s:
    raise SystemExit("0.3.7 builder: D-Star build anchor missing")
s=s.replace(old,new,1)
old2='install -D -m 0755 DStarGateway/dstargateway /usr/local/bin/dstargateway'
new2='''install -D -m 0755 DStarGateway/dstargateway /usr/local/bin/dstargateway
strip --strip-unneeded DGWVoiceTransmit/dgwvoicetransmit
install -D -m 0755 DGWVoiceTransmit/dgwvoicetransmit /usr/local/bin/dgwvoicetransmit
mkdir -p /usr/share/2pny/audio/dstar
cp -a Data/*.ambe Data/*.indx /usr/share/2pny/audio/dstar/
chmod 0644 /usr/share/2pny/audio/dstar/*'''
if old2 not in s and 'install -D -m 0755 DGWVoiceTransmit/dgwvoicetransmit' not in s:
    raise SystemExit("0.3.7 builder: D-Star install anchor missing")
s=s.replace(old2,new2,1)
builder.write_text(s)

# Syntax / invariant gates before the expensive image build.
subprocess.run(["python3","-m","py_compile",
    str(root/"rootfs-overlay/usr/local/sbin/2pny-display-core"),
    str(root/"rootfs-overlay/usr/local/sbin/2pny-protocol-network-apply")],check=True)
subprocess.run(["bash","-n",str(root/"rootfs-overlay/usr/local/sbin/2pny-direct-start"),str(root/"rootfs-overlay/usr/local/sbin/2pny-direct-recover")],check=True)
main=(root/"src/2pnyd/main.go").read_text()
direct=(root/"rootfs-overlay/usr/share/2pny/direct.html").read_text()
display=(root/"rootfs-overlay/usr/local/sbin/2pny-display-core").read_text()
pa=(root/"rootfs-overlay/usr/local/sbin/2pny-protocol-network-apply").read_text()
ui=(root/"rootfs-overlay/usr/share/2pny/ui-common-0.3.0.js").read_text()
assert '"0.3.7-alpha"' in main
assert '/api/direct/call' in main and '/direct' in main
assert 'PU2PNY Direct' in direct and 'Direct' in ui
assert 'PU2PNY Moderno V2' in display and 'Graphical 128x64 renderer' in display
assert 'Data={audio_path}' in pa and '/usr/share/2pny/audio/dstar/' in pa
assert 'DGWVoiceTransmit/dgwvoicetransmit' in s and 'Data/*.ambe' in s
assert 'network_id=dmrid+essid if essid and len(dmrid)==7 else dmrid' in (root/"rootfs-overlay/usr/local/libexec/2pny-dmr-apply").read_text()
print("PU2PNY-OS 0.3.7 overlay applied")
