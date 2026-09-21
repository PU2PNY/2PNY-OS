#!/usr/bin/env python3
"""Apply PU2PNY-OS 0.3.10-alpha corrective overlay after 0.3.9."""
from pathlib import Path
import json, os, re, shutil, subprocess, sys, tempfile

root=Path(sys.argv[1]).resolve()
repo=Path(__file__).resolve().parents[1]
version="0.3.10-alpha"

def install(src,dst,mode=0o644):
    target=root/dst
    target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(repo/src,target)
    os.chmod(target,mode)

# Backend + pages. History and Direct remain inherited baselines.
install("src/2pnyd-main-0.3.10.go","src/2pnyd/main.go")
for src,dst in (
    ("src/ui-common-0.3.10.js","rootfs-overlay/usr/share/2pny/ui-common-0.3.0.js"),
    ("src/wizard-0.3.10.html","rootfs-overlay/usr/share/2pny/wizard.html"),
    ("src/hotspot-0.3.10.html","rootfs-overlay/usr/share/2pny/hotspot.html"),
    ("src/display-0.3.10.html","rootfs-overlay/usr/share/2pny/display.html"),
    ("src/expert-0.3.10.html","rootfs-overlay/usr/share/2pny/expert.html"),
):
    install(src,dst)

# Runtime helpers.
for src,dst in (
    ("src/2pny-protocol-network-apply-all-0.3.10.py","rootfs-overlay/usr/local/sbin/2pny-protocol-network-apply"),
    ("src/2pny-mqtt-preflight-0.3.10.py","rootfs-overlay/usr/local/sbin/2pny-mqtt-preflight"),
    ("src/2pny-operational-apply-0.3.10.py","rootfs-overlay/usr/local/sbin/2pny-operational-apply"),
    ("src/2pny-display-apply-0.3.10.py","rootfs-overlay/usr/local/sbin/2pny-display-apply"),
    ("src/2pny-display-core-0.3.10.py","rootfs-overlay/usr/local/sbin/2pny-display-core"),
    ("src/2pny-display-detector-0.3.9.py","rootfs-overlay/usr/local/sbin/2pny-display-detector"),
    ("src/2pny-display-bootstrap-0.3.9","rootfs-overlay/usr/local/sbin/2pny-display-bootstrap"),
):
    install(src,dst,0o755)

install("src/display-catalog-0.3.9.json","rootfs-overlay/usr/share/2pny/display-catalog.json")
for src,dst in (
    ("src/2pny-display-detect-0.3.9.service","rootfs-overlay/etc/systemd/system/2pny-display-detect.service"),
    ("src/2pny-display-detect-0.3.9.path","rootfs-overlay/etc/systemd/system/2pny-display-detect.path"),
    ("src/99-pu2pny-display-hotplug-0.3.9.rules","rootfs-overlay/etc/udev/rules.d/99-pu2pny-display-hotplug.rules"),
):
    install(src,dst)

(root/"rootfs-overlay/etc/2pny/version").write_text(version+"\n")

# Enable non-destructive boot/request detection. Do not enable any TFT flasher.
wants=root/"rootfs-overlay/etc/systemd/system/multi-user.target.wants"
wants.mkdir(parents=True,exist_ok=True)
for unit in ("2pny-display-detect.service","2pny-display-detect.path"):
    link=wants/unit
    if link.exists() or link.is_symlink():link.unlink()
    os.symlink("../"+unit,link)

# Syntax/compile gates.
subprocess.run(["gofmt","-w",str(root/"src/2pnyd/main.go")],check=True)
subprocess.run(["go","test",str(root/"src/2pnyd/main.go")],check=True)
subprocess.run(["python3","-m","py_compile",
    str(root/"rootfs-overlay/usr/local/sbin/2pny-protocol-network-apply"),
    str(root/"rootfs-overlay/usr/local/sbin/2pny-mqtt-preflight"),
    str(root/"rootfs-overlay/usr/local/sbin/2pny-operational-apply"),
    str(root/"rootfs-overlay/usr/local/sbin/2pny-display-apply"),
    str(root/"rootfs-overlay/usr/local/sbin/2pny-display-core"),
    str(root/"rootfs-overlay/usr/local/sbin/2pny-display-detector"),
],check=True)
subprocess.run(["bash","-n",str(root/"rootfs-overlay/usr/local/sbin/2pny-display-bootstrap")],check=True)
subprocess.run(["node","--check",str(root/"rootfs-overlay/usr/share/2pny/ui-common-0.3.0.js")],check=True)

