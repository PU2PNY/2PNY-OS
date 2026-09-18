#!/usr/bin/env python3
import configparser, datetime, json, os, re, shutil, subprocess, sys, tempfile, time
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

if proto!="DMR": die(f"network module for {proto} is not enabled in 0.2.6 yet",10)
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

if not CONFIG.exists(): die("MMDVMHost config missing",3)
cp=configparser.ConfigParser(interpolation=None,strict=False)
cp.optionxform=str
try: cp.read(CONFIG)
except Exception: die("MMDVMHost config is invalid",3)

try:
    callsign=cp["General"]["Callsign"].strip()
    dmrid=cp["General"]["Id"].strip()
    rx=int(cp["Modem"]["RXFrequency"]); tx=int(cp["Modem"]["TXFrequency"])
    duplex=int(cp["General"].get("Duplex","0"))
except Exception: die("MMDVMHost identity/RF fields are incomplete",3)
if not re.fullmatch(r"\d{6,9}",dmrid): die("invalid DMR ID in RF configuration",3)
network_id=dmrid+essid if essid and len(dmrid)==7 else dmrid

slot1=slot in ("1","both")
slot2=slot in ("2","both")
if kind.lower()=="brandmeister" and not password:
    die("BrandMeister requires the Hotspot Security password")
if kind.lower()=="tgif" and not password:
    password="passw0rd"
if kind.lower()=="xlx" and not password:
    password="passw0rd"

BACKUPS.mkdir(parents=True,exist_ok=True)
GATEWAY_DIR.mkdir(parents=True,exist_ok=True)
stamp=datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
backup_dir=BACKUPS/stamp
backup_dir.mkdir(parents=True,exist_ok=True)
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
    "DMR":{"Enable":"1","ColorCode":str(color),"DumpTAData":"1"},
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
        if current=="DMR Network" and k in ("Address","Port","Password","Type","Options"):
            continue
    out.append(line)
if current is not None: flush(current)
for sec,items in sections.items():
    if sec in present: continue
    out+=["",f"[{sec}]"]+[f"{k}={v}" for k,v in items.items()]
host_text="\n".join(out)+"\n"

info_slots=("1" if slot1 else "0","1" if slot2 else "0")
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
Enabled=0

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
Slot={2 if slot=="both" else slot}
TG=6
Base=64000
Startup={reflector}
Relink=10
UserControl=1
Module={module}
Debug=0

[Dynamic TG Control]
Enable=1

[Remote Commands]
Enable=0
"""
else:
    xlx_hosts=""
    pass_lines=[]
    for s in ((1,2) if slot=="both" else (int(slot),)):
        pass_lines += [f"PassAllTG={s}",f"PassAllPC={s}"]
    name={"brandmeister":"BM","tgif":"TGIF_Network"}.get(kind.lower(),server.replace(" ","_"))
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
    atomic(CONFIG,host_text)
    atomic(GATEWAY,gateway_text)
    atomic(XLXHOSTS,xlx_hosts or "# no XLX selected\n")
    ctl("daemon-reload")
    ctl("enable",GW_SERVICE)
    if not ctl("restart",GW_SERVICE):
        raise RuntimeError("DMRGateway failed to start")
    time.sleep(1)
    if not service_active(GW_SERVICE):
        raise RuntimeError("DMRGateway did not remain active")
    if not ctl("restart",HOST_SERVICE):
        raise RuntimeError("MMDVMHost failed after enabling DMRGateway")
    time.sleep(2)
    if not service_active(HOST_SERVICE):
        raise RuntimeError("MMDVMHost did not remain active with DMRGateway")
except Exception as e:
    restore()
    die(f"{e}; configuration rolled back",4)

state={
    "protocol":"DMR","server_name":server,"address":address,"port":port,
    "kind":kind,"color_code":color,"slot":slot,"slot1":1 if slot1 else 0,
    "slot2":1 if slot2 else 0,"module":module if xlx_enabled else "",
    "essid":essid,"network_id":network_id,"state":"configured",
    "gateway":"DMRGateway","updated":datetime.datetime.now(datetime.timezone.utc).isoformat()
}
atomic_json(STATEFILE,state)

print(f"NETWORK_APPLY_OK protocol=DMR kind={kind} server={server} slot={slot} module={module or '-'}")
