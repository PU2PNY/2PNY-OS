#!/usr/bin/env python3
import json, os, subprocess
from pathlib import Path

REQ=Path("/run/2pny/ssh-request.json")
RES=Path("/run/2pny/ssh-result.json")

def finish(obj):
    RES.parent.mkdir(parents=True,exist_ok=True)
    tmp=RES.with_suffix(".tmp")
    tmp.write_text(json.dumps(obj,ensure_ascii=False)+"\n")
    os.chmod(tmp,0o644)
    os.replace(tmp,RES)

try:
    req=json.loads(REQ.read_text())
    action=str(req.get("action") or "").strip()
    key=str(req.get("key") or "").strip()
    if action not in ("ssh-enable","ssh-disable"):
        raise ValueError("ação SSH inválida")
    if action=="ssh-enable" and not key:
        raise ValueError("chave pública SSH ausente")
    p=subprocess.run(
        ["/usr/local/sbin/2pny-expert-ssh",action],
        input=(key+"\n") if key else "",
        text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=20
    )
    if p.returncode:
        raise RuntimeError((p.stdout or "não foi possível alterar o SSH").strip())
    active=subprocess.run(["systemctl","is-active","--quiet","ssh.service"]).returncode==0
    if action=="ssh-enable" and not active:
        raise RuntimeError("ssh.service não permaneceu ativo")
    if action=="ssh-disable" and active:
        raise RuntimeError("ssh.service permaneceu ativo após desativar")
    finish({"ok":True,"ssh_active":active,"user":"radioexpert","port":22})
except Exception as exc:
    finish({"ok":False,"error":str(exc)})
    raise SystemExit(1)
