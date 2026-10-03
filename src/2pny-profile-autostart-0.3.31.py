#!/usr/bin/env python3
import fcntl,json,os,subprocess,tempfile
from pathlib import Path
STATE=Path('/var/lib/2pny');RUN=Path('/run/2pny')
CFG=STATE/'config.json';PROVEN=STATE/'last-active-profile.json';HW=STATE/'hardware-probe.json';PROVISIONED=STATE/'provisioned'
VALID={'DMR':'2pny-dmrgateway.service','DSTAR':'2pny-dstargateway.service','YSF':'2pny-ysfgateway.service','P25':'2pny-p25gateway.service','NXDN':'2pny-nxdngateway.service','POCSAG':'2pny-dapnetgateway.service'}
RUN.mkdir(parents=True,exist_ok=True); lock=open(RUN/'profile-autostart.lock','w')
try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
except BlockingIOError:raise SystemExit(0)
def readj(p):
    try:return json.loads(p.read_text())
    except Exception:return {}
def active(u):return subprocess.run(['systemctl','is-active','--quiet',u],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode==0
def log(m):subprocess.run(['logger','-t','pu2pny-profile-autostart','--',m],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
def atomic(path,obj):
    fd,tmp=tempfile.mkstemp(prefix='.'+path.name+'.',dir=str(path.parent))
    try:
        with os.fdopen(fd,'w') as f:json.dump(obj,f,ensure_ascii=False,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
        os.chmod(tmp,0o600);os.replace(tmp,path)
    finally:
        try:os.unlink(tmp)
        except FileNotFoundError:pass
if not PROVISIONED.exists():raise SystemExit(0)
proof=readj(PROVEN);proto=str(proof.get('protocol') or '').upper();gateway=VALID.get(proto)
if not gateway or not isinstance(proof.get('profile'),dict):raise SystemExit(0)
mmdvm=readj(HW).get('mmdvm') or {}
if not mmdvm.get('detected'):
    log('perfil comprovado pendente: MMDVM ainda não confirmada');raise SystemExit(0)
# Keep RF up if the proven profile is already healthy.
if active('2pny-mmdvmhost.service') and active(gateway):raise SystemExit(0)
# NetworkManager dispatcher will call us again when a default route exists.
r=subprocess.run(['ip','-4','route','show','default'],stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True)
if r.returncode or not r.stdout.strip():
    log('perfil comprovado pendente: uplink ainda indisponível');raise SystemExit(0)
draft=readj(CFG); proven_cfg=proof['profile']
try:
    atomic(CFG,proven_cfg)
    result=subprocess.run(['timeout','-k','5','80','/usr/local/sbin/2pny-protocol-profiles','activate',proto],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=90)
finally:
    # Saved draft and active runtime are separate concepts; never destroy a draft.
    if draft and draft!=proven_cfg:atomic(CFG,draft)
if result.returncode==0:log('último perfil ativo comprovado restaurado: '+proto)
else:log('último perfil ativo comprovado permaneceu pendente: '+proto)
