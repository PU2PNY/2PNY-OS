#!/usr/bin/env python3
"""Software regression gates for PU2PNY-OS 0.3.13."""
from pathlib import Path
import importlib.util, re, socket, tempfile, threading

ROOT=Path(__file__).resolve().parents[1]
probe=(ROOT/"src/2pny-hardware-probe-0.3.12.py").read_text()
rf=(ROOT/"src/2pny-rf-apply-0.3.13").read_text()
mqtt_text=(ROOT/"src/2pny-mqtt-preflight-0.3.13.py").read_text()
service=(ROOT/"src/2pny-mmdvmhost-0.3.13.service").read_text()
dmr=(ROOT/"src/2pny-protocol-network-apply-0.3.13.py").read_text()
catalog=(ROOT/"src/2pny-server-catalog-0.3.13.py").read_text()
lang=(ROOT/"src/ui-language-0.3.13.js").read_text()
wiz=(ROOT/"src/wizard-0.3.13.html").read_text()
conf=(ROOT/"src/2pny-mosquitto-local-0.3.12.conf").read_text()

# Preserve the 0.3.12 UART ownership fix.
assert "mmdvm-serial.lock" in probe and "fcntl.flock" in probe
assert 'SERIAL_LOCK=/run/2pny/mmdvm-serial.lock' in rf and "flock -w 15 7" in rf
assert "UARTSpeed=$MODEM_BAUD" in rf

# RF-018: minimum MMDVM/UART proof first; operational MQTT second.
assert "[Log]\nMQTTLevel=0\nDisplayLevel=0" in rf
for marker in (
    "mmdvmhost_bootstrap_failed",
    "mqtt_preflight_failed_after_uart_ok",
    "mmdvmhost_mqtt_phase_failed",
    "enable_operational_mqtt",
    "rf-bootstrap.json",
):
    assert marker in rf
assert rf.index("if ! start_host; then") < rf.index("systemctl start mosquitto.service")
assert rf.index("systemctl start mosquitto.service") < rf.index("enable_operational_mqtt")

# The service preflight is unprivileged. It must skip publishing and must honor
# MQTTLevel=0 during phase A instead of turning a diagnostic write into RF fail.
assert "Requires=mosquitto.service" not in service
assert "Wants=systemd-udev-settle.service mosquitto.service" in service
assert "--no-publish --respect-log-level" in service
assert "--no-publish" in mqtt_text and "--respect-log-level" in mqtt_text
assert "mqtt_log_enabled" in mqtt_text

# Real broker/protocol validation remains mandatory for phase B.
assert "listener 1883 127.0.0.1" in conf and "allow_anonymous true" in conf
assert "mqtt_connect_packet" in mqtt_text and "CONNACK" in mqtt_text

# PROTO-019: TGIF uses the pinned DMRGateway rewrite model and never records the
# Security Key in public runtime state.
for marker in (
    "Name=TGIF_Network",
    'TGRewrite{idx}={s},1,2,1,9999998',
    'SrcRewrite{idx}=2,1,{s},1,9999998',
    'tgif_auth_mode="legacy" if password=="passw0rd" else "secured"',
    'Password="{password}"',
    '"auth_mode":tgif_auth_mode',
):
    assert marker in dmr
assert '"password":password' not in dmr.lower()
assert "Chave de segurança TGIF" in catalog

# UI-028: initial chooser remains multilingual, normal Portuguese wizard does not
# contain the reported generic English labels.
body_after_chooser=wiz
m=re.search(r'<div class="languagewelcome".*?</div>\s*</div>',wiz,re.S)
if m:
    body_after_chooser=wiz[:m.start()]+wiz[m.end():]
for forbidden in (
    "Senha do master",
    "Opções do master",
    ">Hotspot Security<",
    "O rádio precisa usar o mesmo Color Code.",
):
    assert forbidden not in body_after_chooser, forbidden
for required in (
    "Senha de segurança do hotspot",
    "Chave de segurança TGIF",
    "O rádio precisa usar o mesmo código de cor.",
    "pny-i18n-pending",
):
    assert required in wiz
for required in (
    "A MMDVM passou no teste básico",
    "TGIF Security Key",
    "document.documentElement.classList.remove('pny-i18n-pending')",
):
    assert required in lang

# Protocol-level MQTT handshake regression from 0.3.12.
spec=importlib.util.spec_from_file_location("mqtt_preflight",ROOT/"src/2pny-mqtt-preflight-0.3.13.py")
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)

with tempfile.TemporaryDirectory() as td:
    cfg=Path(td)/"MMDVM-Host.ini"
    mod.CONFIG=cfg
    cfg.write_text("[Log]\nMQTTLevel=0\n[MQTT]\nHost=127.0.0.1\nPort=1883\n")
    assert mod.mqtt_log_enabled() is False
    cfg.write_text("[Log]\nMQTTLevel=1\n[MQTT]\nHost=127.0.0.1\nPort=1883\n")
    assert mod.mqtt_log_enabled() is True

def broker(reply):
    srv=socket.socket();srv.bind(("127.0.0.1",0));srv.listen(1)
    port=srv.getsockname()[1]
    def run():
        c,_=srv.accept()
        try:
            data=c.recv(4096)
            assert data and data[0]==0x10
            c.sendall(reply)
        finally:
            c.close();srv.close()
    threading.Thread(target=run,daemon=True).start()
    return port

p=broker(b"\x20\x02\x00\x00")
ok,msg=mod.check({"kind":"tcp","host":"127.0.0.1","port":p,"username":"","password":""},attempts=1,delay=0)
assert ok and "handshake MQTT confirmado" in msg

p=broker(b"\x20\x02\x00\x05")
ok,msg=mod.check({"kind":"tcp","host":"127.0.0.1","port":p,"username":"","password":""},attempts=1,delay=0)
assert not ok and "não autorizado" in msg

print("TEST_0313_REGRESSIONS_OK")
