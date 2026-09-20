#!/usr/bin/env python3
"""PU2PNY-OS 0.3.6 independent protocol RF/network profiles."""
import datetime,json,os,re,shutil,subprocess,sys,tempfile
from pathlib import Path

STATE=Path("/var/lib/2pny")
CFG=STATE/"config.json"
PROFILES=STATE/"protocol-profiles.json"
HW=STATE/"hardware-probe.json"
SECRETS=STATE/"protocol-secrets"
BACKUPS=STATE/"backups/profiles"
VALID={"DMR","DSTAR","YSF","P25","NXDN","POCSAG"}

def readj(p,default=None):
    try:return json.loads(Path(p).read_text())
    except Exception:return {} if default is None else default

def atomic_json(p,obj,mode=0o600):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(prefix="."+p.name+".",dir=str(p.parent))
    with os.fdopen(fd,"w") as f:json.dump(obj,f,ensure_ascii=False,indent=2);f.write("\n")
    os.chmod(tmp,mode);os.replace(tmp,p)

def die(msg,code=2):
    print(msg,file=sys.stderr);raise SystemExit(code)

def validate(profile):
    proto=str(profile.get("protocol") or "").upper()
    if proto not in VALID:die("protocolo inválido")
    try:rx=int(profile.get("rx_hz") or 0);tx=int(profile.get("tx_hz") or rx)
    except Exception:die("frequência inválida")
    if not 100_000_000<=rx<=1_000_000_000 or not 100_000_000<=tx<=1_000_000_000:die("frequência fora de 100 MHz..1 GHz")
    mode=str(profile.get("use_mode") or "hotspot")
    if mode not in ("hotspot","repeater"):die("modo RF inválido")
    if mode=="hotspot":tx=rx
    module=str(profile.get("xlx_module") or "").upper()
    if proto=="DSTAR" and not re.fullmatch(r"[A-Z]",module or ""):module="D"
    essid=str(profile.get("essid") or "").strip()
    if proto=="DMR":
        if essid and not re.fullmatch(r"(?:0[1-9]|[1-9][0-9])",essid):die("identificação DMR deve ser 01 a 99")
    else:essid=""
    out=dict(profile);out.update(protocol=proto,rx_hz=rx,tx_hz=tx,use_mode=mode,xlx_module=module,essid=essid)
    out["server_port"]=int(out.get("server_port") or 0)
    out["color_code"]=int(out.get("color_code") or 1)
    out["dmr_slot"]=str(out.get("dmr_slot") or "2")
    return out

def profile_from_cfg(c):
    return validate({k:c.get(k) for k in (
      "protocol","rx_hz","tx_hz","use_mode","server_name","server_address","server_port",
      "network_kind","xlx_module","color_code","dmr_slot","essid")})

def load_profiles():
    obj=readj(PROFILES,{"profiles":{}})
    if not isinstance(obj,dict):obj={"profiles":{}}
    ps=obj.get("profiles")
    if not isinstance(ps,dict):ps={};obj["profiles"]=ps
    c=readj(CFG,{})
    proto=str(c.get("protocol") or "").upper()
    if proto in VALID and proto not in ps:
        try:ps[proto]=profile_from_cfg(c);atomic_json(PROFILES,obj)
        except Exception:pass
    return obj

def save_stdin():
    try:profile=validate(json.load(sys.stdin))
    except SystemExit:raise
    except Exception:die("perfil inválido")
    obj=load_profiles();obj["profiles"][profile["protocol"]]=profile
    obj["updated"]=datetime.datetime.now(datetime.timezone.utc).isoformat()
    atomic_json(PROFILES,obj)
    print(json.dumps({"ok":True,"profile":profile},ensure_ascii=False))

def port_from_hw():
    h=readj(HW,{});m=h.get("mmdvm") or {}
    if not m.get("detected"):die("MMDVM não detectada; perfil não aplicado",3)
    port=str(m.get("port") or "")
    if not port.startswith("/dev/"):die("porta MMDVM inválida",3)
    return port

def secret(proto):
    p=SECRETS/(proto.lower()+".secret")
    try:return p.read_text().strip()
    except Exception:return ""

def activate(proto):
    proto=proto.upper()
    obj=load_profiles();profile=(obj.get("profiles") or {}).get(proto)
    if not profile:die("perfil ainda não configurado para "+proto,4)
    profile=validate(profile);old=readj(CFG,{})
    if not old:die("configuração atual ausente",4)
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    bdir=BACKUPS/stamp;bdir.mkdir(parents=True,exist_ok=True);shutil.copy2(CFG,bdir/"config.json")
    port=port_from_hw()
    old_rx=int(old.get("rx_hz") or 0);old_tx=int(old.get("tx_hz") or old_rx)
    old_mode=str(old.get("use_mode") or "hotspot")
    rf_changed=(old_rx!=profile["rx_hz"] or old_tx!=profile["tx_hz"] or old_mode!=profile["use_mode"])
    def rf(c):
        rx=str(int(c.get("rx_hz") or 0));tx=str(int(c.get("tx_hz") or c.get("rx_hz") or 0))
        if str(c.get("use_mode") or "hotspot")!="repeater":tx=rx
        args=[rx,tx,str(int(c.get("rx_offset_hz") or 0)),str(int(c.get("tx_offset_hz") or 0)),
              "1" if str(c.get("use_mode"))=="repeater" else "0",port,str(c.get("callsign") or ""),str(c.get("dmr_id") or "")]
        return subprocess.run(["/usr/local/sbin/2pny-rf-apply",*args],text=True,capture_output=True,timeout=45)
    if rf_changed:
        merged=dict(old);merged.update(profile)
        r=rf(merged)
        if r.returncode:die((r.stderr or r.stdout or "falha ao aplicar RF").strip(),5)
    pwd=secret(proto)
    args=[proto,str(profile.get("server_name") or ""),str(profile.get("server_address") or ""),
          str(profile.get("server_port") or 0),pwd,str(profile.get("use_mode") or "hotspot"),
          str(profile.get("color_code") or 1),str(profile.get("dmr_slot") or "2"),
          str(profile.get("xlx_module") or ""),str(profile.get("essid") or ""),
          str(profile.get("network_kind") or ""),""] 
    r=subprocess.run(["/usr/local/sbin/2pny-protocol-network-apply",*args],text=True,capture_output=True,timeout=55)
    if r.returncode:
        if rf_changed:
            try:rf(old)
            except Exception:pass
        die((r.stderr or r.stdout or "falha ao aplicar rede do protocolo").strip(),6)
    new=dict(old);new.update(profile);new["network_state"]="connecting"
    atomic_json(CFG,new)
    print(json.dumps({"ok":True,"active":proto,"profile":profile,"rf_changed":rf_changed},ensure_ascii=False))

def main():
    cmd=sys.argv[1] if len(sys.argv)>1 else "list-json"
    if cmd=="list-json":
        obj=load_profiles();obj["current"]=str(readj(CFG,{}).get("protocol") or "").upper();print(json.dumps(obj,ensure_ascii=False))
    elif cmd=="save-json":save_stdin()
    elif cmd=="activate" and len(sys.argv)==3:activate(sys.argv[2])
    else:die("uso: 2pny-protocol-profiles list-json|save-json|activate PROTO")
if __name__=="__main__":main()
