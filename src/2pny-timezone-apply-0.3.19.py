#!/usr/bin/env python3
"""PU2PNY-OS 0.3.19 privileged timezone helper.

Consumes all pending uniquely named requests from /run/2pny. No shell, no arbitrary
filesystem target and no generic privileged command surface.
"""
import json, os, re, subprocess
from pathlib import Path

RUN=Path("/run/2pny")
REQ_RE=re.compile(r"^timezone-request-([0-9]{10,32})\.json$")

def finish(request_id,obj):
    obj=dict(obj,request_id=request_id)
    target=RUN/f"timezone-result-{request_id}.json"
    tmp=RUN/f".timezone-result-{request_id}.tmp"
    tmp.write_text(json.dumps(obj,ensure_ascii=False)+"\n")
    os.chmod(tmp,0o644)
    os.replace(tmp,target)

def find_request():
    rows=[]
    for p in RUN.glob("timezone-request-*.json"):
        m=REQ_RE.fullmatch(p.name)
        if m:
            try: rows.append((p.stat().st_mtime_ns,p,m.group(1)))
            except FileNotFoundError: pass
    return min(rows,key=lambda x:x[0]) if rows else None

def effective_timezone():
    p=subprocess.run(
        ["timedatectl","show","-p","Timezone","--value"],
        text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=5)
    value=(p.stdout or "").strip()
    if value:return value
    try:
        target=os.path.realpath("/etc/localtime")
        prefix="/usr/share/zoneinfo/"
        if target.startswith(prefix):return target[len(prefix):]
    except Exception:pass
    return ""

def process_one(found):
    _,req_path,request_id=found
    try:
        raw=req_path.read_text()
        try:req_path.unlink()
        except FileNotFoundError:pass
        req=json.loads(raw)
        if str(req.get("request_id") or "")!=request_id:raise ValueError("request-id de fuso não confere")
        tz=str(req.get("timezone") or "").strip()
        if not tz or ".." in tz or tz.startswith("/") or not re.fullmatch(r"[A-Za-z0-9_+.-]+(?:/[A-Za-z0-9_+.-]+)+",tz):raise ValueError("fuso horário inválido")
        if not (Path("/usr/share/zoneinfo")/tz).is_file():raise ValueError("fuso horário não existe neste sistema")
        p=subprocess.run(["timedatectl","set-timezone",tz],text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=10)
        if p.returncode:raise RuntimeError("timedatectl: "+(p.stderr or p.stdout or "falhou").strip()[-800:])
        effective=effective_timezone()
        if effective!=tz:raise RuntimeError(f"fuso não confirmado: solicitado={tz}, efetivo={effective or '—'}")
        try:Path("/etc/timezone").write_text(tz+"\n")
        except Exception:pass
        finish(request_id,{"ok":True,"timezone":effective,"method":"timedatectl"})
    except Exception as exc:
        try:finish(request_id,{"ok":False,"error":str(exc)[:900],"timezone":effective_timezone()})
        except Exception:pass
def main():
    RUN.mkdir(parents=True,exist_ok=True)
    # SEC-026: drain pending requests so PathExistsGlob cannot stay true
    # without a fresh activation edge.
    for _ in range(32):
        found=find_request()
        if not found:return 0
        process_one(found)
    return 0

if __name__=="__main__":
    raise SystemExit(main())
