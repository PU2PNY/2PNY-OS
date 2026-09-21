#!/usr/bin/env python3
"""Software regression gates for PU2PNY-OS 0.3.12."""
from pathlib import Path
import importlib.util, socket, tempfile, threading, time

ROOT=Path(__file__).resolve().parents[1]
probe=(ROOT/"src/2pny-hardware-probe-0.3.12.py").read_text()
rf=(ROOT/"src/2pny-rf-apply-0.3.12").read_text()
lang=(ROOT/"src/ui-language-0.3.12.js").read_text()
wiz=(ROOT/"src/wizard-0.3.12.html").read_text()
conf=(ROOT/"src/2pny-mosquitto-local-0.3.12.conf").read_text()

assert "mmdvm-serial.lock" in probe and "fcntl.flock" in probe
assert 'SERIAL_LOCK=/run/2pny/mmdvm-serial.lock' in rf and "flock -w 15 7" in rf
assert "UARTSpeed=$MODEM_BAUD" in rf
assert "MMDVMHost failed with detected baud" not in rf
assert "listener 1883 127.0.0.1" in conf and "allow_anonymous true" in conf
assert "Sistema Operacional de Rádio Digital" in wiz
assert "Digital Radio Operating System" not in wiz
assert "Object.assign(D," in lang
for phrase in (
    "MMDVM detectada. O assistente avançará automaticamente em 5 segundos.",
    "MMDVMHost não iniciou; a configuração anterior foi restaurada. O diagnóstico técnico foi salvo no Expert.",
    "A MMDVM ainda está sendo verificada; aguarde alguns segundos e tente novamente.",
):
    assert phrase in lang

spec=importlib.util.spec_from_file_location("mqtt_preflight",ROOT/"src/2pny-mqtt-preflight-0.3.12.py")
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
ok,msg=mod.check({"kind":"tcp","host":"127.0.0.1","port":p,"username":"","password":""},attempts=1,delay=0)
assert ok and "handshake MQTT confirmado" in msg

p=broker(b"\x20\x02\x00\x05")
ok,msg=mod.check({"kind":"tcp","host":"127.0.0.1","port":p,"username":"","password":""},attempts=1,delay=0)
assert not ok and "não autorizado" in msg
print("TEST_0312_REGRESSIONS_OK")
