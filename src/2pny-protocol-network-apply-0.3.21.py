#!/usr/bin/env python3
import grp, configparser, datetime, json, os, re, shutil, subprocess, sys, tempfile, time
from pathlib import Path

CONFIG=Path("/var/lib/2pny/mmdvm/MMDVM-Host.ini")
STATE=Path("/var/lib/2pny")
GATEWAY_DIR=STATE/"dmr"
GATEWAY=GATEWAY_DIR/"DMRGateway.ini"
XLXHOSTS=GATEWAY_DIR/"XLXHosts.txt"
STATEFILE=STATE/"network-radio.json"
BACKUPS=STATE/"backups/network-radio"
HOST_SERVICE="2pny-mmdvmhost.service"
GW_SERVICE="2pny-dmrgateway.service"

def die(msg,code=2):
    print(msg,file=sys.stderr); raise SystemExit(code)
def run(args,check=False):
    p=subprocess.run(args,text=True,capture_output=True)
    if check and p.returncode:
        die((p.stderr or p.stdout or "command failed").strip(),4)
    return p
def service_active(name):
    return run(["systemctl","is-active","--quiet",name]).returncode==0
def ctl(*args):
    return run(["systemctl",*args]).returncode==0
def atomic(path,text,mode=0o640,group="mmdvm"):
    path.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(prefix="."+path.name+".",dir=str(path.parent))
    try:
        with os.fdopen(fd,"w") as f: f.write(text); f.flush(); os.fsync(f.fileno())
        os.chmod(tmp,mode)
        try:
            import grp
            os.chown(tmp,0,grp.getgrnam(group).gr_gid)
        except Exception: pass
        os.replace(tmp,path)
    finally:
        try: os.unlink(tmp)
        except FileNotFoundError: pass
def atomic_json(path,obj):
    atomic(path,json.dumps(obj,ensure_ascii=False,indent=2)+"\n",0o600)

if os.geteuid()!=0: die("root required",1)
if len(sys.argv)!=13:
    die("usage: 2pny-protocol-network-apply DMR SERVER ADDRESS PORT PASSWORD USEMODE COLOR SLOT MODULE ESSID KIND OPTIONS")

proto,server,address,port_s,password,usemode,color_s,slot,module,essid,kind,options=sys.argv[1:]
proto=proto.upper().strip(); server=server.strip(); address=address.strip(); usemode=usemode.lower().strip()
slot=slot.lower().strip(); module=module.upper().strip(); essid=essid.strip(); kind=kind.strip(); options=options.strip()

if proto!="DMR": die(f"network module for {proto} is not enabled by the DMR apply helper",10)
if not server or not address: die("server name/address required")
if len(server)>128 or len(address)>255 or len(password)>128 or len(options)>512: die("DMR field too long")
if any(any(c in v for c in "\r\n\x00") for v in (server,address,password,options)): die("control characters are not allowed in DMR fields")
if not re.fullmatch(r"[A-Za-z0-9._:-]+",address): die("invalid server address")
try: port=int(port_s)
except ValueError: die("invalid server port")
if not 1<=port<=65535: die("invalid server port")
try: color=int(color_s)
except ValueError: die("invalid DMR color code")
if not 0<=color<=15: die("invalid DMR color code")
if usemode not in ("hotspot","repeater"): die("invalid use mode")
if slot not in ("1","2","both"): die("DMR slot must be 1, 2 or both")
if usemode=="hotspot" and slot=="both": die("simplex hotspot must use one DMR slot")
if module and not re.fullmatch(r"[A-Z]",module): die("invalid XLX module")
if essid and not re.fullmatch(r"\d{2}",essid): die("ESSID must contain exactly two digits")
if essid=="00": essid=""
# PROTO-030: XLX uses the base DMR ID. A BrandMeister/other ESSID must never
# leak into an XLX profile after switching networks.
if kind.lower()=="xlx": essid=""

if not CONFIG.exists(): die("MMDVMHost config missing",3)
cp=configparser.ConfigParser(interpolation=None,strict=False)
cp.optionxform=str
try: cp.read(CONFIG)
except Exception: die("MMDVMHost config is invalid",3)

