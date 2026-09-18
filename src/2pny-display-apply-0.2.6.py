#!/usr/bin/env python3
import grp, json, os, subprocess, sys, time
from pathlib import Path

STATE=Path("/var/lib/2pny")
HW=STATE/"hardware-probe.json"
OVERRIDE=STATE/"display-override.json"
DIR=STATE/"display"
CONF=DIR/"MMDVM-Display.ini"
STATUS=STATE/"display-runtime.json"
SERVICE="2pny-display.service"

def write_json(path,obj,mode=0o600):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+"\n")
    os.chmod(tmp,mode)
    os.replace(tmp,path)

def service(*args):
    return subprocess.run(["systemctl",*args],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode==0

def load(path):
    try: return json.loads(path.read_text())
    except Exception: return {}

hw=load(HW)
ov=load(OVERRIDE)
m=hw.get("mmdvm") or {}
d=hw.get("display") or {}

enabled=False
kind=""
port=""
speed=9600
layout=2
confidence="none"

if ov.get("enabled") is False:
    pass
elif ov.get("enabled") and m.get("detected"):
    enabled=True; kind="nextion_mmdvm"; port="modem"; confidence="manual"
    try: layout=int(ov.get("layout",2))
    except Exception: layout=2
elif d.get("detected") and d.get("class") in ("nextion","nextion_mmdvm"):
    enabled=True; kind=str(d.get("class")); confidence=str(d.get("confidence") or "protocol")
    if kind=="nextion_mmdvm":
        port="modem"
    else:
        port=str(d.get("port") or "")
        try: speed=int(d.get("baud") or 9600)
        except Exception: speed=9600
    try: layout=int(d.get("layout",2))
    except Exception: layout=2

if layout not in (0,2,3): layout=2

if not enabled or not port:
    service("disable","--now",SERVICE)
    try: CONF.unlink()
    except FileNotFoundError: pass
    write_json(STATUS,{
        "state":"not_configured","type":"none","active":False,
        "message":"Nenhuma Nextion confirmada ou habilitada.",
        "updated":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime())
    })
    print("DISPLAY_NOT_CONFIGURED")
    raise SystemExit(0)

for directory in (STATE, DIR):
    directory.mkdir(parents=True,exist_ok=True)
    os.chown(directory,0,grp.getgrnam("mmdvm").gr_gid)
    os.chmod(directory,0o750)
content=f"""[General]
Display=Nextion
TemperatureInF=0
Daemon=0

[Log]
MQTTLevel=1
DisplayLevel=1

[MQTT]
Host=127.0.0.1
Port=1883
Keepalive=60
Auth=0
Name=display
HostMQTTName=host
InfoMQTTName=info
HostConfName=MMDVM-Host

[Nextion]
Port={port}
Speed={speed}
Brightness=80
DisplayClock=1
UTC=0
ScreenLayout={layout}
IdleBrightness=30
"""
tmp=CONF.with_suffix(".tmp")
tmp.write_text(content)
os.chmod(tmp,0o640)
try:
    import grp
    os.chown(tmp,0,grp.getgrnam("mmdvm").gr_gid)
except Exception:
    pass
os.replace(tmp,CONF)

active=False
message="Nextion preparada; será iniciada quando o MMDVMHost estiver ativo."
if (STATE/"rf-configured").exists() and service("is-active","--quiet","2pny-mmdvmhost.service"):
    service("enable",SERVICE)
    service("restart",SERVICE)
    time.sleep(1)
    active=service("is-active","--quiet",SERVICE)
    message="MMDVM-Display ativo e conectado à Nextion." if active else "MMDVM-Display não permaneceu ativo; verifique layout/porta."

write_json(STATUS,{
    "state":"active" if active else "configured",
    "type":"Nextion","integration":kind,"port":port,"speed":speed,
    "layout":layout,"confidence":confidence,"active":active,
    "message":message,
    "updated":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime())
})
print("DISPLAY_APPLY_OK" if active else "DISPLAY_CONFIGURED")

