#!/usr/bin/env python3
from pathlib import Path
import os,re,shutil,subprocess,sys

root=Path(sys.argv[1]).resolve()
repo=Path(__file__).resolve().parents[1]
version="0.2.9-alpha"
DMRGATEWAY_COMMIT="2a3306de313cf4c094c2031c9ced5a6858bbbfcc"
DSTAR_COMMIT="612f388727a9bb47aaeaae3a89f5abff3152ed93"
YSF_COMMIT="a71e33aaed25a93e8c2bb2d87fc5fb7491e72fe7"
P25_COMMIT="3c5fb387c4e2d676a7c79069d2bb3541473b0528"
NXDN_COMMIT="8950677e9876e577fb87b955cfa93bacd059209d"
FLAGS_COMMIT="086f7e97d657358203916dbe84f61c2bccaa81eb"

def install(src,dst,mode):
    target=root/dst
    target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(repo/src,target)
    os.chmod(target,mode)

# Web/backend modules
install("src/2pnyd-main-0.2.9.go","src/2pnyd/main.go",0o644)
install("src/wizard-0.2.9.html","rootfs-overlay/usr/share/2pny/wizard.html",0o644)
install("src/dashboard-0.2.9.html","rootfs-overlay/usr/share/2pny/dashboard.html",0o644)
install("src/ui-language-0.2.7.js","rootfs-overlay/usr/share/2pny/ui-language.js",0o644)

# Wi-Fi module
install("src/2pny-network-switch-0.2.9","rootfs-overlay/usr/local/sbin/2pny-network-switch",0o755)
install("src/2pny-network-core-0.2.7","rootfs-overlay/usr/local/sbin/2pny-network-core",0o755)

# Live/RadioID database module
install("src/2pny-live-core-0.2.9.py","rootfs-overlay/usr/local/lib/2pny-live-core.py",0o644)
install("src/2pny-station-worker-0.2.9.py","rootfs-overlay/usr/local/sbin/2pny-station-worker",0o755)
install("src/2pny-station-0.2.8.service","rootfs-overlay/etc/systemd/system/2pny-station.service",0o644)

# Display module
install("src/2pny-display-core-0.2.9.py","rootfs-overlay/usr/local/sbin/2pny-display-core",0o755)
install("src/2pny-display-core-0.2.9.service","rootfs-overlay/etc/systemd/system/2pny-display-core.service",0o644)
install("src/2pny-display-apply-0.2.9.py","rootfs-overlay/usr/local/sbin/2pny-display-apply",0o755)
install("src/2pny-display-status-0.2.8.py","rootfs-overlay/usr/local/sbin/2pny-display-status",0o755)

# Protocol/catalog modules
install("src/2pny-server-catalog-0.2.9.py","rootfs-overlay/usr/local/sbin/2pny-server-catalog",0o755)
install("src/2pny-hostfiles-update-0.2.9","rootfs-overlay/usr/local/sbin/2pny-hostfiles-update",0o755)
install("src/2pny-protocol-network-apply-0.2.9.py","rootfs-overlay/usr/local/libexec/2pny-dmr-apply",0o755)
install("src/2pny-protocol-network-apply-all-0.2.9.py","rootfs-overlay/usr/local/sbin/2pny-protocol-network-apply",0o755)
for src,dst in (
 ("src/2pny-dstargateway-0.2.9.service","rootfs-overlay/etc/systemd/system/2pny-dstargateway.service"),
 ("src/2pny-ysfgateway-0.2.9.service","rootfs-overlay/etc/systemd/system/2pny-ysfgateway.service"),
 ("src/2pny-p25gateway-0.2.9.service","rootfs-overlay/etc/systemd/system/2pny-p25gateway.service"),
 ("src/2pny-nxdngateway-0.2.9.service","rootfs-overlay/etc/systemd/system/2pny-nxdngateway.service"),
):
    install(src,dst,0o644)

# APRS module
install("src/2pny-aprs-0.2.9.py","rootfs-overlay/usr/local/sbin/2pny-aprs",0o755)
install("src/2pny-aprs-0.2.9.service","rootfs-overlay/etc/systemd/system/2pny-aprs.service",0o644)

