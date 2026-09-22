#!/usr/bin/env python3
"""PU2PNY-OS SEC-025 one-shot RF administration helper."""
import json, os, re, subprocess, sys, time
from pathlib import Path

REQ=Path("/run/2pny/radio-admin-command.request")
ARM=Path("/run/2pny/radio-admin-armed.json")
STATUS=Path("/run/2pny/radio-admin-status.json")
CFG=Path("/var/lib/2pny/config.json")
ARM_SECONDS=30
PROFILE_MAP={"DMR":"DMR","DSTAR":"DSTAR","YSF":"YSF","P25":"P25","NXDN":"NXDN","POCSAG":"POCSAG"}

def norm(v):
    v=str(v or "").upper().strip()
    v=v.split("/",1)[0].strip()
    return re.sub(r"\s+","",v)

def atomic(path,obj,mode):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(json.dumps(obj,ensure_ascii=False,separators=(",",":"))+"\n")
    os.chmod(tmp,mode);os.replace(tmp,path)

def status(ok,action,caller,message,**extra):
    obj={"ok":bool(ok),"action":action,"caller":caller,"message":message,
         "updated":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime())}
    obj.update(extra);atomic(STATUS,obj,0o644)

def configured_owner():
    try:
        obj=json.loads(CFG.read_text())
        return norm(obj.get("callsign"))
    except Exception:
        return ""

def read_request():
    try: raw=REQ.read_text(errors="replace").strip()
    except FileNotFoundError: return None
    finally:
        try: REQ.unlink()
        except FileNotFoundError: pass
    parts=raw.split("\t")
    if len(parts)<2:return None
    action=parts[0].strip().upper();caller=norm(parts[1]);arg=(parts[2].strip().upper() if len(parts)>2 else "")
    return action,caller,arg

def armed_for(caller):
    try:
        obj=json.loads(ARM.read_text())
        return norm(obj.get("caller"))==caller and float(obj.get("expires",0))>=time.time()
    except Exception:
        return False

def consume_arm():
    try:ARM.unlink()
    except FileNotFoundError:pass

def schedule_system(action):
    verb="poweroff" if action=="OFF" else "reboot"
    unit="2pny-radio-admin-"+verb
    p=subprocess.run(["systemd-run","--quiet","--unit",unit,"--on-active=6s",
                      "/usr/bin/systemctl",verb],text=True,capture_output=True,timeout=8)
    if p.returncode:
        raise RuntimeError((p.stderr or p.stdout or "systemd-run failed").strip())

def main():
    if os.geteuid()!=0:
        return 2
    req=read_request()
    if not req:return 0
    action,caller,arg=req
    owner=configured_owner()
    if not owner or caller!=owner:
        status(False,action,caller,"Comando RF recusado: indicativo não autorizado.")
        return 3
    if action=="ARM":
        now=time.time()
        atomic(ARM,{"caller":caller,"armed_at":now,"expires":now+ARM_SECONDS},0o600)
        status(True,action,caller,f"Administração RF armada por {ARM_SECONDS}s.",expires_in=ARM_SECONDS)
        return 0
    if not armed_for(caller):
        consume_arm()
        status(False,action,caller,"Comando RF recusado: envie PNYARM e repita dentro de 30 s.")
        return 4
    consume_arm()
    try:
        if action in ("OFF","REBOOT"):
            schedule_system(action)
            status(True,action,caller,"Ação agendada com atraso seguro de 6 s.")
            return 0
        if action=="PROFILE" and arg in PROFILE_MAP:
            p=subprocess.run(["/usr/local/sbin/2pny-protocol-profiles","activate",PROFILE_MAP[arg]],
                             text=True,capture_output=True,timeout=75)
            if p.returncode:
                raise RuntimeError((p.stderr or p.stdout or "falha ao ativar perfil").strip())
            status(True,action,caller,"Perfil ativado.",profile=PROFILE_MAP[arg])
            return 0
        raise RuntimeError("ação não permitida")
    except Exception as exc:
        status(False,action,caller,"Falha: "+str(exc)[:220],profile=arg or None)
        return 5

if __name__=="__main__":
    raise SystemExit(main())