try:
    callsign=cp["General"]["Callsign"].strip()
    dmrid=cp["General"]["Id"].strip()
    rx=int(cp["Modem"]["RXFrequency"]); tx=int(cp["Modem"]["TXFrequency"])
except Exception: die("MMDVMHost identity/RF fields are incomplete",3)
if not re.fullmatch(r"\d{6,9}",dmrid): die("invalid DMR ID in RF configuration",3)
network_id=dmrid+essid if essid and len(dmrid)==7 and kind.lower()!="xlx" else dmrid

# RF-019 / PROTO-028: repeater mode is the source of truth for effective
# duplex. Local MMDVMHost<->DMRGateway transport must keep both timeslots open.
duplex=1 if usemode=="repeater" else 0
slot1=True if duplex else slot in ("1","both")
slot2=True if duplex else slot in ("2","both")
remote_slot="2" if slot=="both" else slot
tgif_auth_mode=""
if kind.lower()=="brandmeister" and not password:
    die("BrandMeister requires the Hotspot Security password")
if kind.lower()=="tgif":
    if not password:
        password="passw0rd"
    if '"' in password:
        die("TGIF Security Key contém caractere não suportado")
    tgif_auth_mode="legacy" if password=="passw0rd" else "secured"
if kind.lower()=="xlx" and not password:
    password="passw0rd"

# Service users need traversal through the private state directory.
service_gid=grp.getgrnam("mmdvm").gr_gid
for directory in (STATE, CONFIG.parent, GATEWAY_DIR):
    directory.mkdir(parents=True,exist_ok=True)
    os.chown(directory,0,service_gid)
    os.chmod(directory,0o750)
BACKUPS.mkdir(parents=True,exist_ok=True)
GATEWAY_DIR.mkdir(parents=True,exist_ok=True)
stamp=datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
backup_dir=Path(tempfile.mkdtemp(prefix=stamp+"-",dir=BACKUPS))
old_host_active=service_active(HOST_SERVICE)
old_gw_active=service_active(GW_SERVICE)
for p in (CONFIG,GATEWAY,XLXHOSTS,STATEFILE):
    if p.exists(): shutil.copy2(p,backup_dir/p.name)

def restore():
    for p in (CONFIG,GATEWAY,XLXHOSTS,STATEFILE):
        b=backup_dir/p.name
        if b.exists(): shutil.copy2(b,p)
        else:
            try: p.unlink()
            except FileNotFoundError: pass
    ctl("daemon-reload")
    if old_gw_active: ctl("restart",GW_SERVICE)
    else: ctl("stop",GW_SERVICE)
    if old_host_active: ctl("restart",HOST_SERVICE)

# Render MMDVMHost using only keys supported by the pinned host:
# MMDVMHost talks to DMRGateway locally; external master auth lives in DMRGateway.
sections={
    "General":{"Duplex":str(duplex)},
    "D-Star":{"Enable":"0"},
    "DMR":{"Enable":"1","ColorCode":str(color),"DumpTAData":"1"},
    "System Fusion":{"Enable":"0"},
    "P25":{"Enable":"0"},
    "NXDN":{"Enable":"0"},
    "DMR Network":{
        "Enable":"1","GatewayAddress":"127.0.0.1","GatewayPort":"62031",
        "LocalAddress":"127.0.0.1","LocalPort":"62032","Jitter":"360",
        "Slot1":"1" if slot1 else "0","Slot2":"1" if slot2 else "0","Debug":"0"
    },
    "D-Star Network":{"Enable":"0"},
    "System Fusion Network":{"Enable":"0"},
    "P25 Network":{"Enable":"0"},
    "NXDN Network":{"Enable":"0"},
}
# PROTO-036: keep the approved simplex transport byte-for-byte compatible.
# Only repeater/duplex mode makes the local DMRGateway contract explicit.
if duplex:
    sections["DMR Network"].update({
        "Type":"Gateway",
        "RemoteAddress":"127.0.0.1","RemotePort":"62031",
        "LocalAddress":"127.0.0.1","LocalPort":"62032"
    })
lines=CONFIG.read_text().splitlines()
out=[]; current=None; seen={k:set() for k in sections}; present=set()
def flush(sec):
    if sec in sections:
        for k,v in sections[sec].items():
            if k not in seen[sec]: out.append(f"{k}={v}"); seen[sec].add(k)
