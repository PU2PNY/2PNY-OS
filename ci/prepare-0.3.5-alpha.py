#!/usr/bin/env python3
from pathlib import Path
import os, shutil, subprocess, sys

root=Path(sys.argv[1]).resolve()
repo=Path(__file__).resolve().parents[1]
version="0.3.5-alpha"

def install(src,dst,mode):
    target=root/dst
    target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(repo/src,target)
    os.chmod(target,mode)

# 0.3.5 overlays the complete 0.3.4 image. RF/DMR binaries and the physically
# validated DMR path are intentionally not replaced here.
install("src/2pnyd-main-0.3.5.go","src/2pnyd/main.go",0o644)
install("src/wizard-0.3.5.html","rootfs-overlay/usr/share/2pny/wizard.html",0o644)
install("src/dashboard-0.3.5.html","rootfs-overlay/usr/share/2pny/dashboard.html",0o644)
install("src/internet-0.3.5.html","rootfs-overlay/usr/share/2pny/internet.html",0o644)
install("src/history-0.3.5.html","rootfs-overlay/usr/share/2pny/history.html",0o644)
install("src/system-0.3.5.html","rootfs-overlay/usr/share/2pny/system.html",0o644)
install("src/display-0.3.5.html","rootfs-overlay/usr/share/2pny/display.html",0o644)
install("src/aprs-0.3.5.html","rootfs-overlay/usr/share/2pny/aprs.html",0o644)
install("src/expert-0.3.5.html","rootfs-overlay/usr/share/2pny/expert.html",0o644)
install("src/ui-common-0.3.5.js","rootfs-overlay/usr/share/2pny/ui-common-0.3.0.js",0o644)

install("src/2pny-network-switch-0.3.5","rootfs-overlay/usr/local/sbin/2pny-network-switch",0o755)
install("src/2pny-network-core-0.3.5","rootfs-overlay/usr/local/sbin/2pny-network-core",0o755)
install("src/2pny-wifi-profiles-0.3.5","rootfs-overlay/usr/local/sbin/2pny-wifi-profiles",0o755)
install("src/2pny-protocol-network-apply-all-0.3.5.py","rootfs-overlay/usr/local/sbin/2pny-protocol-network-apply",0o755)
install("src/2pny-station-worker-0.3.5.py","rootfs-overlay/usr/local/sbin/2pny-station-worker",0o755)
install("src/2pny-netdiag-0.3.5.py","rootfs-overlay/usr/local/sbin/2pny-netdiag",0o755)
install("src/2pny-auto-maintenance-0.3.5","rootfs-overlay/usr/local/sbin/2pny-auto-maintenance",0o755)
install("src/2pny-display-core-0.3.5.py","rootfs-overlay/usr/local/sbin/2pny-display-core",0o755)
install("src/2pny-display-status-0.3.5.py","rootfs-overlay/usr/local/sbin/2pny-display-status",0o755)

(root/"rootfs-overlay/etc/2pny/version").write_text(version+"\n")

for rel in (
  "rootfs-overlay/usr/local/sbin/2pny-network-switch",
  "rootfs-overlay/usr/local/sbin/2pny-network-core",
  "rootfs-overlay/usr/local/sbin/2pny-wifi-profiles",
  "rootfs-overlay/usr/local/sbin/2pny-auto-maintenance",
):
    subprocess.run(["bash","-n",str(root/rel)],check=True)

for rel in (
  "rootfs-overlay/usr/local/sbin/2pny-protocol-network-apply",
  "rootfs-overlay/usr/local/sbin/2pny-station-worker",
  "rootfs-overlay/usr/local/sbin/2pny-netdiag",
  "rootfs-overlay/usr/local/sbin/2pny-display-core",
  "rootfs-overlay/usr/local/sbin/2pny-display-status",
):
    subprocess.run(["python3","-m","py_compile",str(root/rel)],check=True)
    cache=(root/rel).parent/"__pycache__"
    if cache.exists():shutil.rmtree(cache)

main=(root/"src/2pnyd/main.go").read_text()
wiz=(root/"rootfs-overlay/usr/share/2pny/wizard.html").read_text()
dash=(root/"rootfs-overlay/usr/share/2pny/dashboard.html").read_text()
internet=(root/"rootfs-overlay/usr/share/2pny/internet.html").read_text()
history=(root/"rootfs-overlay/usr/share/2pny/history.html").read_text()
system=(root/"rootfs-overlay/usr/share/2pny/system.html").read_text()
display=(root/"rootfs-overlay/usr/share/2pny/display.html").read_text()
common=(root/"rootfs-overlay/usr/share/2pny/ui-common-0.3.0.js").read_text()
apply=(root/"rootfs-overlay/usr/local/sbin/2pny-protocol-network-apply").read_text()
station=(root/"rootfs-overlay/usr/local/sbin/2pny-station-worker").read_text()
disp=(root/"rootfs-overlay/usr/local/sbin/2pny-display-core").read_text()

assert '"0.3.5-alpha"' in main
assert "2pny-wifi-profiles" in main and "/api/network/dns" in main
assert "space_around_delimiters=False" in apply
assert "network-runtime.json" in station and "module_tg" in station
assert "Bem-vindo / Welcome" in wiz and "scheduleHardwareAdvance" in wiz
assert "Módulo / TG" in dash and "TOT: corte automático" in dash
assert ("Wi‑Fi principal e reserva" in internet or "Wi-Fi principal e reserva" in internet) and "Usar Cloudflare" in internet
assert "Atividade 24h" in history
assert "Manutenção automática" in system and "Throttling" in system
assert "PU2PNY Moderno" in display
assert "pnyAprsToast" in common
assert "Iniciando / Starting" in disp and "TOT: corte em" in disp
print("PU2PNY-OS 0.3.5 corrective/feature overlay applied")
