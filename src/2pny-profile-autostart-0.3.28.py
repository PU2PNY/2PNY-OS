#!/usr/bin/env python3
import fcntl,json,os,subprocess,sys
from pathlib import Path

STATE=Path("/var/lib/2pny")
RUN=Path("/run/2pny")
CFG=STATE/"config.json"
HW=STATE/"hardware-probe.json"
PROVISIONED=STATE/"provisioned"
VALID={"DMR":"2pny-dmrgateway.service","DSTAR":"2pny-dstargateway.service","YSF":"2pny-ysfgateway.service",
       "P25":"2pny-p25gateway.service","NXDN":"2pny-nxdngateway.service","POCSAG":"2pny-dapnetgateway.service"}

RUN.mkdir(parents=True,exist_ok=True)
lock=open(RUN/"profile-autostart.lock","w")
try:
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
except BlockingIOError:
    raise SystemExit(0)

def readj(path):
    try:return json.loads(path.read_text())
    except Exception:return {}
def active(unit):
    return subprocess.run(["systemctl","is-active","--quiet",unit],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode==0
def log(msg):
    subprocess.run(["logger","-t","pu2pny-profile-autostart","--",msg],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)

if not PROVISIONED.exists():
    raise SystemExit(0)
cfg=readj(CFG)
proto=str(cfg.get("protocol") or "").upper()
gateway=VALID.get(proto)
if not gateway:
    raise SystemExit(0)
mmdvm=readj(HW).get("mmdvm") or {}
if not mmdvm.get("detected"):
    log("perfil salvo não reativado: MMDVM ainda não confirmada")
    raise SystemExit(0)
# A healthy selected profile is never touched merely because the network changed.
if active("2pny-mmdvmhost.service") and active(gateway):
    raise SystemExit(0)
if subprocess.run(["ip","-4","route","show","default"],stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True).returncode!=0:
    raise SystemExit(0)
try:
    result=subprocess.run(["timeout","-k","5","80","/usr/local/sbin/2pny-protocol-profiles","activate",proto],
                          stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=90)
except Exception as exc:
    log("falha controlada ao reativar perfil salvo")
    raise SystemExit(0)
if result.returncode==0:
    log("perfil salvo reativado: "+proto)
else:
    # Do not include helper output: it can contain provider details and should
    # not leak credentials or turn a transient network error into a reboot loop.
    log("perfil salvo permaneceu pendente: "+proto)
raise SystemExit(0)
