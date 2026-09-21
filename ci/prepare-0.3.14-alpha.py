#!/usr/bin/env python3
"""Apply PU2PNY-OS 0.3.14-alpha MQTT/wizard corrective overlay after 0.3.13."""
from pathlib import Path
import os,re,shutil,subprocess,sys,tempfile

root=Path(sys.argv[1]).resolve()
repo=Path(__file__).resolve().parents[1]
version="0.3.14-alpha"

def install(src,dst,mode=0o644):
    target=root/dst
    target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(repo/src,target)
    os.chmod(target,mode)

# Keep the 0.3.12 Wi-Fi baseline and the 0.3.13 MMDVM bootstrap/TGIF work.
install("src/2pnyd-main-0.3.14.go","src/2pnyd/main.go")
install("src/wizard-0.3.14.html","rootfs-overlay/usr/share/2pny/wizard.html")
install("src/ui-language-0.3.14.js","rootfs-overlay/usr/share/2pny/ui-language.js")
install("src/2pny-rf-apply-0.3.14","rootfs-overlay/usr/local/sbin/2pny-rf-apply",0o755)
install("src/2pny-mqtt-preflight-0.3.14.py","rootfs-overlay/usr/local/sbin/2pny-mqtt-preflight",0o755)
install("src/2pny-operational-apply-0.3.14.py","rootfs-overlay/usr/local/sbin/2pny-operational-apply",0o755)
install("src/2pny-protocol-network-apply-all-0.3.14.py","rootfs-overlay/usr/local/sbin/2pny-protocol-network-apply",0o755)
install("src/2pny-mosquitto-local-0.3.14.conf","rootfs-overlay/etc/mosquitto/2pny-local.conf",0o644)
install("src/mosquitto-0.3.14.service","rootfs-overlay/etc/systemd/system/mosquitto.service",0o644)
(root/"rootfs-overlay/etc/2pny/version").write_text(version+"\n")

# The old include-based broker config is superseded by the deterministic
# single-purpose config used directly by the PU2PNY service.
old=root/"rootfs-overlay/etc/mosquitto/conf.d/2pny-local.conf"
if old.exists() or old.is_symlink():
    old.unlink()

# Ensure the PU2PNY broker unit is enabled in the final image independent of
# Debian package presets/chroot service policy.
wants=root/"rootfs-overlay/etc/systemd/system/multi-user.target.wants"
wants.mkdir(parents=True,exist_ok=True)
link=wants/"mosquitto.service"
if link.exists() or link.is_symlink():
    link.unlink()
link.symlink_to("../mosquitto.service")

# 0.3.12 already guarantees the real mosquitto package is installed after
# build-dependency cleanup. Keep that invariant.
builder=root/"builder/build-image.sh"
bs=builder.read_text()
assert "PU2PNY_MOSQUITTO_RUNTIME_0312" in bs
assert "apt-get install -y --no-install-recommends mosquitto" in bs

subprocess.run(["gofmt","-w",str(root/"src/2pnyd/main.go")],check=True)
subprocess.run(["go","test",str(root/"src/2pnyd/main.go")],check=True)
subprocess.run(["bash","-n",str(root/"rootfs-overlay/usr/local/sbin/2pny-rf-apply")],check=True)
for rel in (
    root/"rootfs-overlay/usr/local/sbin/2pny-mqtt-preflight",
    root/"rootfs-overlay/usr/local/sbin/2pny-operational-apply",
    root/"rootfs-overlay/usr/local/sbin/2pny-protocol-network-apply",
):
    subprocess.run(["python3","-m","py_compile",str(rel)],check=True)
for base in (root/"rootfs-overlay/usr/local/sbin",):
    cache=base/"__pycache__"
    if cache.exists():shutil.rmtree(cache)
subprocess.run(["node","--check",str(root/"rootfs-overlay/usr/share/2pny/ui-language.js")],check=True)

wiz=(root/"rootfs-overlay/usr/share/2pny/wizard.html").read_text()
for body in re.findall(r"<script(?:\s[^>]*)?>(.*?)</script>",wiz,re.I|re.S):
    if not body.strip():continue
    with tempfile.NamedTemporaryFile("w",suffix=".js",delete=False) as tf:
        tf.write(body);name=tf.name
    try:subprocess.run(["node","--check",name],check=True)
    finally:os.unlink(name)

main=(root/"src/2pnyd/main.go").read_text()
rf=(root/"rootfs-overlay/usr/local/sbin/2pny-rf-apply").read_text()
mqtt=(root/"rootfs-overlay/usr/local/sbin/2pny-mqtt-preflight").read_text()
op=(root/"rootfs-overlay/usr/local/sbin/2pny-operational-apply").read_text()
proto=(root/"rootfs-overlay/usr/local/sbin/2pny-protocol-network-apply").read_text()
lang=(root/"rootfs-overlay/usr/share/2pny/ui-language.js").read_text()
mosq=(root/"rootfs-overlay/etc/mosquitto/2pny-local.conf").read_text()
mosqsvc=(root/"rootfs-overlay/etc/systemd/system/mosquitto.service").read_text()
mmdvmsvc=(root/"rootfs-overlay/etc/systemd/system/2pny-mmdvmhost.service").read_text()

assert '"0.3.14-alpha"' in main

# Preserve the HW-PASS 0.3.13 phase-A design.
assert '[Log]\nMQTTLevel=0\nDisplayLevel=0' in rf
assert 'mmdvmhost_bootstrap_failed' in rf
assert 'SERIAL_LOCK=/run/2pny/mmdvm-serial.lock' in rf

# PROTO-020 deterministic broker + bounded real MQTT readiness.
assert 'listener 1883 127.0.0.1' in mosq
assert 'allow_anonymous true' in mosq and 'persistence false' in mosq
assert 'ExecStart=/usr/sbin/mosquitto -c /etc/mosquitto/2pny-local.conf' in mosqsvc
assert 'User=mosquitto' in mosqsvc and 'Restart=on-failure' in mosqsvc
assert link.is_symlink() and os.readlink(link)=="../mosquitto.service"
assert '--ensure-service' in mqtt and 'ensure_service' in mqtt
assert 'systemctl","reset-failed"' in mqtt and 'systemctl","start"' in mqtt
assert 'mqtt_connect_packet' in mqtt and 'CONNACK' in mqtt
assert '--ensure-service --attempts 12 --delay 0.4 --service-wait 10' in rf
assert '"--ensure-service","--attempts","12","--delay","0.4","--service-wait","10"' in op
assert '"--ensure-service","--attempts","12","--delay","0.4","--service-wait","10"' in proto

# MMDVMHost remains independent from a hard Requires during phase A.
assert 'Requires=mosquitto.service' not in mmdvmsvc
assert 'ExecStartPre=/usr/local/sbin/2pny-mqtt-preflight --quiet --no-publish --respect-log-level' in mmdvmsvc

# WIZ-007: failures remain in Configuração Básica and no secrets enter draft.
assert "saveBasicDraft(data)" in wiz and "step(3);localStorage.setItem('pu2pny-wizard-step','3')" in wiz
assert "resumeBasic=!alreadyProvisioned" in wiz
assert "clearBasicDraft();await loadConclusion();step(4)" in wiz
draft_block=wiz[wiz.index("function saveBasicDraft"):wiz.index("function clearBasicDraft")]
assert "server_password" not in draft_block and "bm_api_key" not in draft_block and "server_options" not in draft_block
assert "A última tentativa não foi concluída." in lang

print("PREPARE_0314_OK")
