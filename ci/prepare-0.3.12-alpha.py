#!/usr/bin/env python3
"""Apply PU2PNY-OS 0.3.12-alpha MMDVM/MQTT/i18n regression fixes after 0.3.11."""
from pathlib import Path
import os,re,shutil,subprocess,sys,tempfile

root=Path(sys.argv[1]).resolve()
repo=Path(__file__).resolve().parents[1]
version="0.3.12-alpha"

def install(src,dst,mode=0o644):
    target=root/dst
    target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(repo/src,target)
    os.chmod(target,mode)

install("src/2pnyd-main-0.3.12.go","src/2pnyd/main.go")
install("src/wizard-0.3.12.html","rootfs-overlay/usr/share/2pny/wizard.html")
install("src/ui-language-0.3.12.js","rootfs-overlay/usr/share/2pny/ui-language.js")
install("src/2pny-rf-apply-0.3.12","rootfs-overlay/usr/local/sbin/2pny-rf-apply",0o755)
install("src/2pny-hardware-probe-0.3.12.py","rootfs-overlay/usr/local/sbin/2pny-hardware-probe",0o755)
install("src/2pny-mqtt-preflight-0.3.12.py","rootfs-overlay/usr/local/sbin/2pny-mqtt-preflight",0o755)
install("src/2pny-mosquitto-local-0.3.12.conf","rootfs-overlay/etc/mosquitto/conf.d/2pny-local.conf",0o644)
(root/"rootfs-overlay/etc/2pny/version").write_text(version+"\n")

# RF-018: the image must contain the broker, not only libmosquitto.
builder=root/"builder/build-image.sh"
bs=builder.read_text()
ready="wpasupplicant rfkill wireless-regdb mosquitto libmosquitto1"
old="wpasupplicant rfkill wireless-regdb libmosquitto1"
if ready not in bs:
    if old not in bs:
        raise SystemExit("builder package anchor for mosquitto not found")
    bs=bs.replace(old,ready,1)
builder.write_text(bs)

subprocess.run(["gofmt","-w",str(root/"src/2pnyd/main.go")],check=True)
subprocess.run(["go","test",str(root/"src/2pnyd/main.go")],check=True)
subprocess.run(["bash","-n",str(root/"rootfs-overlay/usr/local/sbin/2pny-rf-apply")],check=True)
for rel in ("2pny-hardware-probe","2pny-mqtt-preflight"):
    subprocess.run(["python3","-m","py_compile",str(root/"rootfs-overlay/usr/local/sbin"/rel)],check=True)
subprocess.run(["node","--check",str(root/"rootfs-overlay/usr/share/2pny/ui-language.js")],check=True)
cache=root/"rootfs-overlay/usr/local/sbin/__pycache__"
if cache.exists():shutil.rmtree(cache)

wiz=(root/"rootfs-overlay/usr/share/2pny/wizard.html").read_text()
for body in re.findall(r"<script(?:\s[^>]*)?>(.*?)</script>",wiz,re.I|re.S):
    if not body.strip():continue
    with tempfile.NamedTemporaryFile("w",suffix=".js",delete=False) as tf:
        tf.write(body);name=tf.name
    try:subprocess.run(["node","--check",name],check=True)
    finally:os.unlink(name)

main=(root/"src/2pnyd/main.go").read_text()
rf=(root/"rootfs-overlay/usr/local/sbin/2pny-rf-apply").read_text()
probe=(root/"rootfs-overlay/usr/local/sbin/2pny-hardware-probe").read_text()
mqtt=(root/"rootfs-overlay/usr/local/sbin/2pny-mqtt-preflight").read_text()
lang=(root/"rootfs-overlay/usr/share/2pny/ui-language.js").read_text()
mosq=(root/"rootfs-overlay/etc/mosquitto/conf.d/2pny-local.conf").read_text()
service=(root/"rootfs-overlay/etc/systemd/system/2pny-mmdvmhost.service").read_text()

assert '"0.3.12-alpha"' in main
assert 'SERIAL_LOCK=/run/2pny/mmdvm-serial.lock' in rf and 'flock -w 15 7' in rf
assert 'mmdvm-serial.lock' in probe and 'fcntl.flock' in probe
assert 'mqtt_connect_packet' in mqtt and 'CONNACK' in mqtt
assert 'listener 1883 127.0.0.1' in mosq and 'allow_anonymous true' in mosq
assert ready in builder.read_text()
assert 'Requires=mosquitto.service' in service
assert 'ExecStartPre=/usr/local/sbin/2pny-mqtt-preflight --quiet' in service
assert 'scheduleHardwareAdvance' in wiz and 'Sistema Operacional de Rádio Digital' in wiz
assert 'Object.assign(D,' in lang and 'A MMDVM ainda está sendo verificada' in lang
print("PREPARE_0312_OK")