for line in lines:
    st=line.strip()
    if st.startswith("[") and st.endswith("]"):
        if current is not None: flush(current)
        current=st[1:-1]; present.add(current); out.append(line); continue
    if current in sections and "=" in st and not st.startswith("#"):
        k=st.split("=",1)[0].strip()
        if k in sections[current]:
            out.append(f"{k}={sections[current][k]}"); seen[current].add(k); continue
        # Remove invalid direct-master keys left by 0.2.5.
        if current=="DMR Network" and k in ("Address","Port","Password","Options"):
            continue
        if current=="DMR Network" and k=="Type" and not duplex:
            continue
    out.append(line)
if current is not None: flush(current)
for sec,items in sections.items():
    if sec in present: continue
    out+=["",f"[{sec}]"]+[f"{k}={v}" for k,v in items.items()]
host_text="\n".join(out)+"\n"

info_slots=("1" if slot1 else "0","1" if slot2 else "0")
voice_cfg={}
try: voice_cfg=json.loads((STATE/"voice-settings.json").read_text())
except Exception: voice_cfg={}
voice_enabled=bool(voice_cfg.get("enabled",True))
voice_lang=str(voice_cfg.get("language") or "pt").lower()
voice_language={"pt":"pt_PT","en":"en_GB","es":"es_ES"}.get(voice_lang,"pt_PT")
voice_dir="/usr/share/2pny/audio/dmrgateway"

base=f"""[General]
Id={dmrid}
Timeout=10
RFTimeout=10
NetTimeout=10
RptAddress=127.0.0.1
RptPort=62032
LocalAddress=127.0.0.1
LocalPort=62031
RuleTrace=0
Daemon=0
TrunkingEnabled=0
Debug=0

[Log]
DisplayLevel=1
MQTTLevel=0

[Voice]
Enabled={1 if voice_enabled else 0}
Language={voice_language}
Directory={voice_dir}

[Info]
Callsign={callsign}
TXFrequency={tx}
RXFrequency={rx}
Power=1
ColorCode={color}
Duplex={duplex}
Slot1={info_slots[0]}
Slot2={info_slots[1]}
Latitude=0.0
Longitude=0.0
Height=0
Location=PU2PNY-OS
Description=PU2PNY-OS DMR hotspot
URL=https://xlx026.net

"""
xlx_enabled=kind.lower()=="xlx"
if xlx_enabled:
    m=re.search(r"(\d{3})",server)
    if not m: die("XLX server name must contain the three-digit reflector number")
    reflector=m.group(1)
    if not module: module="C"
    room=4000+(ord(module)-ord("A")+1)
    xlx_hosts=f"{reflector};{address};{room}\n"
    gateway_text=base+f"""[XLX Network]
Enabled=1
Id={network_id}
File={XLXHOSTS}
Port={port}
Password={password}
ReloadTime=0
Slot={remote_slot}
TG=6
Base=64000
Startup={reflector}
Relink=10
UserControl=1
# PU2PNY RF group controls are patched into the pinned DMRGateway:
# TG4000=unlink, TG4001..4026=module A..Z, TG4099=status voice.
Module={module}
Debug=0

[Dynamic TG Control]
Enable=1

[Remote Commands]
Enable=0
"""
else:
    xlx_hosts=""
    # PROTO-028: in duplex both LOCAL RF timeslots must reach the gateway.
    # Keep each network's proven routing semantics instead of replacing them
    # with a generic pass-through rule.
    route_slots=(1,2) if duplex else ((1,2) if slot=="both" else (int(slot),))
    if kind.lower()=="tgif":
        # PROTO-019 baseline: TGIF network side uses TS2. Map every enabled
        # local RF slot to/from TGIF TS2; in duplex this means both TS1 and TS2
        # remain usable locally without changing TGIF's upstream contract.
        rewrite_lines=[]
        for idx,s in enumerate(route_slots):
            rewrite_lines += [
                f"TGRewrite{idx}={s},1,2,1,9999998",
                f"SrcRewrite{idx}=2,1,{s},1,9999998",
            ]
        gateway_text=base+f"""[XLX Network]
Enabled=0

[DMR Network 1]
Enabled=1
Name=TGIF_Network
Id={network_id}
{chr(10).join(rewrite_lines)}
Address={address}
Password="{password}"
Port={port}
Location=0
Debug=0

[Dynamic TG Control]
Enable=1

[Remote Commands]
Enable=0
"""
    else:
        pass_lines=[]
        for s in route_slots:
            pass_lines += [f"PassAllTG={s}",f"PassAllPC={s}"]
        name={"brandmeister":"BM"}.get(kind.lower(),server.replace(" ","_"))
        location="1" if kind.lower()=="brandmeister" else "0"
        optline=f"Options={options}\n" if options else ""
        gateway_text=base+f"""[XLX Network]
Enabled=0

[DMR Network 1]
Enabled=1
Name={name}
Id={network_id}
Address={address}
Port={port}
Password={password}
{optline}Location={location}
{chr(10).join(pass_lines)}
Debug=0

[Dynamic TG Control]
Enable=1

[Remote Commands]
Enable=0
"""

