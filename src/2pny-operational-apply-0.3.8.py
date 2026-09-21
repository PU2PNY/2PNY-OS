#!/usr/bin/env python3
import fcntl,json,os,subprocess,sys,time
from pathlib import Path
STATE=Path("/var/lib/2pny");RUN=Path("/run/2pny");CFG=STATE/"config.json";RF=STATE/"rf-configured"
DISABLED=STATE/"operational-disabled";REQ=RUN/"operational-request.json";RES=RUN/"operational-result.json";LOCK=RUN/"operational.lock"
HOST="2pny-mmdvmhost.service"
GATEWAYS={"DMR":"2pny-dmrgateway.service","DSTAR":"2pny-dstargateway.service","YSF":"2pny-ysfgateway.service","P25":"2pny-p25gateway.service","NXDN":"2pny-nxdngateway.service","POCSAG":"2pny-dapnetgateway.service"}
def run(*a,timeout=20):return subprocess.run(list(a),text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=timeout)
def active(u):return run("systemctl","is-active","--quiet",u,timeout=5).returncode==0
def result(o):
 RUN.mkdir(parents=True,exist_ok=True);t=RES.with_suffix(".tmp");t.write_text(json.dumps(o,ensure_ascii=False)+"\n");os.chmod(t,0o644);os.replace(t,RES)
def journal(u):
 try:return run("journalctl","-u",u,"-n","18","--no-pager","-o","cat",timeout=6).stdout.strip()[-1600:]
 except Exception:return ""
def wait(u,secs=12):
 end=time.monotonic()+secs
 while time.monotonic()<end:
  if active(u):return True
  time.sleep(.4)
 return False
def start(u,retries=3):
 last=""
 for _ in range(retries):
  run("systemctl","reset-failed",u,timeout=5);p=run("systemctl","start",u,timeout=20)
  if p.returncode==0 and wait(u):return True,""
  last=(p.stderr or p.stdout or journal(u) or "serviço não permaneceu ativo").strip();time.sleep(1)
 return False,last or journal(u)
def action():
 if len(sys.argv)>1:return sys.argv[1].strip().lower()
 try:return str(json.loads(REQ.read_text()).get("action") or "").strip().lower()
 except Exception:return ""
def config():
 try:return json.loads(CFG.read_text())
 except Exception:return {}
def display(st,msg):
 try:subprocess.run(["/usr/local/sbin/2pny-display-status",st,msg],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=4)
 except Exception:pass
RUN.mkdir(parents=True,exist_ok=True)
with open(LOCK,"w") as lk:
 fcntl.flock(lk,fcntl.LOCK_EX);a=action()
 if a=="off":
  DISABLED.write_text("1\n");os.chmod(DISABLED,0o600)
  for u in GATEWAYS.values():run("systemctl","stop",u,timeout=10)
  run("systemctl","stop",HOST,timeout=10);ok=not active(HOST);display("warning","Operacional desligado")
  result({"ok":ok,"operational":False,"state":"disabled","message":"Operacional desligado." if ok else "MMDVMHost não confirmou parada."});raise SystemExit(0 if ok else 1)
 if a not in ("on","restore"):
  result({"ok":False,"error":"ação operacional inválida"});raise SystemExit(2)
 if a=="restore" and DISABLED.exists():
  result({"ok":True,"operational":False,"state":"disabled","reason":"user_disabled","message":"Operacional permaneceu desligado por escolha do usuário."});raise SystemExit(0)
 if not RF.exists():
  result({"ok":False,"operational":False,"error":"RF ainda não foi configurada."});raise SystemExit(3)
 c=config();proto=str(c.get("protocol") or "").upper();unit=GATEWAYS.get(proto)
 if not unit:
  result({"ok":False,"operational":False,"error":"Perfil/protocolo salvo inválido."});raise SystemExit(4)
 if a=="on":
  try:DISABLED.unlink()
  except FileNotFoundError:pass
 run("systemctl","start","mosquitto.service",timeout=12);run("systemctl","enable",HOST,timeout=8)
 ok,detail=start(HOST)
 if not ok:
  result({"ok":False,"operational":False,"protocol":proto,"service":HOST,"error":"MMDVMHost não iniciou.","detail":detail or journal(HOST)});raise SystemExit(5)
 for p,u in GATEWAYS.items():
  if p==proto:run("systemctl","enable",u,timeout=8)
  else:run("systemctl","disable",u,timeout=8);run("systemctl","stop",u,timeout=8)
 ok,detail=start(unit)
 if not ok:
  result({"ok":False,"operational":False,"protocol":proto,"service":unit,"mmdvmhost_active":active(HOST),"error":"Gateway do perfil salvo não iniciou.","detail":detail or journal(unit)});raise SystemExit(6)
 try:subprocess.run(["systemctl","try-restart","2pny-display-core.service"],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=8)
 except Exception:pass
 result({"ok":True,"operational":True,"state":"active","protocol":proto,"gateway":unit,"mmdvmhost_active":True,"gateway_active":True,"message":"Operacional restaurado com o perfil "+proto+"."})
