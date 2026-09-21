#!/usr/bin/env python3
"""PU2PNY display apply 0.3.9.

For Nextion connected through the modem, MMDVMHost is the authoritative writer.
This avoids two display writers fighting over the modem transparent channel and
makes ON7LDS ScreenLayout=2/3 actually take effect.  Direct-serial Nextion,
OLED and LCD continue to use the PU2PNY Display Core.
"""
import configparser, json, os, shutil, subprocess, tempfile, time
from pathlib import Path

STATE=Path("/var/lib/2pny")
HW=STATE/"hardware-probe.json"
OVERRIDE=STATE/"display-override.json"
STATUS=STATE/"display-runtime.json"
SETTINGS=STATE/"display-settings.json"
HOST=STATE/"mmdvm/MMDVM-Host.ini"
CORE="2pny-display-core.service"
LEGACY="2pny-display.service"
MMDVM="2pny-mmdvmhost.service"

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

def patch_native_nextion(layout):
    if not HOST.exists():raise RuntimeError("MMDVM-Host.ini ausente")
    cp=configparser.ConfigParser(interpolation=None,strict=False);cp.optionxform=str
    cp.read(HOST)
    if not cp.has_section("General"):cp.add_section("General")
    if not cp.has_section("Nextion"):cp.add_section("Nextion")
    cp.set("General","Display","Nextion")
    cp.set("Nextion","Port","modem")
    cp.set("Nextion","Brightness",cp.get("Nextion","Brightness",fallback="50"))
    cp.set("Nextion","DisplayClock","1")
    cp.set("Nextion","UTC","0")
    cp.set("Nextion","IdleBrightness",cp.get("Nextion","IdleBrightness",fallback="20"))
    cp.set("Nextion","ScreenLayout",str(layout))
    backup=HOST.with_name("MMDVM-Host.ini.display-backup")
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
    verify=configparser.ConfigParser(interpolation=None,strict=False);verify.optionxform=str;verify.read(HOST)
    if verify.get("General","Display",fallback="")!="Nextion" or verify.get("Nextion","Port",fallback="")!="modem" or verify.get("Nextion","ScreenLayout",fallback="")!=str(layout):
        shutil.copy2(backup,HOST)
        raise RuntimeError("MMDVMHost não confirmou o layout Nextion solicitado; configuração anterior restaurada")
    if active(MMDVM):
        if not ctl("restart",MMDVM):
            shutil.copy2(backup,HOST);ctl("restart",MMDVM);raise RuntimeError("MMDVMHost não reiniciou; configuração anterior restaurada")
        time.sleep(2)
        if not active(MMDVM):
            shutil.copy2(backup,HOST);ctl("restart",MMDVM);raise RuntimeError("MMDVMHost não permaneceu ativo; configuração anterior restaurada")
    return backup

hw=load(HW);ov=load(OVERRIDE);m=hw.get("mmdvm") or {};d=hw.get("display") or {}
if ov.get("enabled") is False:
    ctl("disable","--now",LEGACY);ctl("disable","--now",CORE)
    write_json(STATUS,{"state":"disabled","active":False,"type":"none","message":"Display desativado pelo usuário.",
                       "updated":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime())},0o644)
    print("DISPLAY_DISABLED");raise SystemExit(0)

kind=""
if d.get("class")=="nextion":
    kind="nextion"
elif d.get("class")=="nextion_mmdvm" or (d.get("state")=="mmdvm_display_candidate" and m.get("detected")) or ov.get("enabled"):
    kind="nextion_mmdvm"
elif str(d.get("address") or "").lower() in ("0x3c","0x3d"):
    kind="oled"
elif str(d.get("address") or "").lower() in ("0x27","0x3f"):
    kind="lcd"

if not kind:
    ctl("disable","--now",LEGACY);ctl("disable","--now",CORE)
    write_json(STATUS,{"state":"not_configured","active":False,"type":"none",
                       "message":"Nenhum display suportado foi identificado.",
                       "updated":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime())},0o644)
    print("DISPLAY_NOT_CONFIGURED");raise SystemExit(0)

requested=int(ov.get("layout") or 9)
if requested not in (9,2,3):requested=9
settings=load(SETTINGS)

if kind=="nextion_mmdvm":
    # Stock/unknown HMI over the modem must be driven by MMDVMHost.  ScreenLayout
    # 2 and 3 are upstream-supported.  Moderno V2 requires a direct/compatible
    # HMI path; without flashing the user's TFT we fall back to ON7LDS layout 2.
    effective=requested if requested in (2,3) else 2
    ctl("disable","--now",LEGACY);ctl("disable","--now",CORE)
    patch_native_nextion(effective)
    d.update({"class":"nextion_mmdvm","port":"modem","auto_selected":True,
              "message":"Nextion via MMDVM controlada pelo renderer nativo do MMDVMHost."})
    hw["display"]=d;write_json(HW,hw)
    settings.update({"enabled":True,"driver":"mmdvmhost-nextion","type":kind,"automatic":True,
                     "requested_layout":requested,"effective_layout":effective})
    write_json(SETTINGS,settings)
    msg="Nextion ativa via MMDVMHost."
    if requested==9:
        msg+=" Moderno V2 preservou o HMI e usou ON7LDS como compatibilidade; nenhum TFT foi gravado."
    write_json(STATUS,{"state":"active" if active(MMDVM) else "configured","active":active(MMDVM),
                       "type":kind,"driver":"MMDVMHost Nextion","integration":"modem",
                       "layout":requested,"effective_layout":effective,"message":msg,
                       "updated":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime())},0o644)
    print("DISPLAY_APPLY_OK");raise SystemExit(0)

# Direct Nextion/OLED/LCD are rendered by PU2PNY Display Core.
ctl("disable","--now",LEGACY)
settings.update({"enabled":True,"driver":"pu2pny-display-core","type":kind,"automatic":True,
                 "requested_layout":requested,"effective_layout":requested})
write_json(SETTINGS,settings)
ctl("enable",CORE)
started=False
if (STATE/"rf-configured").exists() and active(MMDVM):
    ctl("restart",CORE);time.sleep(1.2);started=active(CORE)
msg="PU2PNY Display Core configurado; iniciará junto com o rádio."
if started:msg="PU2PNY Display Core ativo."
write_json(STATUS,{"state":"active" if started else "configured","active":started,"type":kind,
                   "driver":"pu2pny-display-core","integration":kind,"layout":requested,
                   "effective_layout":requested,"automatic":True,"message":msg,
                   "updated":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime())},0o644)
print("DISPLAY_APPLY_OK" if started else "DISPLAY_CONFIGURED")