# Build-time DMRGateway patches
install("ci/patch-dmrgateway-pu2pny-0.2.9.py","builder/patch-dmrgateway-pu2pny-0.2.9.py",0o755)
install("ci/patch-dmrgateway-hourly-0.2.9.py","builder/patch-dmrgateway-hourly-0.2.9.py",0o755)

(root/"rootfs-overlay/etc/2pny/version").write_text(version+"\n")
for rel in ("rootfs-overlay/var/lib/2pny/station","rootfs-overlay/var/cache/2pny/photos",
            "rootfs-overlay/run/2pny","rootfs-overlay/var/lib/2pny/dstar","rootfs-overlay/var/lib/2pny/ysf",
            "rootfs-overlay/var/lib/2pny/p25","rootfs-overlay/var/lib/2pny/nxdn"):
    (root/rel).mkdir(parents=True,exist_ok=True)

# Enable only passive/control modules. Protocol gateways are enabled when selected.
wants=root/"rootfs-overlay/etc/systemd/system/multi-user.target.wants"
wants.mkdir(parents=True,exist_ok=True)
for service in ("2pny-station.service","2pny-display-core.service","2pny-aprs.service"):
    link=wants/service
    if link.exists() or link.is_symlink():link.unlink()
    link.symlink_to("../"+service)

# Patch image builder. 0.2.7 already leaves the C++ toolchain installed until
# the known purge anchor, so compile all optional gateways immediately before it.
builder=root/"builder/build-image.sh"
s=builder.read_text()
# The gateway compilation happens inside the target chroot before the normal
# overlay rsync. Stage the two tiny source patches into the target first.
chroot_anchor='chroot "$ROOT_MNT" env MMDVMHOST_COMMIT="$MMDVMHOST_COMMIT" /bin/bash -s <<\'MMDVM_BUILD\''
if "PU2PNY_029_STAGE_BUILD_PATCHES" not in s:
    if chroot_anchor not in s: raise SystemExit("0.2.9 builder: chroot anchor missing")
    stage='''# PU2PNY_029_STAGE_BUILD_PATCHES
mkdir -p "$ROOT_MNT/builder"
cp "$ROOT_DIR/rootfs-overlay/builder/patch-dmrgateway-pu2pny-0.2.9.py" "$ROOT_MNT/builder/"
cp "$ROOT_DIR/rootfs-overlay/builder/patch-dmrgateway-hourly-0.2.9.py" "$ROOT_MNT/builder/"
chmod 0755 "$ROOT_MNT/builder/"*.py
'''
    s=s.replace(chroot_anchor,stage+chroot_anchor,1)
anchor="apt-get purge -y g++ make git libmosquitto-dev nlohmann-json3-dev"
if anchor not in s:
    raise SystemExit("0.2.9 builder: compile/purge anchor missing")
