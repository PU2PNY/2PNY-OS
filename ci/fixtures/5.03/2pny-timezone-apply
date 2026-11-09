#!/usr/bin/env python3
"""PU2PNY-OS 0.3.20 privileged clock/timezone helper.

Consumes bounded uniquely named requests from /run/2pny. It exposes only two
strict operations: set a zone that exists in /usr/share/zoneinfo, or set a
validated local wall clock after disabling NTP. No shell/eval/arbitrary path.
"""
import datetime, json, os, re, subprocess
from pathlib import Path

RUN=Path("/run/2pny")
TZ_RE=re.compile(r"^timezone-request-([0-9]{10,32})\.json$")
TIME_RE=re.compile(r"^time-request-([0-9]{10,32})\.json$")
ZONE_RE=re.compile(r"^[A-Za-z0-9_+.-]+(?:/[A-Za-z0-9_+.-]+)*$")

def run(args,timeout=10):
    return subprocess.run(args,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=timeout)

def finish(kind,request_id,obj):
    obj=dict(obj,request_id=request_id)
    target=RUN/f"{kind}-result-{request_id}.json"
    tmp=RUN/f".{kind}-result-{request_id}.tmp"
    tmp.write_text(json.dumps(obj,ensure_ascii=False)+"\n")
    os.chmod(tmp,0o644)
    os.replace(tmp,target)

def candidates():
    rows=[]
    for kind,glob,rx in (("timezone","timezone-request-*.json",TZ_RE),("time","time-request-*.json",TIME_RE)):
        for p in RUN.glob(glob):
            m=rx.fullmatch(p.name)
            if not m:continue
            try:rows.append((p.stat().st_mtime_ns,kind,p,m.group(1)))
            except FileNotFoundError:pass
    return sorted(rows,key=lambda x:x[0])

def effective_timezone():
    p=run(["timedatectl","show","-p","Timezone","--value"],5)
    value=(p.stdout or "").strip()
    if value:return value
    try:
        target=os.path.realpath("/etc/localtime");prefix="/usr/share/zoneinfo/"
        if target.startswith(prefix):return target[len(prefix):]
    except Exception:pass
    return ""

def set_timezone(req,request_id):
    tz=str(req.get("timezone") or "").strip()
    if not tz or ".." in tz or tz.startswith("/") or not ZONE_RE.fullmatch(tz):
        raise ValueError("fuso horário inválido")
    zone=Path("/usr/share/zoneinfo")/tz
    if not zone.is_file():raise ValueError("fuso horário não existe neste sistema")
    p=run(["timedatectl","set-timezone",tz],10)
    if p.returncode:raise RuntimeError("timedatectl: "+(p.stderr or p.stdout or "falhou").strip()[-800:])
    effective=effective_timezone()
    if effective!=tz:raise RuntimeError(f"fuso não confirmado: solicitado={tz}, efetivo={effective or '—'}")
    try:Path("/etc/timezone").write_text(tz+"\n")
    except Exception:pass
    finish("timezone",request_id,{"ok":True,"timezone":effective,"method":"timedatectl"})

def set_time(req,request_id):
    value=str(req.get("local_time") or "").strip()
    try:
        parsed=datetime.datetime.strptime(value,"%Y-%m-%dT%H:%M:%S")
    except ValueError:
        try:parsed=datetime.datetime.strptime(value,"%Y-%m-%dT%H:%M")
        except ValueError:raise ValueError("data/hora inválida; use AAAA-MM-DDTHH:MM[:SS]")
    if not 2020<=parsed.year<=2099:raise ValueError("ano fora do intervalo permitido")
    p=run(["timedatectl","set-ntp","false"],10)
    if p.returncode:raise RuntimeError("não foi possível desativar NTP antes do ajuste manual")
    wanted=parsed.strftime("%Y-%m-%d %H:%M:%S")
    p=run(["timedatectl","set-time",wanted],10)
    if p.returncode:raise RuntimeError("timedatectl: "+(p.stderr or p.stdout or "falhou").strip()[-800:])
    out=run(["date","+%Y-%m-%dT%H:%M:%S"],5)
    effective=(out.stdout or "").strip()
    try:
        actual=datetime.datetime.strptime(effective,"%Y-%m-%dT%H:%M:%S")
        if abs((actual-parsed).total_seconds())>5:raise RuntimeError(f"hora não confirmada: solicitado={value}, efetivo={effective or '—'}")
    except ValueError:raise RuntimeError("não foi possível confirmar a hora efetiva")
    finish("time",request_id,{"ok":True,"local_time":effective,"timezone":effective_timezone(),"ntp":False,"method":"timedatectl"})

def process_one(found):
    _,kind,req_path,request_id=found
    try:
        raw=req_path.read_text()
        try:req_path.unlink()
        except FileNotFoundError:pass
        req=json.loads(raw)
        if str(req.get("request_id") or "")!=request_id:raise ValueError("request-id não confere")
        if kind=="timezone":set_timezone(req,request_id)
        else:set_time(req,request_id)
    except Exception as exc:
        try:finish(kind,request_id,{"ok":False,"error":str(exc)[:900],"timezone":effective_timezone()})
        except Exception:pass

def main():
    RUN.mkdir(parents=True,exist_ok=True)
    # SEC-028/029: drain all pending bounded requests so PathExistsGlob
    # cannot remain true without a fresh activation edge.
    for _ in range(32):
        rows=candidates()
        if not rows:return 0
        process_one(rows[0])
    return 0

if __name__=="__main__":raise SystemExit(main())