try:
    # Validate the exact candidates before touching live services.
    hc=configparser.ConfigParser(interpolation=None,strict=False);hc.optionxform=str;hc.read_string(host_text)
    if hc.get("General","Duplex",fallback="-1")!=str(duplex):
        raise RuntimeError("MMDVMHost Duplex candidate inconsistent")
    if duplex and (hc.get("DMR Network","Slot1",fallback="0")!="1" or hc.get("DMR Network","Slot2",fallback="0")!="1"):
        raise RuntimeError("DMR duplex candidate did not enable TS1/TS2 local transport")
    gi=configparser.ConfigParser(interpolation=None,strict=False);gi.optionxform=str;gi.read_string(gateway_text)
    if gi.get("Info","Duplex",fallback="-1")!=str(duplex):
        raise RuntimeError("DMRGateway Duplex candidate inconsistent")
    if duplex and (gi.get("Info","Slot1",fallback="0")!="1" or gi.get("Info","Slot2",fallback="0")!="1"):
        raise RuntimeError("DMRGateway duplex candidate did not advertise TS1/TS2")
    atomic(CONFIG,host_text)
    atomic(GATEWAY,gateway_text)
    atomic(XLXHOSTS,xlx_hosts or "# no XLX selected\n")
    ctl("daemon-reload")
    ctl("enable",GW_SERVICE)
    # RF-020: bring the local RF endpoint up first, then attach DMRGateway.
    # MMDVMHost owns the modem and UDP 62032; DMRGateway connects to it on
    # 62031. This mirrors the stable ordering used by the other gateways and
    # avoids a duplex startup window with a gateway bound before its RF peer.
    if not ctl("restart",HOST_SERVICE):
        raise RuntimeError("MMDVMHost failed while enabling DMR")
    time.sleep(2)
    if not service_active(HOST_SERVICE):
        detail=run(["journalctl","-u",HOST_SERVICE,"-n","18","--no-pager","-o","cat"]).stdout.strip()[-1600:]
        raise RuntimeError("MMDVMHost did not remain active for DMR"+(": "+detail if detail else ""))
    if not ctl("restart",GW_SERVICE):
        raise RuntimeError("DMRGateway failed to start")
    time.sleep(1)
    if not service_active(GW_SERVICE):
        raise RuntimeError("DMRGateway did not remain active")
except Exception as e:
    restore()
    die(f"{e}; configuration rolled back",4)

state={
    "protocol":"DMR","server_name":server,"address":address,"port":port,
    "kind":kind,"color_code":color,"slot":slot,"slot1":1 if slot1 else 0,
    "slot2":1 if slot2 else 0,"duplex":bool(duplex),"remote_slot":remote_slot if xlx_enabled else "",
    "module":module if xlx_enabled else "",
    "essid":essid,"network_id":network_id,"state":"configured",
    "gateway":"DMRGateway","auth_mode":tgif_auth_mode if kind.lower()=="tgif" else "",
    "voice_enabled":voice_enabled,"voice_language":voice_language,
    "local_transport":"gateway-explicit" if duplex else "simplex-protected",
    "updated":datetime.datetime.now(datetime.timezone.utc).isoformat()
}
atomic_json(STATEFILE,state)

print(f"NETWORK_APPLY_OK protocol=DMR kind={kind} server={server} slot={slot} module={module or '-'} auth={tgif_auth_mode or '-'}")