if "PU2PNY_OPTIONAL_GATEWAYS_0_2_9" not in s:
    block=f'''# PU2PNY_OPTIONAL_GATEWAYS_0_2_9
DG_COMMIT="{DMRGATEWAY_COMMIT}"
DG=/tmp/DMRGateway-029
rm -rf "$DG"
git init -q "$DG"; cd "$DG"
git remote add origin https://github.com/g4klx/DMRGateway.git
git fetch -q --depth=1 origin "$DG_COMMIT"; git checkout -q --detach FETCH_HEAD
python3 /builder/patch-dmrgateway-pu2pny-0.2.9.py "$DG"
python3 /builder/patch-dmrgateway-hourly-0.2.9.py "$DG"
make -j"$JOBS"
strip --strip-unneeded DMRGateway
install -D -m 0755 DMRGateway /usr/local/bin/DMRGateway
mkdir -p /usr/share/2pny/audio/dmrgateway /usr/share/2pny/upstream
cp -a Audio/. /usr/share/2pny/audio/dmrgateway/
printf '%s\n' "$DG_COMMIT" >/usr/share/2pny/upstream/DMRGateway.commit
cd /
rm -rf "$DG"

# Boost is needed only to compile DStarGateway. Install it after the larger
# MMDVM/Display builds, then remove it immediately to keep the target rootfs small.
apt-get install -y --no-install-recommends libboost-dev

DSTAR_COMMIT="{DSTAR_COMMIT}"
DSTAR=/tmp/DStarGateway-029
rm -rf "$DSTAR"
git init -q "$DSTAR"; cd "$DSTAR"
git remote add origin https://github.com/g4klx/DStarGateway.git
git fetch -q --depth=1 origin "$DSTAR_COMMIT"; git checkout -q --detach FETCH_HEAD
make -j"$JOBS" DStarGateway/dstargateway
strip --strip-unneeded DStarGateway/dstargateway
install -D -m 0755 DStarGateway/dstargateway /usr/local/bin/dstargateway
printf '%s\n' "$DSTAR_COMMIT" >/usr/share/2pny/upstream/DStarGateway.commit
cd /
rm -rf "$DSTAR"
apt-get purge -y libboost-dev
apt-get autoremove -y --purge

YSF_COMMIT="{YSF_COMMIT}"
YSF=/tmp/YSFClients-029
rm -rf "$YSF"
git init -q "$YSF"; cd "$YSF"
git remote add origin https://github.com/g4klx/YSFClients.git
git fetch -q --depth=1 origin "$YSF_COMMIT"; git checkout -q --detach FETCH_HEAD
make -C YSFGateway -j"$JOBS"
strip --strip-unneeded YSFGateway/YSFGateway
install -D -m 0755 YSFGateway/YSFGateway /usr/local/bin/YSFGateway
printf '%s\n' "$YSF_COMMIT" >/usr/share/2pny/upstream/YSFGateway.commit
cd /
rm -rf "$YSF"

P25_COMMIT="{P25_COMMIT}"
P25=/tmp/P25Clients-029
rm -rf "$P25"
git init -q "$P25"; cd "$P25"
git remote add origin https://github.com/g4klx/P25Clients.git
git fetch -q --depth=1 origin "$P25_COMMIT"; git checkout -q --detach FETCH_HEAD
make -C P25Gateway -j"$JOBS"
strip --strip-unneeded P25Gateway/P25Gateway
install -D -m 0755 P25Gateway/P25Gateway /usr/local/bin/P25Gateway
printf '%s\n' "$P25_COMMIT" >/usr/share/2pny/upstream/P25Gateway.commit
cd /
rm -rf "$P25"

NXDN_COMMIT="{NXDN_COMMIT}"
NXDN=/tmp/NXDNClients-029
rm -rf "$NXDN"
git init -q "$NXDN"; cd "$NXDN"
git remote add origin https://github.com/g4klx/NXDNClients.git
git fetch -q --depth=1 origin "$NXDN_COMMIT"; git checkout -q --detach FETCH_HEAD
make -C NXDNGateway -j"$JOBS"
strip --strip-unneeded NXDNGateway/NXDNGateway
install -D -m 0755 NXDNGateway/NXDNGateway /usr/local/bin/NXDNGateway
printf '%s\n' "$NXDN_COMMIT" >/usr/share/2pny/upstream/NXDNGateway.commit
cd /
rm -rf "$NXDN"

FLAGS_COMMIT="{FLAGS_COMMIT}"
FLAGS=/tmp/flag-icons-029
rm -rf "$FLAGS"
git init -q "$FLAGS"; cd "$FLAGS"
git remote add origin https://github.com/lipis/flag-icons.git
git fetch -q --depth=1 origin "$FLAGS_COMMIT"; git checkout -q --detach FETCH_HEAD
mkdir -p /usr/share/2pny/flags
cp -a flags/4x3 /usr/share/2pny/flags/
cp LICENSE /usr/share/2pny/flags/LICENSE-MIT
printf '%s\n' "$FLAGS_COMMIT" >/usr/share/2pny/upstream/flag-icons.commit
cd /
rm -rf "$FLAGS"

'''
    # Builder runs in chroot; expose patch files at /builder.
    s=s.replace(anchor,block+anchor,1)

