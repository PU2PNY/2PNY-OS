#!/usr/bin/env python3
import json, os, subprocess
from pathlib import Path

REQ=Path("/run/2pny/timezone-request.json")
RES=Path("/run/2pny/timezone-result.json")

def finish(obj):
    RES.parent.mkdir(parents=True,exist_ok=True)
    tmp=RES.with_suffix(".tmp")
    tmp.write_text(json.dumps(obj,ensure_ascii=False)+"\n")
    os.chmod(tmp,0o644)
    os.replace(tmp,RES)

try:
    req=json.loads(REQ.read_text())
    tz=str(req.get("timezone") or "").strip()
    if not tz or ".." in tz or tz.startswith("/"):
        raise ValueError("fuso horário inválido")
    zone=Path("/usr/share/zoneinfo")/tz
    if not zone.is_file():
        raise ValueError("fuso horário não existe neste sistema")
    p=subprocess.run(["timedatectl","set-timezone",tz],text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=8)
    if p.returncode:
        raise RuntimeError((p.stderr or p.stdout or "timedatectl falhou").strip())
    q=subprocess.run(["timedatectl","show","-p","Timezone","--value"],text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=4)
    effective=q.stdout.strip()
    if effective!=tz:
        raise RuntimeError("o sistema não confirmou o fuso solicitado")
    finish({"ok":True,"timezone":effective})
except Exception as exc:
    finish({"ok":False,"error":str(exc)})
    raise SystemExit(1)
