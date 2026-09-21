#!/usr/bin/env python3
"""Apply PU2PNY-OS 0.3.13-alpha corrective overlay after 0.3.12."""
from pathlib import Path
import os,re,shutil,subprocess,sys,tempfile

root=Path(sys.argv[1]).resolve()
repo=Path(__file__).resolve().parents[1]
version="0.3.13-alpha"

def install(src,dst,mode=0o644):
    target=root/dst
    target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(repo/src,target)
    os.chmod(target,mode)

# Narrow corrective overlay. Wi-Fi/network onboarding files are intentionally
# not replaced here because 0.3.12 received HW PASS for that flow.
install("src/2pnyd-main-0.3.13.go","src/2pnyd/main.go")
install("src/wizard-0.3.13.html","rootfs-overlay/usr/share/2pny/wizard.html")
install("src/ui-language-0.3.13.js","rootfs-overlay/usr/share/2pny/ui-language.js")
install("src/2pny-rf-apply-0.3.13","rootfs-overlay/usr/local/sbin/2pny-rf-apply",0o755)
install("src/2pny-mqtt-preflight-0.3.13.py","rootfs-overlay/usr/local/sbin/2pny-mqtt-preflight",0o755)
install("src/2pny-mmdvmhost-0.3.13.service","rootfs-overlay/etc/systemd/system/2pny-mmdvmhost.service")
install("src/2pny-protocol-network-apply-0.3.13.py","rootfs-overlay/usr/local/libexec/2pny-dmr-apply",0o755)
install("src/2pny-server-catalog-0.3.13.py","rootfs-overlay/usr/local/sbin/2pny-server-catalog",0o755)
(root/"rootfs-overlay/etc/2pny/version").write_text(version+"\n")

# Inherited 0.3.12 assets remain authoritative for detector/broker config.
# Do not remove the real local Mosquitto runtime added by the previous overlay.
builder=root/"builder/build-image.sh"
bs=builder.read_text()
assert "PU2PNY_MOSQUITTO_RUNTIME_0312" in bs
assert "apt-get install -y --no-install-recommends mosquitto" in bs

subprocess.run(["gofmt","-w",str(root/"src/2pnyd/main.go")],check=True)
subprocess.run(["go","test",str(root/"src/2pnyd/main.go")],check=True)
subprocess.run(["bash","-n",str(root/"rootfs-overlay/usr/local/sbin/2pny-rf-apply")],check=True)
for rel in (
    root/"rootfs-overlay/usr/local/sbin/2pny-mqtt-preflight",
    root/"rootfs-overlay/usr/local/sbin/2pny-server-catalog",
    root/"rootfs-overlay/usr/local/libexec/2pny-dmr-apply",
):
    subprocess.run(["python3","-m","py_compile",str(rel)],check=True)
for base in (
    root/"rootfs-overlay/usr/local/sbin",
    root/"rootfs-overlay/usr/local/libexec",
):
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
dmr=(root/"rootfs-overlay/usr/local/libexec/2pny-dmr-apply").read_text()
catalog=(root/"rootfs-overlay/usr/local/sbin/2pny-server-catalog").read_text()
lang=(root/"rootfs-overlay/usr/share/2pny/ui-language.js").read_text()
service=(root/"rootfs-overlay/etc/systemd/system/2pny-mmdvmhost.service").read_text()
mosq=(root/"rootfs-overlay/etc/mosquitto/conf.d/2pny-local.conf").read_text()

assert '"0.3.13-alpha"' in main

# RF-017 remains: UART ownership lock is preserved.
assert 'SERIAL_LOCK=/run/2pny/mmdvm-serial.lock' in rf and 'flock -w 15 7' in rf

# RF-018: first start is the proven minimal RF/UART bootstrap, then MQTT phase.
assert '[Log]\nMQTTLevel=0\nDisplayLevel=0' in rf
assert 'mmdvmhost_bootstrap_failed' in rf
assert 'mqtt_preflight_failed_after_uart_ok' in rf
assert 'mmdvmhost_mqtt_phase_failed' in rf
assert 'enable_operational_mqtt' in rf
assert 'rf-bootstrap.json' in rf

# Systemd must not make Mosquitto a hard dependency during phase A, and its
# unprivileged preflight must not try to write root-owned runtime diagnostics.
assert 'Wants=systemd-udev-settle.service mosquitto.service' in service
assert 'Requires=mosquitto.service' not in service
assert 'ExecStartPre=/usr/local/sbin/2pny-mqtt-preflight --quiet --no-publish --respect-log-level' in service
assert '--no-publish' in mqtt and '--respect-log-level' in mqtt and 'mqtt_log_enabled' in mqtt
assert 'mqtt_connect_packet' in mqtt and 'CONNACK' in mqtt
assert 'listener 1883 127.0.0.1' in mosq and 'allow_anonymous true' in mosq

# PROTO-019: explicit TGIF template from the pinned DMRGateway contract.
assert 'Name=TGIF_Network' in dmr
assert 'TGRewrite{idx}={s},1,2,1,9999998' in dmr
assert 'SrcRewrite{idx}=2,1,{s},1,9999998' in dmr
assert 'tgif_auth_mode="legacy" if password=="passw0rd" else "secured"' in dmr
assert 'Password="{password}"' in dmr
assert '"auth_mode":tgif_auth_mode' in dmr
assert 'Chave de segurança TGIF' in catalog

# UI-028: Portuguese base contains no generic English credential labels and
# translation catalog contains exact PT/EN/ES entries for this corrective flow.
for forbidden in ('Senha do master','Opções do master','Hotspot Security</','O rádio precisa usar o mesmo Color Code.'):
    assert forbidden not in wiz, forbidden
for required in ('Chave de segurança TGIF','Senha de segurança do hotspot','O rádio precisa usar o mesmo código de cor.','pny-i18n-pending'):
    assert required in wiz, required
for required in ('TGIF Security Key','A MMDVM passou no teste básico','document.documentElement.classList.remove'):
    assert required in lang, required

print("PREPARE_0313_OK")
