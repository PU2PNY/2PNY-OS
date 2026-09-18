#!/usr/bin/env python3
from pathlib import Path
import os, re, shutil, subprocess, sys

root=Path(sys.argv[1]).resolve()
repo=Path(__file__).resolve().parents[1]
version="0.2.7-alpha"
DMRGATEWAY_COMMIT="2a3306de313cf4c094c2031c9ced5a6858bbbfcc"
DISPLAY_COMMIT="96a0705d818c4234960a61dd2837e32f9450f811"

def install(src,dst,mode):
    target=root/dst
    target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(repo/src,target)
    os.chmod(target,mode)

install("src/2pnyd-main-0.2.7.go","src/2pnyd/main.go",0o644)
install("src/2pny-network-switch-0.2.7","rootfs-overlay/usr/local/sbin/2pny-network-switch",0o755)
install("src/2pny-rf-apply-0.2.7","rootfs-overlay/usr/local/sbin/2pny-rf-apply",0o755)
install("src/2pny-protocol-network-apply-0.2.7.py","rootfs-overlay/usr/local/sbin/2pny-protocol-network-apply",0o755)
install("src/2pny-server-catalog-0.2.7.py","rootfs-overlay/usr/local/sbin/2pny-server-catalog",0o755)
install("src/2pny-live-status-0.2.7.py","rootfs-overlay/usr/local/sbin/2pny-live-status",0o755)
install("src/2pny-display-apply-0.2.7.py","rootfs-overlay/usr/local/sbin/2pny-display-apply",0o755)
install("src/2pny-display-status-0.2.7.py","rootfs-overlay/usr/local/sbin/2pny-display-status",0o755)
install("src/wizard-0.2.7.html","rootfs-overlay/usr/share/2pny/wizard.html",0o644)
install("src/dashboard-0.2.7.html","rootfs-overlay/usr/share/2pny/dashboard.html",0o644)
install("src/2pny-mmdvmhost-0.2.7.service","rootfs-overlay/etc/systemd/system/2pny-mmdvmhost.service",0o644)
install("src/2pny-dmrgateway-0.2.7.service","rootfs-overlay/etc/systemd/system/2pny-dmrgateway.service",0o644)
install("src/2pny-display-0.2.7.service","rootfs-overlay/etc/systemd/system/2pny-display.service",0o644)
install("src/mosquitto-pu2pny-0.2.7.conf","rootfs-overlay/etc/mosquitto/conf.d/pu2pny-local.conf",0o644)

install("src/2pny-network-core-0.2.7","rootfs-overlay/usr/local/sbin/2pny-network-core",0o755)
install("src/2pny-station-worker-0.2.7.py","rootfs-overlay/usr/local/sbin/2pny-station-worker",0o755)
install("src/2pny-station-0.2.7.service","rootfs-overlay/etc/systemd/system/2pny-station.service",0o644)
install("src/2pny-expert-ssh-0.2.7","rootfs-overlay/usr/local/sbin/2pny-expert-ssh",0o755)
install("src/ui-language-0.2.7.js","rootfs-overlay/usr/share/2pny/ui-language.js",0o644)
for name in ("var/lib/2pny/station","var/cache/2pny/photos","run/2pny"):
    (root/"rootfs-overlay"/name).mkdir(parents=True,exist_ok=True)
wants=root/"rootfs-overlay/etc/systemd/system/multi-user.target.wants"
wants.mkdir(parents=True,exist_ok=True)
link=wants/"2pny-station.service"
if link.exists() or link.is_symlink():link.unlink()
link.symlink_to("../2pny-station.service")
avahi=root/"rootfs-overlay/etc/avahi/avahi-daemon.conf"
avahi.parent.mkdir(parents=True,exist_ok=True)
avahi.write_text("[server]\nhost-name=pu2pny\nuse-ipv4=yes\nuse-ipv6=yes\n[wide-area]\nenable-wide-area=no\n[publish]\npublish-addresses=yes\npublish-workstation=yes\n[reflector]\nenable-reflector=no\n")
(root/"rootfs-overlay/etc/2pny/version").write_text(version+"\n")

