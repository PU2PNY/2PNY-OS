#!/usr/bin/env python3
import datetime, json, os, re, shutil, subprocess, time
from pathlib import Path

REQ=Path("/run/2pny/rflevel-request.json")
RES=Path("/run/2pny/rflevel-result.json")
HOST=Path("/var/lib/2pny/mmdvm/MMDVM-Host.ini")
LIVE=Path("/run/2pny/live-state.json")
BACK=Path("/var/lib/2pny/backups/rflevel")

def finish(obj):
    RES.parent.mkdir(parents=True,exist_ok=True)
    tmp=RES.with_suffix(".tmp")
    tmp.write_text(json.dumps(obj,ensure_ascii=False)+"\n")
    os.chmod(tmp,0o644)
    os.replace(tmp,RES)

def active(unit):
    return subprocess.run(["systemctl","is-active","--quiet",unit]).returncode==0

def set_rflevel(text,value):
    lines=text.splitlines()
    out=[];in_modem=False;seen=False
    for line in lines:
        stripped=line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            if in_modem and not seen:
                out.append(f"RFLevel={value}")
                seen=True
            in_modem=stripped.lower()=="[modem]"
            out.append(line)
            continue
        if in_modem and re.match(r"(?i)^\s*RFLevel\s*=",line):
            out.append(f"RFLevel={value}");seen=True
        else:
            out.append(line)
    if in_modem and not seen:
        out.append(f"RFLevel={value}");seen=True
    if not seen:
        raise RuntimeError("seção [Modem] não encontrada")
    return "\n".join(out)+"\n"

def current_level(text):
    in_modem=False
    for raw in text.splitlines():
        line=raw.strip()
        if line.startswith("[") and line.endswith("]"):
            in_modem=line.lower()=="[modem]";continue
        if in_modem and re.match(r"(?i)^RFLevel\s*=",line):
            return int(line.split("=",1)[1].strip())
    return None

try:
    req=json.loads(REQ.read_text())
    value=int(req.get("rf_level"))
    if value<0 or value>100: raise ValueError("RFLevel deve estar entre 0 e 100")
    try:
        live=json.loads(LIVE.read_text())
    except Exception:
        live={}
    if live.get("active"):
        raise RuntimeError("há atividade de rádio em andamento; aguarde o Standby para alterar a potência")
    text=HOST.read_text()
    previous=current_level(text)
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    BACK.mkdir(parents=True,exist_ok=True)
    backup=BACK/f"MMDVM-Host.ini.{stamp}"
    shutil.copy2(HOST,backup)
    candidate=set_rflevel(text,value)
    tmp=HOST.with_suffix(".rflevel.tmp")
    tmp.write_text(candidate)
    os.chmod(tmp,0o640)
    try:
        import grp
        os.chown(tmp,0,grp.getgrnam("mmdvm").gr_gid)
    except Exception:
        pass
    os.replace(tmp,HOST)
    p=subprocess.run(["systemctl","restart","2pny-mmdvmhost.service"],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    time.sleep(2)
    if p.returncode or not active("2pny-mmdvmhost.service"):
        shutil.copy2(backup,HOST)
        subprocess.run(["systemctl","restart","2pny-mmdvmhost.service"])
        raise RuntimeError("MMDVMHost não permaneceu ativo; valor anterior restaurado")
    effective=current_level(HOST.read_text())
    finish({"ok":True,"rf_level":effective,"previous":previous,"backup":str(backup)})
except Exception as exc:
    finish({"ok":False,"error":str(exc)})
    raise SystemExit(1)
