#!/usr/bin/env python3
"""Apply PU2PNY non-DMR protocol/gateway configuration transactionally.

DMR is delegated to the physically-proven DMR helper.  D-Star, YSF/C4FM,
P25, NXDN and POCSAG/DAPNET get their own pinned upstream gateways and local loopback ports.
"""
import configparser, datetime, grp, json, os, re, shutil, subprocess, sys, tempfile, time
from pathlib import Path

STATE=Path("/var/lib/2pny")
HOST=STATE/"mmdvm/MMDVM-Host.ini"
STATEFILE=STATE/"network-radio.json"
BACKUPS=STATE/"backups/protocol"
DMR_HELPER="/usr/local/libexec/2pny-dmr-apply"
SERVICES={
 "DMR":"2pny-dmrgateway.service","DSTAR":"2pny-dstargateway.service",
 "YSF":"2pny-ysfgateway.service","P25":"2pny-p25gateway.service","NXDN":"2pny-nxdngateway.service",
 "POCSAG":"2pny-dapnetgateway.service",
}

def die(msg,code=2):
    print(msg,file=sys.stderr);raise SystemExit(code)
def run(*args):
    return subprocess.run(list(args),stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
def active(unit):return run("systemctl","is-active","--quiet",unit).returncode==0
def ctl(*args):return run("systemctl",*args).returncode==0
def group_gid(name):
    try:return grp.getgrnam(name).gr_gid
    except KeyError:die(f"required group missing: {name}",1)

def atomic(path,text,mode=0o640,group=None):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(prefix="."+path.name+".",dir=str(path.parent))
    try:
        with os.fdopen(fd,"w") as f:f.write(text);f.flush();os.fsync(f.fileno())
        os.chmod(tmp,mode)
        if group is not None: os.chown(tmp,0,group_gid(group))
        os.replace(tmp,path)
    finally:
        try:os.unlink(tmp)
        except FileNotFoundError:pass

def normalize_host_permissions():
    HOST.parent.mkdir(parents=True,exist_ok=True)
    gid=group_gid("mmdvm")
    os.chown(HOST.parent,0,gid);os.chmod(HOST.parent,0o750)
    if HOST.exists():
        os.chown(HOST,0,gid);os.chmod(HOST,0o640)
    st=HOST.stat()
    if st.st_gid!=gid or (st.st_mode & 0o040)==0:
        raise RuntimeError("MMDVMHost config is not readable by group mmdvm")

def atomic_json(path,obj):atomic(path,json.dumps(obj,ensure_ascii=False,indent=2)+"\n",0o600)
def q(v):
    v=str(v or "").replace("\r"," ").replace("\n"," ").replace("\x00"," ")
    return v[:180]
def setsec(cp,name,values):
    if not cp.has_section(name):cp.add_section(name)
    for k,v in values.items():cp.set(name,k,str(v))
def gateway_paths(proto):
    return {
      "DSTAR":[STATE/"dstar/DStarGateway.ini"],
      "YSF":[STATE/"ysf/YSFGateway.ini",STATE/"ysf/YSFHosts.json",STATE/"ysf/FCSRooms.txt"],
      "P25":[STATE/"p25/P25Gateway.ini",STATE/"p25/P25Hosts.json"],
      "NXDN":[STATE/"nxdn/NXDNGateway.ini",STATE/"nxdn/NXDNHosts.json"],
      "POCSAG":[STATE/"pocsag/DAPNETGateway.ini"],
    }.get(proto,[])

if os.geteuid()!=0:die("root required",1)
if len(sys.argv)!=13:die("usage: apply PROTO SERVER ADDRESS PORT PASSWORD USEMODE COLOR SLOT MODULE ESSID KIND OPTIONS")
proto,server,address,port_s,password,usemode,color,slot,module,essid,kind,options=sys.argv[1:]
proto=proto.upper().replace("-","").strip()
if proto=="DSTAR":proto="DSTAR"
if proto=="C4FM":proto="YSF"
if proto not in SERVICES:die("unsupported protocol")
if proto=="DMR":
    os.execv(DMR_HELPER,[DMR_HELPER]+sys.argv[1:])

server=q(server).strip();address=q(address).strip();password=q(password).strip();kind=q(kind).strip();module=q(module).upper().strip()
if not HOST.exists():die("MMDVMHost config missing",3)
if proto=="DSTAR" and (not module or not re.fullmatch(r"[A-Z]",module)):die("D-Star module A-Z required")
if proto=="POCSAG" and not password:die("DAPNET AuthKey required")
try:port=int(port_s or 0)
except ValueError:port=0
if port<0 or port>65535:die("invalid port")

cp=configparser.ConfigParser(interpolation=None,strict=False);cp.optionxform=str
try:
    cp.read(HOST)
    callsign=cp["General"]["Callsign"].strip().upper()
    radioid=cp["General"]["Id"].strip()
    rx=int(cp["Modem"]["RXFrequency"]);tx=int(cp["Modem"]["TXFrequency"])
except Exception:die("MMDVMHost identity/RF config incomplete",3)

stamp=datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
backup=BACKUPS/stamp;backup.mkdir(parents=True,exist_ok=True)
shutil.copy2(HOST,backup/"MMDVM-Host.ini")
if STATEFILE.exists():shutil.copy2(STATEFILE,backup/"network-radio.json")
old_active={p:active(s) for p,s in SERVICES.items()}
old_enabled={p:run("systemctl","is-enabled","--quiet",svc).returncode==0 for p,svc in SERVICES.items()}
old_host_active=active("2pny-mmdvmhost.service")
for p in gateway_paths(proto):
    if p.exists():shutil.copy2(p,backup/p.name)

def restore():
    if (backup/"MMDVM-Host.ini").exists():
        shutil.copy2(backup/"MMDVM-Host.ini",HOST)
        normalize_host_permissions()
    if (backup/"network-radio.json").exists():shutil.copy2(backup/"network-radio.json",STATEFILE)
    for p in gateway_paths(proto):
        b=backup/p.name
        if b.exists():p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(b,p)
    for p,s in SERVICES.items():
        ctl("enable" if old_enabled[p] else "disable",s)
        ctl("stop",s)
    # Restore the radio engine deterministically before restoring the previous
    # network gateway.  Do not depend on systemd's restart-on-failure race.
    if old_host_active:
        ctl("restart","2pny-mmdvmhost.service")
        time.sleep(1.0)
    else:
        ctl("stop","2pny-mmdvmhost.service")
    for p,s in SERVICES.items():
        if old_active[p]:ctl("restart",s)

def mqtt_preflight():
    # The apply helper runs as root. Start the local-only broker if it is
    # installed but inactive, then prove the configured endpoint is reachable.
    ctl("start","mosquitto.service")
    p=run("/usr/local/sbin/2pny-mqtt-preflight","--quiet")
    if p.returncode:
        msg=(p.stderr or p.stdout or "broker MQTT local indisponível").strip()
        raise RuntimeError("Pré-verificação MQTT falhou antes de alterar o rádio: "+msg)

# Do not touch a working RF state if its required local event bus is not ready.
mqtt_preflight()

# One RF protocol + one matching network at a time. RF settings are preserved.
setsec(cp,"D-Star",{"Enable":"1" if proto=="DSTAR" else "0","Module":module if proto=="DSTAR" else cp.get("D-Star","Module",fallback="C")})
setsec(cp,"DMR",{"Enable":"0"})
setsec(cp,"System Fusion",{"Enable":"1" if proto=="YSF" else "0"})
setsec(cp,"P25",{"Enable":"1" if proto=="P25" else "0","NAC":cp.get("P25","NAC",fallback="293")})
setsec(cp,"NXDN",{"Enable":"1" if proto=="NXDN" else "0","RAN":cp.get("NXDN","RAN",fallback="1")})
setsec(cp,"POCSAG",{"Enable":"1" if proto=="POCSAG" else "0"})
setsec(cp,"D-Star Network",{"Enable":"1" if proto=="DSTAR" else "0","LocalAddress":"127.0.0.1","LocalPort":"20011","GatewayAddress":"127.0.0.1","GatewayPort":"20010","Debug":"0"})
setsec(cp,"DMR Network",{"Enable":"0"})
setsec(cp,"System Fusion Network",{"Enable":"1" if proto=="YSF" else "0","LocalAddress":"127.0.0.1","LocalPort":"3200","GatewayAddress":"127.0.0.1","GatewayPort":"4200","Debug":"0"})
setsec(cp,"P25 Network",{"Enable":"1" if proto=="P25" else "0","LocalAddress":"127.0.0.1","LocalPort":"32010","GatewayAddress":"127.0.0.1","GatewayPort":"42020","Debug":"0"})
setsec(cp,"NXDN Network",{"Enable":"1" if proto=="NXDN" else "0","Protocol":"Icom","LocalAddress":"127.0.0.1","LocalPort":"14021","GatewayAddress":"127.0.0.1","GatewayPort":"14020","Debug":"0"})
setsec(cp,"POCSAG Network",{"Enable":"1" if proto=="POCSAG" else "0","LocalAddress":"127.0.0.1","LocalPort":"3800","GatewayAddress":"127.0.0.1","GatewayPort":"4800","Debug":"0"})

buf=[]
with tempfile.NamedTemporaryFile("w+",delete=False) as tf:
    cp.write(tf);tmp_host=Path(tf.name)
host_text=tmp_host.read_text();tmp_host.unlink(missing_ok=True)

voice=read_voice={}
try:read_voice=json.loads((STATE/"voice-settings.json").read_text())
except Exception:pass
lang={"pt":"Portugues","en":"English_UK","es":"Espanol"}.get(str(read_voice.get("language") or "pt"),"Portugues")

try:
    # Stop gateways before changing the local loopback endpoint.
    for unit in SERVICES.values():ctl("stop",unit)
    atomic(HOST,host_text,0o640,"mmdvm")
    normalize_host_permissions()
    # Verify again after the candidate host INI is written, still before the
    # MMDVMHost restart. Any failure enters the transaction rollback.
    mqtt_preflight()

    if proto=="DSTAR":
        d=STATE/"dstar";d.mkdir(parents=True,exist_ok=True)
        normalized=server.replace("_","").replace("-","").upper()
        if normalized.startswith("XLX") and len(normalized)>=6:reflector=normalized[:6]+" "+module
        elif normalized.startswith(("REF","DCS","XRF")):reflector=normalized[:6]+" "+module
        else:reflector=(normalized+" "+module).strip()
        ini=f"""[General]
Type=Hotspot
Callsign={callsign}
Address=0.0.0.0
HBAddress=127.0.0.1
HBPort=20010
Latitude=0.0
Longitude=0.0
Description1=PU2PNY-OS
Description2=Digital Radio Hotspot
URL=https://xlx026.net
Language={lang}

[IRCDDB 1]
Enabled=0

[Repeater 1]
Enabled=1
Band={module}
Callsign={callsign}
Address=127.0.0.1
Port=20011
Type=HB
Reflector={reflector}
ReflectorAtStartup=true
ReflectorReconnect=Fixed
Frequency={rx/1000000:.6f}
Offset={(tx-rx)/1000000:.6f}
RangeKm=1
Latitude=0.0
Longitude=0.0
Description1=PU2PNY-OS
Description2=Hotspot
URL=https://xlx026.net

[APRS]
Enabled=0
[Log]
MQTTLevel=1
DisplayLevel=1
[MQTT]
Address=127.0.0.1
Port=1883
Keepalive=60
Authenticate=0
Name=dstar-gateway
[Paths]
Data=/var/lib/2pny/dstar
[Hosts Files]
HostsFiles=/var/lib/2pny/dstar
ReloadTimer=72
CustomHostsfiles=/var/lib/2pny/dstar/custom
[Dextra]
Enabled=1
MaxDongles=5
[D-Plus]
Enabled=1
MaxDongles=5
Login={callsign}
[DCS]
Enabled=1
[XLX]
Enabled=1
[D-Rats]
Enabled=0
[Remote Commands]
Enabled=0
"""
        atomic(d/"DStarGateway.ini",ini)
        (d/"custom").mkdir(parents=True,exist_ok=True)
        for src in ("DPlus_Hosts.txt","DExtra_Hosts.txt","DCS_Hosts.txt","XLXHosts.txt"):
            p=STATE/"hosts"/src
            if p.exists():shutil.copy2(p,d/src)

    elif proto=="YSF":
        d=STATE/"ysf";d.mkdir(parents=True,exist_ok=True)
        hosts=STATE/"hosts"
        yjson=hosts/"YSFHosts.json"
        if not yjson.exists() and (hosts/"YSFHosts.txt").exists():
            refs=[]
            for raw in (hosts/"YSFHosts.txt").read_text(errors="ignore").splitlines():
                line=raw.strip()
                if not line or line.startswith("#"):continue
                parts=line.split(";")
                if len(parts)<5:continue
                ident,name,desc,host,ps=map(str.strip,parts[:5])
                try:pnum=int(ps)
                except ValueError:continue
                refs.append({"designator":ident.zfill(5)[-5:],"country":"YSF","name":name,
                             "use_xx_prefix":False,"user_count":"000","description":desc or name,
                             "port":pnum,"ipv4":host,"ipv6":None})
            atomic(yjson,json.dumps({"reflectors":refs},ensure_ascii=False,separators=(",",":"))+"\n",0o644)
        rooms=hosts/"FCSRooms.txt"
        if not rooms.exists() and (hosts/"FCSHosts.txt").exists():
            shutil.copy2(hosts/"FCSHosts.txt",rooms)
        for src in ("YSFHosts.json","FCSRooms.txt"):
            p=hosts/src
            if p.exists():shutil.copy2(p,d/src)
        startup=server
        ini=f"""[General]
Callsign={callsign}
Suffix=ND
Id={radioid}
RptAddress=127.0.0.1
RptPort=3200
LocalAddress=127.0.0.1
LocalPort=4200
WiresXCommandPassthrough=1
Debug=0
Daemon=0
[Info]
RXFrequency={rx}
TXFrequency={tx}
Power=1
Latitude=0.0
Longitude=0.0
Height=0
Name=PU2PNY
Description=PU2PNY-OS
[Log]
DisplayLevel=1
MQTTLevel=1
[APRS]
Enable=0
[MQTT]
Address=127.0.0.1
Port=1883
Keepalive=60
Auth=0
Name=ysf-gateway
[Network]
Startup={startup}
InactivityTimeout=10
Reconnect=1
Revert=0
Debug=0
[YSF Network]
Enable=1
Port=42000
Hosts={d/"YSFHosts.json"}
ReloadTime=60
[FCS Network]
Enable=1
Rooms={d/"FCSRooms.txt"}
Port=42001
[GPSD]
Enable=0
[Remote Commands]
Enable=0
"""
        atomic(d/"YSFGateway.ini",ini)

    elif proto=="P25":
        d=STATE/"p25";d.mkdir(parents=True,exist_ok=True)
        p=STATE/"hosts/P25Hosts.json"
        if not p.exists(): atomic(p,'{"reflectors":[]}\n',0o644)
        shutil.copy2(p,d/"P25Hosts.json")
        ident=re.search(r"\d{2,7}",server);static=ident.group(0) if ident else ""
        ini=f"""[General]
Callsign={callsign}
RptAddress=127.0.0.1
RptPort=32010
LocalPort=42020
Debug=0
Daemon=0
[Id Lookup]
Name=/var/lib/2pny/hosts/DMRIds.dat
Time=24
[Voice]
Enabled=0
[Log]
DisplayLevel=1
MQTTLevel=1
[MQTT]
Address=127.0.0.1
Port=1883
Keepalive=60
Auth=0
Name=p25-gateway
[Network]
Port=42010
HostsFile1={d/"P25Hosts.json"}
HostsFile2=/var/lib/2pny/hosts/P25Hosts.txt
ReloadTime=60
Static={static}
RFHangTime=120
NetHangTime=60
Debug=0
[Remote Commands]
Enable=0
"""
        atomic(d/"P25Gateway.ini",ini)

    elif proto=="NXDN":
        d=STATE/"nxdn";d.mkdir(parents=True,exist_ok=True)
        p=STATE/"hosts/NXDNHosts.json"
        if not p.exists(): atomic(p,'{"reflectors":[]}\n',0o644)
        shutil.copy2(p,d/"NXDNHosts.json")
        ident=re.search(r"\d{2,7}",server);static=ident.group(0) if ident else ""
        ini=f"""[General]
Callsign={callsign}
Suffix=NXDN
RptProtocol=Icom
RptAddress=127.0.0.1
RptPort=14021
LocalPort=14020
Debug=0
Daemon=0
[Info]
RXFrequency={rx}
TXFrequency={tx}
Power=1
Latitude=0.0
Longitude=0.0
Height=0
Name=PU2PNY
Description=PU2PNY-OS
[Voice]
Enabled=0
[APRS]
Enable=0
[Id Lookup]
Name=/var/lib/2pny/hosts/NXDN.csv
Time=24
[Log]
DisplayLevel=1
MQTTLevel=1
[MQTT]
Address=127.0.0.1
Port=1883
Keepalive=60
Auth=0
Name=nxdn-gateway
[Network]
Port=14050
HostsFile1={d/"NXDNHosts.json"}
HostsFile2=/var/lib/2pny/hosts/NXDNHosts.txt
ReloadTime=60
Static={static}
RFHangTime=120
NetHangTime=60
Debug=0
[GPSD]
Enable=0
[Remote Commands]
Enable=0
"""
        atomic(d/"NXDNGateway.ini",ini)

    elif proto=="POCSAG":
        d=STATE/"pocsag";d.mkdir(parents=True,exist_ok=True)
        dapnet_address=address or "dapnet.afu.rwth-aachen.de"
        dapnet_port=port or 43434
        ini=f"""[General]
Callsign={callsign}
RptAddress=127.0.0.1
RptPort=3800
LocalAddress=127.0.0.1
LocalPort=4800
Daemon=0

[Log]
DisplayLevel=1
MQTTLevel=1

[MQTT]
Address=127.0.0.1
Port=1883
Keepalive=60
Auth=0
Name=dapnet-gateway

[DAPNET]
Address={dapnet_address}
Port={dapnet_port}
AuthKey={password}
Debug=0
"""
        atomic(d/"DAPNETGateway.ini",ini,0o600)

    ctl("daemon-reload")
    host="2pny-mmdvmhost.service"
    # Validate MMDVMHost first. UDP gateways may be absent while it starts.
    mqtt_preflight()
    if not ctl("restart",host):raise RuntimeError("MMDVMHost restart failed")
    time.sleep(3)
    if not active(host):
        detail=run("journalctl","-u",host,"-n","24","--no-pager","-o","cat").stdout.strip()[-1800:]
        raise RuntimeError("MMDVMHost did not remain active"+(": "+detail if detail else ""))
    unit=SERVICES[proto]
    for p,u in SERVICES.items():
        if p==proto: ctl("enable",u)
        else: ctl("disable",u)
    if not ctl("restart",unit):raise RuntimeError(unit+" failed to start")
    time.sleep(2)
    if not active(unit):
        detail=run("journalctl","-u",unit,"-n","24","--no-pager","-o","cat").stdout.strip()[-1800:]
        raise RuntimeError(unit+" did not remain active"+(": "+detail if detail else ""))
except Exception as exc:
    restore();die(str(exc)+"; configuration rolled back",4)

atomic_json(STATEFILE,{
 "protocol":proto,"server_name":server,"address":address,"port":port,"kind":kind,
 "module":module if proto=="DSTAR" else "","state":"configured","gateway":SERVICES[proto],
 "updated":datetime.datetime.now(datetime.timezone.utc).isoformat()
})
print(f"NETWORK_APPLY_OK protocol={proto} server={server} module={module or '-'}")
