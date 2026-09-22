#!/usr/bin/env python3
"""Apply the focused PU2PNY-OS 0.3.20-alpha maintenance overlay.

0.3.19 is the protected functional base. Only REL-016 scoped maintenance is
installed here; all other files remain inherited byte-for-byte from 0.3.19.
"""
from pathlib import Path
import json, os, re, shutil, subprocess, sys

root=Path(sys.argv[1]).resolve()
repo=Path(__file__).resolve().parents[1]
version="0.3.20-alpha"

def install(src,dst,mode=0o644):
    target=root/dst
    target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(repo/src,target)
    os.chmod(target,mode)

files=[
("src/2pnyd-main-0.3.20.go","src/2pnyd/main.go",0o644),
("src/ui-common-0.3.20.js","rootfs-overlay/usr/share/2pny/ui-common-0.3.0.js",0o644),
("src/internet-0.3.20.html","rootfs-overlay/usr/share/2pny/internet.html",0o644),
("src/hotspot-0.3.20.html","rootfs-overlay/usr/share/2pny/hotspot.html",0o644),
("src/dashboard-0.3.20.html","rootfs-overlay/usr/share/2pny/dashboard.html",0o644),
("src/aprs-0.3.20.html","rootfs-overlay/usr/share/2pny/aprs.html",0o644),
("src/system-0.3.20.html","rootfs-overlay/usr/share/2pny/system.html",0o644),
("src/display-0.3.20.html","rootfs-overlay/usr/share/2pny/display.html",0o644),
("src/2pny-timezone-apply-0.3.20.py","rootfs-overlay/usr/local/sbin/2pny-timezone-apply",0o755),
("src/2pny-timezone-apply-0.3.20.path","rootfs-overlay/etc/systemd/system/2pny-timezone-apply.path",0o644),
("src/2pny-timezone-apply-0.3.20.service","rootfs-overlay/etc/systemd/system/2pny-timezone-apply.service",0o644),
("src/2pny-display-detector-0.3.20.py","rootfs-overlay/usr/local/sbin/2pny-display-detector",0o755),
("src/2pny-display-apply-0.3.20.py","rootfs-overlay/usr/local/sbin/2pny-display-apply",0o755),
("src/2pny-display-core-0.3.20.py","rootfs-overlay/usr/local/sbin/2pny-display-core",0o755),
("src/2pny-display-online-detect-0.3.20","rootfs-overlay/usr/local/sbin/2pny-display-online-detect",0o755),
("src/2pny-display-online-detect-0.3.20.service","rootfs-overlay/etc/systemd/system/2pny-display-online-detect.service",0o644),
("src/2pny-protocol-network-apply-all-0.3.20.py","rootfs-overlay/usr/local/sbin/2pny-protocol-network-apply",0o755),
("src/2pny-protocol-network-apply-0.3.20.py","rootfs-overlay/usr/local/libexec/2pny-dmr-apply",0o755),
("src/2pny-protocol-profiles-0.3.20.py","rootfs-overlay/usr/local/sbin/2pny-protocol-profiles",0o755),
("src/2pny-hostfiles-update-0.3.20","rootfs-overlay/usr/local/sbin/2pny-hostfiles-update",0o755),
("src/2pny-station-worker-0.3.20.py","rootfs-overlay/usr/local/sbin/2pny-station-worker",0o755),
("src/2pny-aprs-0.3.20.py","rootfs-overlay/usr/local/sbin/2pny-aprs",0o755),
("src/2pny-update-manager-0.3.20.py","rootfs-overlay/usr/local/sbin/2pny-update-manager",0o755),
]
for src,dst,mode in files:install(src,dst,mode)

# DMRGateway RF control patch: replace only the PU2PNY group-control patch;
# hourly/voice-arbiter patches stay inherited.
install("ci/patch-dmrgateway-pu2pny-0.3.20.py","builder/patch-dmrgateway-pu2pny-0.3.20.py",0o755)
install("ci/patch-dmrgateway-pu2pny-0.3.20.py","rootfs-overlay/builder/patch-dmrgateway-pu2pny-0.3.20.py",0o755)
builder=root/"builder/build-image.sh"
bs=builder.read_text()
if "patch-dmrgateway-pu2pny-0.2.9.py" in bs:
    bs=bs.replace("patch-dmrgateway-pu2pny-0.2.9.py","patch-dmrgateway-pu2pny-0.3.20.py")