for rel in ("builder/build-image.sh","rootfs-overlay/usr/local/sbin/2pny-firstboot"):
    p=root/rel
    if not p.exists(): continue
    s=p.read_text()
    s=s.replace("0.2.5-alpha",version)
    p.write_text(s)

# Compile DMRGateway and MMDVM-Display from pinned upstream commits inside the
# target image before the existing MMDVMHost build toolchain is removed.
builder=root/"builder/build-image.sh"
s=builder.read_text()
anchor="apt-get purge -y g++ make git libmosquitto-dev nlohmann-json3-dev"
if anchor not in s:
    raise SystemExit("0.2.7 builder: MMDVM build purge anchor not found")
if "PU2PNY_DMRGATEWAY_DISPLAY_0_2_7" not in s:
    block=r'''# PU2PNY_DMRGATEWAY_DISPLAY_0_2_7
DG_COMMIT="2a3306de313cf4c094c2031c9ced5a6858bbbfcc"
DG=/tmp/DMRGateway
rm -rf "$DG"
git init -q "$DG"
cd "$DG"
git remote add origin https://github.com/g4klx/DMRGateway.git
git fetch -q --depth=1 origin "$DG_COMMIT"
git checkout -q --detach FETCH_HEAD
test "$(git rev-parse HEAD)" = "$DG_COMMIT"
make -j"$JOBS"
strip --strip-unneeded DMRGateway
install -D -m 0755 DMRGateway /usr/local/bin/DMRGateway
printf '%s\n' "$DG_COMMIT" >/usr/share/2pny/upstream/DMRGateway.commit

DISP_COMMIT="96a0705d818c4234960a61dd2837e32f9450f811"
DISP=/tmp/MMDVM-Display
rm -rf "$DISP"
git init -q "$DISP"
cd "$DISP"
git remote add origin https://github.com/g4klx/MMDVM-Display.git
git fetch -q --depth=1 origin "$DISP_COMMIT"
git checkout -q --detach FETCH_HEAD
test "$(git rev-parse HEAD)" = "$DISP_COMMIT"
make -j"$JOBS"
strip --strip-unneeded MMDVM-Display NextionUpdater
install -D -m 0755 MMDVM-Display /usr/local/bin/MMDVM-Display
install -D -m 0755 NextionUpdater /usr/local/bin/NextionUpdater
printf '%s\n' "$DISP_COMMIT" >/usr/share/2pny/upstream/MMDVMDisplay.commit
cd /
rm -rf "$DG" "$DISP"

'''
    s=s.replace(anchor,block+anchor,1)

runtime_old="apt-get install -y --no-install-recommends libmosquitto1"
runtime_new="apt-get install -y --no-install-recommends libmosquitto1 mosquitto mosquitto-clients openssh-server"
if runtime_old not in s:
    raise SystemExit("0.2.7 builder: runtime mosquitto anchor not found")
s=s.replace(runtime_old,runtime_new,1)
builder.write_text(s)
os.chmod(builder,0o755)

# No previous mutable provisioning/test state may leak into a release image.
for rel in (
    "rootfs-overlay/var/lib/2pny/provisioned",
    "rootfs-overlay/var/lib/2pny/rf-configured",
    "rootfs-overlay/var/lib/2pny/rf-apply-state.json",
    "rootfs-overlay/var/lib/2pny/network-radio.json",
    "rootfs-overlay/var/lib/2pny/display-runtime.json",
    "rootfs-overlay/var/lib/2pny/display-status.json",
    "rootfs-overlay/var/lib/2pny/display-override.json",
    "rootfs-overlay/var/lib/2pny/network-connect.json",
    "rootfs-overlay/var/lib/2pny/wifi-scan.json",
    "rootfs-overlay/var/lib/2pny/mmdvm-baud",
    "rootfs-overlay/var/lib/2pny/dmr/DMRGateway.ini",
    "rootfs-overlay/var/lib/2pny/dmr/XLXHosts.txt",
    "rootfs-overlay/var/lib/2pny/display/MMDVM-Display.ini",
    "rootfs-overlay/var/lib/2pny/secrets/brandmeister-api.key",
):
    try:(root/rel).unlink()
    except FileNotFoundError:pass

