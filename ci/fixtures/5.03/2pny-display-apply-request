#!/usr/bin/env python3
import json, os, subprocess, time
from pathlib import Path

RES=Path("/run/2pny/display-apply-result.json")
RUNTIME=Path("/var/lib/2pny/display-runtime.json")

def finish(obj):
    RES.parent.mkdir(parents=True,exist_ok=True)
    tmp=RES.with_suffix(".tmp")
    tmp.write_text(json.dumps(obj,ensure_ascii=False)+"\n")
    os.chmod(tmp,0o644)
    os.replace(tmp,RES)

try:
    p=subprocess.run(["/usr/local/sbin/2pny-display-apply"],text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=35)
    if p.returncode:
        raise RuntimeError((p.stdout or "não foi possível aplicar o display").strip())
    runtime={}
    try: runtime=json.loads(RUNTIME.read_text())
    except Exception: pass
    finish({"ok":True,"runtime":runtime,"message":str(runtime.get("message") or "Display aplicado e confirmado.")})
except Exception as exc:
    finish({"ok":False,"error":str(exc)})
    raise SystemExit(1)
