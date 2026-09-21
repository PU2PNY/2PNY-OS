#!/usr/bin/env python3
"""Apply PU2PNY-OS 0.3.15-alpha focused MQTT-onboarding correction after 0.3.14."""
from pathlib import Path
import os,re,shutil,subprocess,sys

root=Path(sys.argv[1]).resolve()
repo=Path(__file__).resolve().parents[1]
version="0.3.15-alpha"

def install(src,dst,mode=0o644):
    target=root/dst
    target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(repo/src,target)
    os.chmod(target,mode)

# REL-008: strictly focused overlay. Do not replace Wi-Fi, wizard, TGIF helper,
# i18n, display, MQTT broker/preflight, RF detector, frequencies or offsets.
install("src/2pnyd-main-0.3.15.go","src/2pnyd/main.go")
install("src/2pny-rf-apply-0.3.15","rootfs-overlay/usr/local/sbin/2pny-rf-apply",0o755)
install("src/2pny-protocol-network-apply-all-0.3.15.py","rootfs-overlay/usr/local/sbin/2pny-protocol-network-apply",0o755)
(root/"rootfs-overlay/etc/2pny/version").write_text(version+"\n")

subprocess.run(["gofmt","-w",str(root/"src/2pnyd/main.go")],check=True)
subprocess.run(["go","test",str(root/"src/2pnyd/main.go")],check=True)
subprocess.run(["bash","-n",str(root/"rootfs-overlay/usr/local/sbin/2pny-rf-apply")],check=True)
subprocess.run(["python3","-m","py_compile",str(root/"rootfs-overlay/usr/local/sbin/2pny-protocol-network-apply")],check=True)
cache=root/"rootfs-overlay/usr/local/sbin/__pycache__"
if cache.exists():shutil.rmtree(cache)

main=(root/"src/2pnyd/main.go").read_text()
rf=(root/"rootfs-overlay/usr/local/sbin/2pny-rf-apply").read_text()
proto=(root/"rootfs-overlay/usr/local/sbin/2pny-protocol-network-apply").read_text()
dmr=(root/"rootfs-overlay/usr/local/libexec/2pny-dmr-apply").read_text()
wiz=(root/"rootfs-overlay/usr/share/2pny/wizard.html").read_text()
mqtt=(root/"rootfs-overlay/usr/local/sbin/2pny-mqtt-preflight").read_text()

assert '"0.3.15-alpha"' in main

# PROTO-021: exact functional boundary recovered from 0.3.6/0.3.8.
assert '[Log]\nMQTTLevel=0\nDisplayLevel=0' in rf
assert 'mmdvmhost_bootstrap_failed' in rf
assert 'RF_APPLY_OK' in rf
for forbidden in ('--ensure-service','enable_operational_mqtt','mqtt_preflight_failed_after_uart_ok','mmdvmhost_mqtt_phase_failed','operational_ok'):
    assert forbidden not in rf, forbidden

# DMR must delegate immediately, without a broker gate.
dmr_branch=proto[proto.index('if proto=="DMR":'):proto.index('server=q(server)',proto.index('if proto=="DMR":'))]
assert 'os.execv(DMR_HELPER' in dmr_branch
assert '2pny-mqtt-preflight' not in dmr_branch
assert '--ensure-service' not in dmr_branch

# The proven DMR helper itself keeps MQTT disabled and validates gateway/host.
assert '[Log]\nDisplayLevel=1\nMQTTLevel=0' in dmr
assert 'DMRGateway did not remain active' in dmr
assert 'MMDVMHost did not remain active with DMRGateway' in dmr
assert '2pny-mqtt-preflight' not in dmr

# Broker/preflight remain present for later features which actually enable MQTT.
assert 'mqtt_connect_packet' in mqtt and 'CONNACK' in mqtt

# WIZ-008 uses existing proven commit path; no new navigation shortcut.
assert "if(s.state==='applied')" in wiz
assert "await loadConclusion();step(4)" in wiz
assert "setTimeout(function(){location.href='/dashboard'},5000)" in wiz
assert 'os.WriteFile(provisionedFile' in main
assert 'writeRFApplyState("applied", done)' in main

print("PREPARE_0315_OK")