for rel in (
    "rootfs-overlay/var/lib/2pny/dmr",
    "rootfs-overlay/var/lib/2pny/display",
    "rootfs-overlay/var/lib/2pny/secrets",
):
    (root/rel).mkdir(parents=True,exist_ok=True)

subprocess.run(["gofmt","-w",str(root/"src/2pnyd/main.go")],check=True)
for rel in (
    "rootfs-overlay/usr/local/sbin/2pny-network-switch",
    "rootfs-overlay/usr/local/sbin/2pny-rf-apply",
    "rootfs-overlay/usr/local/sbin/2pny-network-core",
    "rootfs-overlay/usr/local/sbin/2pny-mode-apply",
    "rootfs-overlay/usr/local/sbin/2pny-auto-maintenance",
    "rootfs-overlay/usr/local/sbin/2pny-hostfiles-update",
):
    subprocess.run(["bash","-n",str(root/rel)],check=True)
for rel in (
    "rootfs-overlay/usr/local/sbin/2pny-protocol-network-apply",
    "rootfs-overlay/usr/local/sbin/2pny-server-catalog",
    "rootfs-overlay/usr/local/sbin/2pny-live-status",
    "rootfs-overlay/usr/local/sbin/2pny-display-apply",
    "rootfs-overlay/usr/local/sbin/2pny-display-status",
    "rootfs-overlay/usr/local/sbin/2pny-hardware-probe",
):
    subprocess.run(["python3","-m","py_compile",str(root/rel)],check=True)
cache=root/"rootfs-overlay/usr/local/sbin/__pycache__"
if cache.exists(): shutil.rmtree(cache)

main=(root/"src/2pnyd/main.go").read_text()
rf=(root/"rootfs-overlay/usr/local/sbin/2pny-rf-apply").read_text()
net=(root/"rootfs-overlay/usr/local/sbin/2pny-protocol-network-apply").read_text()
wiz=(root/"rootfs-overlay/usr/share/2pny/wizard.html").read_text()
dash=(root/"rootfs-overlay/usr/share/2pny/dashboard.html").read_text()
mosq=(root/"rootfs-overlay/etc/mosquitto/conf.d/pu2pny-local.conf").read_text()
display=(root/"rootfs-overlay/usr/local/sbin/2pny-display-apply").read_text()

assert re.search(r'appVersion\s*=\s*"0\.2\.7-alpha"',main)
assert "DMRSlot" in main and "BMAPIConfigured" in main
assert '"dmrgateway_active"' in main and '"mmdvm_baud"' in main
assert 'MODEM_BAUD=' in rf and 'UARTSpeed=$MODEM_BAUD' in rf
assert 'GatewayAddress=127.0.0.1' in rf
assert "DMRGateway.ini" in net and "XLX Network" in net
assert "MMDVM-Display.ini" in display
assert "listener 1883 127.0.0.1" in mosq and "0.0.0.0" not in mosq
for needle in ("Time Slot","Hotspot Security","BrandMeister API Key","Módulo XLX"):
    assert needle in wiz
for needle in ("TX · Seu rádio → Internet","RX · Internet → seu rádio","Internet e rede local","MTR / qualidade"):
    assert needle in dash
assert DMRGATEWAY_COMMIT in builder.read_text()
assert DISPLAY_COMMIT in builder.read_text()
print("PU2PNY-OS 0.2.7 radio/network/display/live patch applied")