for html in ("wizard.html","hotspot.html","display.html","expert.html"):
    txt=(root/"rootfs-overlay/usr/share/2pny"/html).read_text()
    for body in re.findall(r"<script(?:\s[^>]*)?>(.*?)</script>",txt,re.I|re.S):
        if not body.strip():continue
        with tempfile.NamedTemporaryFile("w",suffix=".js",delete=False) as tf:
            tf.write(body);name=tf.name
        try:subprocess.run(["node","--check",name],check=True)
        finally:os.unlink(name)

catalog=json.loads((root/"rootfs-overlay/usr/share/2pny/display-catalog.json").read_text())
assert catalog["policy"]["flash_requires_explicit_confirmation"] is True
assert catalog["policy"]["silent_tft_overwrite"] is False
for p in catalog["profiles"]:
    tft=p.get("tft")
    if tft:
        assert tft.get("status")=="unpublished" or (tft.get("url") and tft.get("sha256"))

# Structural gates for this corrective image.
main=(root/"src/2pnyd/main.go").read_text()
ui=(root/"rootfs-overlay/usr/share/2pny/ui-common-0.3.0.js").read_text()
wizard=(root/"rootfs-overlay/usr/share/2pny/wizard.html").read_text()
hotspot=(root/"rootfs-overlay/usr/share/2pny/hotspot.html").read_text()
display=(root/"rootfs-overlay/usr/share/2pny/display.html").read_text()
expert=(root/"rootfs-overlay/usr/share/2pny/expert.html").read_text()
proto=(root/"rootfs-overlay/usr/local/sbin/2pny-protocol-network-apply").read_text()
op=(root/"rootfs-overlay/usr/local/sbin/2pny-operational-apply").read_text()
mqtt=(root/"rootfs-overlay/usr/local/sbin/2pny-mqtt-preflight").read_text()
dapply=(root/"rootfs-overlay/usr/local/sbin/2pny-display-apply").read_text()
dcore=(root/"rootfs-overlay/usr/local/sbin/2pny-display-core").read_text()
det=(root/"rootfs-overlay/usr/local/sbin/2pny-display-detector").read_text()

assert '"0.3.10-alpha"' in main
assert '/api/display/detection' in main and '/api/diagnostics' in main
assert '"associating"' in main and '"associated"' in main and '"ipv4"' in main and '"route"' in main and '"dns"' in main
assert 'syncClock' in ui and "/api/system" in ui
assert 'wizardOperation' in wizard and "op.step(s.message" in wizard
assert 'sem iframe' in hotspot and '<iframe' not in hotspot.lower()
assert 'rendererSelect' in display and 'nextion-101-1024x600' in display and 'Nunca automático' in display
assert '/api/diagnostics' in expert and 'Diagnóstico operacional' in expert
assert 'local=cols[3]' in proto and 'wait_bridge' in proto and 'waiting_bridge' in proto
assert 'protocol-health.json' in proto and 'last-protocol-rollback.json' in proto
assert 'mqtt-preflight.json' in mqtt and 'MQTT local indisponível' in mqtt
assert 'mqtt_ready' in op and 'wait_bridge' in op and 'last-boot-restore.json' in op
assert 'pu2pny-modern-v2' in dapply and 'mmdvmhost-native' in dapply
assert 'host/display-in' in dcore and '1060' in dcore
assert 'connect' in det and 'comok' in det and 'pnyver.txt' in det
assert 'flashing' not in det.lower()
print("PREPARE_0310_OK")
