#!/usr/bin/env python3
"""PU2PNY display apply 0.3.16.

Two mutually-exclusive Nextion renderer modes are supported:
- pu2pny-modern-v2: MMDVMHost owns the modem serial transport while the
  PU2PNY Display Core sends vector commands through MQTT host/display-in.
- mmdvmhost-native: MMDVMHost owns both transport and native Nextion rendering.

No TFT/HMI is flashed by this helper.
"""
import configparser, json, os, shutil, subprocess, tempfile, time
from pathlib import Path

STATE=Path("/var/lib/2pny")
HW=STATE/"hardware-probe.json"
OVERRIDE=STATE/"display-override.json"
STATUS=STATE/"display-runtime.json"
SETTINGS=STATE/"display-settings.json"
DETECTION=STATE/"display-detection.json"
HOST=STATE/"mmdvm/MMDVM-Host.ini"
CORE="2pny-display-core.service"
LEGACY="2pny-display.service"
MMDVM="2pny-mmdvmhost.service"
MQTT="mosquitto.service"

def load(path):
    try:return json.loads(path.read_text())
    except Exception:return {}

def write_json(path,obj,mode=0o600):
    path.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(prefix="."+path.name+".",dir=str(path.parent))
    try:
        with os.fdopen(fd,"w") as f:
            json.dump(obj,f,ensure_ascii=False,indent=2);f.write("\n");f.flush();os.fsync(f.fileno())
        os.chmod(tmp,mode);os.replace(tmp,path)
    finally:
        try:os.unlink(tmp)
        except FileNotFoundError:pass

def ctl(*args):
    return subprocess.run(["systemctl",*args],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode==0

def active(unit):return ctl("is-active","--quiet",unit)

def mqtt_preflight():
    ctl("start",MQTT)
    p=subprocess.run(["/usr/local/sbin/2pny-mqtt-preflight","--quiet"],text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    if p.returncode:
        msg=(p.stderr or p.stdout or "MQTT local indisponível").strip()
        raise RuntimeError(msg)

def write_host(cp,backup):
    HOST.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(HOST,backup)
    fd,tmp=tempfile.mkstemp(prefix=".MMDVM-Host.display.",dir=str(HOST.parent))
    try:
        with os.fdopen(fd,"w") as f:cp.write(f,space_around_delimiters=False);f.flush();os.fsync(f.fileno())
        os.chmod(tmp,0o640)
        try:
            import grp;os.chown(tmp,0,grp.getgrnam("mmdvm").gr_gid)
        except Exception:pass
        os.replace(tmp,HOST)
    finally:
        try:os.unlink(tmp)
        except FileNotFoundError:pass

def restart_host_or_rollback(backup):
    if not active(MMDVM):return
    if not ctl("restart",MMDVM):
        shutil.copy2(backup,HOST);ctl("restart",MMDVM);raise RuntimeError("MMDVMHost não reiniciou; configuração anterior restaurada")
    end=time.monotonic()+8
    while time.monotonic()<end:
        if active(MMDVM):return
        time.sleep(.25)
    shutil.copy2(backup,HOST);ctl("restart",MMDVM)
    raise RuntimeError("MMDVMHost não permaneceu ativo; configuração anterior restaurada")

def host_config():
    if not HOST.exists():raise RuntimeError("MMDVM-Host.ini ausente")
    cp=configparser.ConfigParser(interpolation=None,strict=False);cp.optionxform=str;cp.read(HOST)
    if not cp.has_section("General"):cp.add_section("General")
    if not cp.has_section("Nextion"):cp.add_section("Nextion")
    return cp

def patch_native_nextion(layout):
    cp=host_config()
    cp.set("General","Display","Nextion")
    cp.set("Nextion","Port","modem")
    cp.set("Nextion","Brightness",cp.get("Nextion","Brightness",fallback="50"))
    cp.set("Nextion","DisplayClock","1");cp.set("Nextion","UTC","0")
    cp.set("Nextion","IdleBrightness",cp.get("Nextion","IdleBrightness",fallback="20"))
    cp.set("Nextion","ScreenLayout",str(layout))
    backup=HOST.with_name("MMDVM-Host.ini.display-backup")
    write_host(cp,backup)
    verify=host_config()
    if verify.get("General","Display",fallback="")!="Nextion" or verify.get("Nextion","Port",fallback="")!="modem" or verify.get("Nextion","ScreenLayout",fallback="")!=str(layout):
        shutil.copy2(backup,HOST)
        raise RuntimeError("MMDVMHost não confirmou o layout Nextion solicitado; configuração anterior restaurada")
    restart_host_or_rollback(backup)
    return backup

def patch_modern_transport():
    """Disable only MMDVMHost's native display renderer.

    MQTT subscription display-in remains active and CMMDVMHost::onDisplay()
    forwards the payload through writeSerialData(), so MMDVMHost still owns the
    physical modem port while PU2PNY is the single logical renderer.
    """
    cp=host_config()
    cp.remove_option("General","Display")
    backup=HOST.with_name("MMDVM-Host.ini.display-backup")
    write_host(cp,backup)
    mqtt_preflight()
    restart_host_or_rollback(backup)
    return backup

hw=load(HW);ov=load(OVERRIDE);m=hw.get("mmdvm") or {};d=hw.get("display") or {}
det=load(DETECTION);detected=[x for x in (det.get("displays") or []) if isinstance(x,dict) and x.get("detected") is True]
if detected:
    preferred=next((x for x in detected if x.get("class")=="nextion_mmdvm" and x.get("physical_confirmed") is True),None)
    if preferred:d=preferred
    elif not d:d=detected[0]
if ov.get("enabled") is False:
    ctl("disable","--now",LEGACY);ctl("disable","--now",CORE)
    write_json(STATUS,{"state":"disabled","active":False,"type":"none","writer":"none","message":"Display desativado pelo usuário.",
                       "updated":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime())},0o644)
    print("DISPLAY_DISABLED");raise SystemExit(0)

kind=""
if d.get("class")=="nextion":kind="nextion"
elif m.get("detected") and (d.get("class")=="nextion_mmdvm" or d.get("state")=="mmdvm_display_candidate" or ov.get("enabled")):kind="nextion_mmdvm"
elif str(d.get("address") or "").lower() in ("0x3c","0x3d"):kind="oled"
elif str(d.get("address") or "").lower() in ("0x27","0x3f"):kind="lcd"

if not kind:
    ctl("disable","--now",LEGACY);ctl("disable","--now",CORE)
    write_json(STATUS,{"state":"not_configured","active":False,"type":"none","writer":"none",
                       "message":"Nenhum display suportado foi identificado.",
                       "updated":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime())},0o644)
    print("DISPLAY_NOT_CONFIGURED");raise SystemExit(0)