# Make patch scripts visible inside the mounted/chroot tree.
overlay_builder=root/"rootfs-overlay/builder"
overlay_builder.mkdir(parents=True,exist_ok=True)
for name in ("patch-dmrgateway-pu2pny-0.2.9.py","patch-dmrgateway-hourly-0.2.9.py"):
    shutil.copy2(root/"builder"/name,overlay_builder/name)
    os.chmod(overlay_builder/name,0o755)

# Runtime dependencies needed by Display Core and local MQTT consumers.
old="apt-get install -y --no-install-recommends libmosquitto1 mosquitto mosquitto-clients openssh-server"
new="apt-get install -y --no-install-recommends libmosquitto1 mosquitto mosquitto-clients openssh-server python3-pil python3-smbus"
if old in s:s=s.replace(old,new,1)
elif "python3-pil" not in s:
    raise SystemExit("0.2.9 builder: runtime package anchor missing")
builder.write_text(s);os.chmod(builder,0o755)

# Release image must not contain user/runtime state.
for rel in (
 "rootfs-overlay/var/lib/2pny/provisioned","rootfs-overlay/var/lib/2pny/rf-configured",
 "rootfs-overlay/var/lib/2pny/rf-apply-state.json","rootfs-overlay/var/lib/2pny/network-radio.json",
 "rootfs-overlay/var/lib/2pny/network-connect.json","rootfs-overlay/var/lib/2pny/wifi-scan.json",
 "rootfs-overlay/var/lib/2pny/wifi-country","rootfs-overlay/var/lib/2pny/station/operators.sqlite",
 "rootfs-overlay/var/lib/2pny/station/operators.sqlite-wal","rootfs-overlay/var/lib/2pny/station/operators.sqlite-shm",
 "rootfs-overlay/run/2pny/live-state.json","rootfs-overlay/run/2pny/contacts.json",
):
    try:(root/rel).unlink()
    except FileNotFoundError:pass

# Source validation.
subprocess.run(["gofmt","-w",str(root/"src/2pnyd/main.go")],check=True)
for rel in (
 "rootfs-overlay/usr/local/sbin/2pny-network-switch","rootfs-overlay/usr/local/sbin/2pny-network-core",
 "rootfs-overlay/usr/local/sbin/2pny-hostfiles-update",
):
    subprocess.run(["bash","-n",str(root/rel)],check=True)
for rel in (
 "rootfs-overlay/usr/local/lib/2pny-live-core.py","rootfs-overlay/usr/local/sbin/2pny-station-worker",
 "rootfs-overlay/usr/local/sbin/2pny-display-core","rootfs-overlay/usr/local/sbin/2pny-display-apply",
 "rootfs-overlay/usr/local/sbin/2pny-server-catalog","rootfs-overlay/usr/local/sbin/2pny-protocol-network-apply",
 "rootfs-overlay/usr/local/libexec/2pny-dmr-apply","rootfs-overlay/usr/local/sbin/2pny-aprs",
):
    subprocess.run(["python3","-m","py_compile",str(root/rel)],check=True)
for base in (root/"rootfs-overlay/usr/local/lib",root/"rootfs-overlay/usr/local/sbin",root/"rootfs-overlay/usr/local/libexec"):
    cache=base/"__pycache__"
    if cache.exists():shutil.rmtree(cache)

main=(root/"src/2pnyd/main.go").read_text()
dash=(root/"rootfs-overlay/usr/share/2pny/dashboard.html").read_text()
wiz=(root/"rootfs-overlay/usr/share/2pny/wizard.html").read_text()
assert re.search(r'appVersion\s*=\s*"0\.2\.9-alpha"',main)
assert "/api/network/country" in main and '"/flags/"' in main
assert 'id="liveCard"' in dash and 'id="liveName"' in dash and "operatorView" in dash
assert "País / região do Wi" in wiz and "reconnectOverlay" in wiz
assert "RadioID" in (root/"rootfs-overlay/usr/local/sbin/2pny-station-worker").read_text()
assert "TG4000" in (root/"builder/patch-dmrgateway-pu2pny-0.2.9.py").read_text()
print("PU2PNY-OS 0.2.9 modular overlay applied")