elif "patch-dmrgateway-pu2pny-0.3.20.py" not in bs:
    raise SystemExit("0.3.20: DMRGateway PU2PNY patch anchor missing")
builder.write_text(bs);os.chmod(builder,0o755)

# Rebuild Direct core with the new RF autocall observer.
direct=root/"src/direct-core";direct.mkdir(parents=True,exist_ok=True)
direct_names=("direct_types.go","direct_session.go","direct_transport.go","direct_radio.go","direct_autocall.go","direct_main.go")
for name in direct_names:shutil.copy2(repo/"src/direct-core"/name,direct/name)
subprocess.run(["gofmt","-w",*(str(direct/n) for n in direct_names)],check=True)
subprocess.run(["go","test",*(str(direct/n) for n in direct_names)],check=True)
target=root/"rootfs-overlay/usr/local/bin/2pny-direct-core";target.parent.mkdir(parents=True,exist_ok=True)
env=os.environ.copy();env.update({"GOOS":"linux","GOARCH":"arm64","CGO_ENABLED":"0"})
subprocess.run(["go","build","-trimpath","-o",str(target),*(str(direct/n) for n in direct_names)],check=True,env=env)
os.chmod(target,0o755)

# Build-time D-Star catalog merge. Runtime updater/apply repeat the same merge,
# so radio-selected XLX destinations remain resolvable after list refreshes.
hosts=root/"rootfs-overlay/var/lib/2pny/hosts"
dstar=hosts/"DStar_Hosts.json";xlx=hosts/"XLXHosts.txt"
if dstar.exists() and xlx.exists():
    obj=json.loads(dstar.read_text());rows=obj.get("reflectors") if isinstance(obj,dict) else []
    merged={str(x.get("name")).upper():x for x in rows if isinstance(x,dict) and x.get("name")}
    for raw in xlx.read_text(errors="ignore").splitlines():
        line=raw.strip()
        if not line or line.startswith("#"):continue
        parts=[x.strip() for x in line.split(";")]
        if len(parts)<2 or not re.fullmatch(r"[A-Z0-9]{3}",parts[0].upper()) or not parts[1]:continue
        name="XLX"+parts[0].upper()
        merged[name]={"name":name,"reflector_type":"DCS","ipv4":parts[1]}
    dstar.write_text(json.dumps({"reflectors":[merged[k] for k in sorted(merged)]},ensure_ascii=False,indent=2)+"\n")

# Keep generic unit names; refresh wants symlinks deterministically.
wants=root/"rootfs-overlay/etc/systemd/system/multi-user.target.wants";wants.mkdir(parents=True,exist_ok=True)
for unit in ("2pny-timezone-apply.path","2pny-display-online-detect.service"):
    link=wants/unit
    if link.exists() or link.is_symlink():link.unlink()
    link.symlink_to("../"+unit)

(root/"rootfs-overlay/etc/2pny/version").write_text(version+"\n")

# Compile/syntax gates before image construction.
subprocess.run(["gofmt","-w",str(root/"src/2pnyd/main.go")],check=True)
subprocess.run(["go","test",str(root/"src/2pnyd/main.go")],check=True)
for p in (
 root/"rootfs-overlay/usr/local/sbin/2pny-timezone-apply",
 root/"rootfs-overlay/usr/local/sbin/2pny-display-detector",
 root/"rootfs-overlay/usr/local/sbin/2pny-display-apply",
 root/"rootfs-overlay/usr/local/sbin/2pny-display-core",
 root/"rootfs-overlay/usr/local/sbin/2pny-protocol-network-apply",
 root/"rootfs-overlay/usr/local/libexec/2pny-dmr-apply",
 root/"rootfs-overlay/usr/local/sbin/2pny-protocol-profiles",
 root/"rootfs-overlay/usr/local/sbin/2pny-station-worker",
 root/"rootfs-overlay/usr/local/sbin/2pny-aprs",
 root/"rootfs-overlay/usr/local/sbin/2pny-update-manager",
):
    subprocess.run(["python3","-m","py_compile",str(p)],check=True)
for p in (root/"rootfs-overlay/usr/local/sbin/2pny-display-online-detect",root/"rootfs-overlay/usr/local/sbin/2pny-hostfiles-update"):
    subprocess.run(["bash","-n",str(p)],check=True)
for cache in root.rglob("__pycache__"):shutil.rmtree(cache,ignore_errors=True)
subprocess.run(["node","--check",str(root/"rootfs-overlay/usr/share/2pny/ui-common-0.3.0.js")],check=True)

print("PREPARE_0320_OK")
