#!/usr/bin/env python3
from pathlib import Path
import os, shutil, subprocess, sys

root=Path(sys.argv[1]).resolve()
repo=Path(__file__).resolve().parents[1]
version="0.2.8-alpha"

def install(src,dst,mode):
    target=root/dst
    target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(repo/src,target)
    os.chmod(target,mode)

install("src/2pnyd-main-0.2.8.go","src/2pnyd/main.go",0o644)
install("src/2pny-live-core-0.2.8.py","rootfs-overlay/usr/local/lib/2pny-live-core.py",0o644)
install("src/2pny-station-worker-0.2.8.py","rootfs-overlay/usr/local/sbin/2pny-station-worker",0o755)
install("src/2pny-station-0.2.8.service","rootfs-overlay/etc/systemd/system/2pny-station.service",0o644)
install("src/dashboard-0.2.8.html","rootfs-overlay/usr/share/2pny/dashboard.html",0o644)
install("src/2pny-display-status-0.2.8.py","rootfs-overlay/usr/local/sbin/2pny-display-status",0o755)
install("src/2pny-display-boot-0.2.8.service","rootfs-overlay/etc/systemd/system/2pny-display-boot.service",0o644)

# Keep the proven 0.2.7 wizard/radio path, but report the new test image version.
wizard=root/"rootfs-overlay/usr/share/2pny/wizard.html"
if wizard.exists():
    text=wizard.read_text()
    text=text.replace("0.2.7-alpha",version)
    wizard.write_text(text)

(root/"rootfs-overlay/etc/2pny/version").write_text(version+"\n")

# Ensure resident live worker and early display boot are enabled.
wants=root/"rootfs-overlay/etc/systemd/system/multi-user.target.wants"
wants.mkdir(parents=True,exist_ok=True)
for service in ("2pny-station.service","2pny-display-boot.service"):
    link=wants/service
    if link.exists() or link.is_symlink():
        link.unlink()
    link.symlink_to("../"+service)

# Release images must not carry runtime state.
for rel in (
    "rootfs-overlay/run/2pny/live-state.json",
    "rootfs-overlay/var/lib/2pny/station/operators.sqlite",
    "rootfs-overlay/var/lib/2pny/station/operators.sqlite-wal",
    "rootfs-overlay/var/lib/2pny/station/operators.sqlite-shm",
):
    try:(root/rel).unlink()
    except FileNotFoundError:pass

subprocess.run(["gofmt","-w",str(root/"src/2pnyd/main.go")],check=True)
subprocess.run(["python3","-m","py_compile",
    str(root/"rootfs-overlay/usr/local/lib/2pny-live-core.py"),
    str(root/"rootfs-overlay/usr/local/sbin/2pny-station-worker"),
    str(root/"rootfs-overlay/usr/local/sbin/2pny-display-status")],check=True)
for base in (root/"rootfs-overlay/usr/local/lib",root/"rootfs-overlay/usr/local/sbin"):
    cache=base/"__pycache__"
    if cache.exists():shutil.rmtree(cache)

main=(root/"src/2pnyd/main.go").read_text()
dash=(root/"rootfs-overlay/usr/share/2pny/dashboard.html").read_text()
assert 'appVersion      = "0.2.8-alpha"' in main
assert "/api/live/events" in main
assert 'id="liveCard"' in dash
assert 'id="rxCard"' not in dash and 'id="txCard"' not in dash
assert "new EventSource('/api/live/events')" in dash
assert "0.2.8-alpha" in dash
print("PU2PNY-OS 0.2.8 alpha live/SSE overlay applied")
