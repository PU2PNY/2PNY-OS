#!/usr/bin/env python3
"""PU2PNY display apply 0.3.1.

The PU2PNY Display Core is authoritative.  The legacy MMDVM-Display service is
never allowed to compete with it.  Nextion through the modem is selected
automatically when the MMDVM display channel is available.
"""
import json, os, subprocess, time
from pathlib import Path

STATE=Path("/var/lib/2pny")
HW=STATE/"hardware-probe.json"
OVERRIDE=STATE/"display-override.json"
STATUS=STATE/"display-runtime.json"
SETTINGS=STATE/"display-settings.json"
CORE="2pny-display-core.service"
LEGACY="2pny-display.service"

def load(path):
    try:return json.loads(path.read_text())
    except Exception:return {}

def write_json(path,obj,mode=0o600):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+"\n")
    os.chmod(tmp,mode);os.replace(tmp,path)

def ctl(*args):
    return subprocess.run(["systemctl",*args],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode==0

def active(unit):return ctl("is-active","--quiet",unit)

hw=load(HW);ov=load(OVERRIDE);m=hw.get("mmdvm") or {};d=hw.get("display") or {}
if ov.get("enabled") is False:
    ctl("disable","--now",LEGACY);ctl("disable","--now",CORE)
    write_json(STATUS,{"state":"disabled","active":False,"type":"none","message":"Display desativado pelo usuário.",
                       "updated":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime())},0o644)
    print("DISPLAY_DISABLED");raise SystemExit(0)

kind=""
if d.get("class")=="nextion":
    kind="nextion"
elif d.get("class")=="nextion_mmdvm" or (d.get("state")=="mmdvm_display_candidate" and m.get("detected")):
    kind="nextion_mmdvm"
elif str(d.get("address") or "").lower() in ("0x3c","0x3d"):
    kind="oled"
elif str(d.get("address") or "").lower() in ("0x27","0x3f"):
    kind="lcd"

if not kind:
    ctl("disable","--now",LEGACY)
    write_json(STATUS,{"state":"not_configured","active":False,"type":"none",
                       "message":"Nenhum display suportado foi identificado.",
                       "updated":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime())},0o644)
    print("DISPLAY_NOT_CONFIGURED");raise SystemExit(0)

# PU2PNY renderer must be the only display writer.
ctl("disable","--now",LEGACY)
settings=load(SETTINGS)
settings.update({"enabled":True,"driver":"pu2pny-display-core","type":kind,"automatic":True})
write_json(SETTINGS,settings)

# Promote the safe MMDVM display channel to an automatic runtime selection.
if kind=="nextion_mmdvm":
    d.update({"class":"nextion_mmdvm","port":"modem","auto_selected":True,
              "message":"Nextion via MMDVM selecionada automaticamente pelo PU2PNY Display Core."})
    hw["display"]=d
    write_json(HW,hw)

ctl("enable",CORE)
started=False
if (STATE/"rf-configured").exists() and active("2pny-mmdvmhost.service"):
    ctl("restart",CORE);time.sleep(1.2);started=active(CORE)

msg="PU2PNY Display Core configurado; iniciará junto com o rádio."
if started:msg="PU2PNY Display Core ativo."
write_json(STATUS,{"state":"active" if started else "configured","active":started,"type":kind,
                   "driver":"pu2pny-display-core","integration":kind,"automatic":True,
                   "message":msg,"updated":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime())},0o644)
print("DISPLAY_APPLY_OK" if started else "DISPLAY_CONFIGURED")