requested=int(ov.get("layout") or 9)
if requested not in (9,2,3):requested=9
renderer=str(ov.get("renderer") or ("pu2pny-modern-v2" if requested==9 else "mmdvmhost-native")).strip().lower()
if renderer not in ("pu2pny-modern-v2","mmdvmhost-native"):renderer="pu2pny-modern-v2"
if requested in (2,3):renderer="mmdvmhost-native"
# DISPLAY-021: MMDVM-connected Nextion may have a valid host->display path even
# when modem firmware does not expose display->host transparent responses.
# COMOK stays the only bidirectional proof. Without it, enable only the writer
# and report TX-only/unconfirmed; never claim physical confirmation or flash HMI.
tx_only_unconfirmed=False
if kind=="nextion_mmdvm":
    tx_only_unconfirmed=d.get("physical_confirmed") is not True
    # Preserve an explicit native layout selection. Moderno V2 remains the
    # default when the user has not selected ON7LDS 2/3.
    if requested==9:renderer="pu2pny-modern-v2"
profile=str(ov.get("model_profile") or "auto")
resolution=str(ov.get("resolution") or "")
settings=load(SETTINGS)

if kind=="nextion_mmdvm" and renderer=="mmdvmhost-native":
    effective=requested if requested in (2,3) else 2
    ctl("disable","--now",LEGACY);ctl("disable","--now",CORE)
    patch_native_nextion(effective)
    d.update({"class":"nextion_mmdvm","port":"modem","auto_selected":True,
              "message":"Nextion via MMDVM controlada pelo renderer nativo do MMDVMHost."})
    hw["display"]=d;write_json(HW,hw)
    settings.update({"enabled":True,"driver":"mmdvmhost-nextion","renderer":"mmdvmhost-native","writer":"mmdvmhost-native",
                     "type":kind,"automatic":True,"model_profile":profile,"resolution":resolution,
                     "requested_layout":requested,"effective_layout":effective})
    write_json(SETTINGS,settings)
    write_json(STATUS,{"state":"active" if active(MMDVM) else "configured","active":active(MMDVM),
                       "type":kind,"driver":"MMDVMHost Nextion","renderer":"mmdvmhost-native","writer":"mmdvmhost-native",
                       "integration":"modem","layout":requested,"effective_layout":effective,
                       "model_profile":profile,"resolution":resolution,
                       "message":"Nextion ativa pelo renderer nativo do MMDVMHost; TFT/HMI preservado.",
                       "updated":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime())},0o644)
    print("DISPLAY_APPLY_OK");raise SystemExit(0)

# PU2PNY renderer: direct displays use their bus; Nextion/MMDVM uses MQTT.
ctl("disable","--now",LEGACY)
if kind=="nextion_mmdvm":
    patch_modern_transport()
settings.update({"enabled":True,"driver":"pu2pny-display-core","renderer":"pu2pny-modern-v2","writer":"pu2pny-display-core",
                 "type":kind,"automatic":True,"model_profile":profile,"resolution":resolution,
                 "requested_layout":9,"effective_layout":9,"physical_confirmed":bool(d.get("physical_confirmed"))})
write_json(SETTINGS,settings)
ctl("enable",CORE)
started=False
if (STATE/"rf-configured").exists() and active(MMDVM):
    if not ctl("restart",CORE):raise RuntimeError("PU2PNY Display Core não iniciou")
    end=time.monotonic()+6
    while time.monotonic()<end:
        if active(CORE):started=True;break
        time.sleep(.25)
    if not started:raise RuntimeError("PU2PNY Display Core não permaneceu ativo")
msg="PU2PNY Moderno V2 configurado; iniciará junto com o rádio."
if started:msg="PU2PNY Moderno V2 ativo."
state="active" if started else "configured"
if kind=="nextion_mmdvm" and tx_only_unconfirmed:
    state="tx_only_unconfirmed"
    msg=("Envio para a Nextion habilitado pela bridge MQTT do MMDVMHost; "
         "o retorno COMOK ainda não foi confirmado. Comunicação bidirecional segue não verificada.")
write_json(STATUS,{"state":state,"active":started,"type":kind,
                   "driver":"pu2pny-display-core","renderer":"pu2pny-modern-v2","writer":"pu2pny-display-core",
                   "integration":"mqtt-mmdvm" if kind=="nextion_mmdvm" else kind,"layout":9,"effective_layout":9,
                   "model_profile":profile,"resolution":resolution,"automatic":True,"physical_confirmed":bool(d.get("physical_confirmed")),
                   "message":msg,
                   "updated":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime())},0o644)
print("DISPLAY_APPLY_OK" if started else "DISPLAY_CONFIGURED")
