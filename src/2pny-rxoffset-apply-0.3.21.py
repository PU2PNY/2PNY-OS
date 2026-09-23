#!/usr/bin/env python3
"""PU2PNY-OS 0.3.21 safe RXOffset calibration apply."""
import datetime,json,os,re,shutil,subprocess,time,tempfile
from pathlib import Path

REQ=Path("/run/2pny/rxoffset-request.json")
RES=Path("/run/2pny/rxoffset-result.json")
HOST=Path("/var/lib/2pny/mmdvm/MMDVM-Host.ini")
LIVE=Path("/run/2pny/live-state.json")
BACK=Path("/var/lib/2pny/backups/rxoffset")

def finish(obj):
    RES.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(prefix=".rxoffset-result.",dir=str(RES.parent))
    with os.fdopen(fd,"w") as f:
        json.dump(obj,f,ensure_ascii=False,separators=(",",":"));f.write("\n");f.flush();os.fsync(f.fileno())
    os.chmod(tmp,0o644);os.replace(tmp,RES)

def active(unit):
    return subprocess.run(["systemctl","is-active","--quiet",unit],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode==0

def current(text):
    section=""
    for raw in text.splitlines():
        line=raw.strip()
        if line.startswith("[") and line.endswith("]"):section=line[1:-1].strip().lower();continue
        if section=="modem" and re.match(r"(?i)^RXOffset\s*=",line):
            return int(line.split("=",1)[1].strip())
    return 0

def render(text,value):
    lines=text.splitlines();out=[];section="";seen=False
    for raw in lines:
        stripped=raw.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            if section=="modem" and not seen:out.append(f"RXOffset={value}");seen=True
            section=stripped[1:-1].strip().lower();out.append(raw);continue
        if section=="modem" and re.match(r"(?i)^\s*RXOffset\s*=",raw):
            out.append(f"RXOffset={value}");seen=True
        else:out.append(raw)
    if section=="modem" and not seen:out.append(f"RXOffset={value}");seen=True
    if not seen:raise RuntimeError("seção [Modem] não encontrada")
    return "\n".join(out)+"\n"

try:
    req=json.loads(REQ.read_text())
    value=int(req.get("rx_offset_hz"))
    if value < -10000 or value > 10000:raise ValueError("RXOffset de calibração deve ficar entre -10000 e 10000 Hz")
    try:live=json.loads(LIVE.read_text())
    except Exception:live={}
    if live.get("active"):raise RuntimeError("há atividade RF em andamento; aguarde Standby para mudar RXOffset")
    text=HOST.read_text();previous=current(text)
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    BACK.mkdir(parents=True,exist_ok=True);backup=BACK/f"MMDVM-Host.ini.{stamp}";shutil.copy2(HOST,backup)
    candidate=render(text,value)
    fd,tmp=tempfile.mkstemp(prefix=".MMDVM-Host.rxoffset.",dir=str(HOST.parent))
    with os.fdopen(fd,"w") as fp:
        fp.write(candidate);fp.flush();os.fsync(fp.fileno())
    os.chmod(tmp,0o640)
    try:
        import grp;os.chown(tmp,0,grp.getgrnam("mmdvm").gr_gid)
    except Exception:pass
    os.replace(tmp,HOST)
    p=subprocess.run(["systemctl","restart","2pny-mmdvmhost.service"],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    time.sleep(2)
    if p.returncode or not active("2pny-mmdvmhost.service"):
        shutil.copy2(backup,HOST);subprocess.run(["systemctl","restart","2pny-mmdvmhost.service"],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        raise RuntimeError("MMDVMHost não permaneceu ativo; RXOffset anterior restaurado")
    effective=current(HOST.read_text())
    if effective!=value:raise RuntimeError("RXOffset efetivo não confere")
    finish({"ok":True,"rx_offset_hz":effective,"previous":previous,"backup":str(backup)})
except Exception as exc:
    finish({"ok":False,"error":str(exc)})
    raise SystemExit(1)
