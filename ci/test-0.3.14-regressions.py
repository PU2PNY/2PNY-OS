#!/usr/bin/env python3
"""Software regression gates for PU2PNY-OS 0.3.14."""
from pathlib import Path
import importlib.util, socket, tempfile, threading

ROOT=Path(__file__).resolve().parents[1]
rf=(ROOT/"src/2pny-rf-apply-0.3.14").read_text()
mqtt_text=(ROOT/"src/2pny-mqtt-preflight-0.3.14.py").read_text()
mosq=(ROOT/"src/2pny-mosquitto-local-0.3.14.conf").read_text()
mosqsvc=(ROOT/"src/mosquitto-0.3.14.service").read_text()
mmdvmsvc=(ROOT/"src/2pny-mmdvmhost-0.3.13.service").read_text()
op=(ROOT/"src/2pny-operational-apply-0.3.14.py").read_text()
proto=(ROOT/"src/2pny-protocol-network-apply-all-0.3.14.py").read_text()
wiz=(ROOT/"src/wizard-0.3.14.html").read_text()
lang=(ROOT/"src/ui-language-0.3.14.js").read_text()

# Preserve the physical PASS from 0.3.13: phase A still proves UART first.
assert "[Log]\nMQTTLevel=0\nDisplayLevel=0" in rf
assert "mmdvmhost_bootstrap_failed" in rf
assert rf.index("if ! start_host; then") < rf.index("--ensure-service")
assert rf.index("--ensure-service") < rf.index("enable_operational_mqtt")
assert "SERIAL_LOCK=/run/2pny/mmdvm-serial.lock" in rf
assert "Requires=mosquitto.service" not in mmdvmsvc

# PROTO-020 deterministic local broker.
assert "listener 1883 127.0.0.1" in mosq
assert "protocol mqtt" in mosq
assert "allow_anonymous true" in mosq
assert "persistence false" in mosq
assert "ExecStart=/usr/sbin/mosquitto -c /etc/mosquitto/2pny-local.conf" in mosqsvc
assert "User=mosquitto" in mosqsvc and "Restart=on-failure" in mosqsvc
for marker in ("--ensure-service","--attempts","--delay","--service-wait","ensure_service","service_snapshot","mqtt_connect_packet","CONNACK"):
    assert marker in mqtt_text
assert "--ensure-service --attempts 12 --delay 0.4 --service-wait 10" in rf
assert '"--ensure-service","--attempts","12","--delay","0.4","--service-wait","10"' in op
assert '"--ensure-service","--attempts","12","--delay","0.4","--service-wait","10"' in proto

# WIZ-007: current form stays on step 3 and drafts never include secrets.
assert "saveBasicDraft(data)" in wiz
assert "resumeBasic=!alreadyProvisioned" in wiz
assert "clearAutoStep();step(3);localStorage.setItem('pu2pny-wizard-step','3')" in wiz
assert "clearBasicDraft();await loadConclusion();step(4)" in wiz
draft=wiz[wiz.index("function saveBasicDraft"):wiz.index("function clearBasicDraft")]
for secret in ("server_password","bm_api_key","server_options"):
    assert secret not in draft
assert "A última tentativa não foi concluída." in lang
assert "MQTT local não ficou pronto." in lang

# Protocol-level MQTT CONNECT/CONNACK still works.
spec=importlib.util.spec_from_file_location("mqtt_preflight",ROOT/"src/2pny-mqtt-preflight-0.3.14.py")
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)

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
ok,msg=mod.check({"kind":"tcp","host":"127.0.0.1","port":p,"username":"","password":""},attempts=1,delay=.05)
assert ok and "handshake MQTT confirmado" in msg

p=broker(b"\x20\x02\x00\x05")
ok,msg=mod.check({"kind":"tcp","host":"127.0.0.1","port":p,"username":"","password":""},attempts=1,delay=.05)
assert not ok and "não autorizado" in msg

# Deterministic service recovery logic without touching the real runner systemd.
class Proc:
    def __init__(self,code=0,out="",err=""):
        self.returncode=code;self.stdout=out;self.stderr=err
calls=[]
real_run=mod.subprocess.run
real_geteuid=mod.os.geteuid
try:
    def fake_run(args,**kwargs):
        calls.append(tuple(args))
        if args[:2]==["systemctl","show"]:
            return Proc(0,"ActiveState=active\nSubState=running\nResult=success\nExecMainStatus=0\n","")
        return Proc(0,"","")
    mod.subprocess.run=fake_run
    # Source CI runs unprivileged; only the systemctl behavior is under test.
    mod.os.geteuid=lambda:0
    ok,msg,snap=mod.ensure_service(1)
    assert ok and snap.get("ActiveState")=="active"
    assert ("systemctl","reset-failed","mosquitto.service") in calls
    assert ("systemctl","enable","mosquitto.service") in calls
    assert ("systemctl","start","mosquitto.service") in calls
finally:
    mod.subprocess.run=real_run
    mod.os.geteuid=real_geteuid

print("TEST_0314_REGRESSIONS_OK")
