#!/usr/bin/env python3
"""Verified PU2PNY application/component updater with local rollback."""
import hashlib,json,os,re,shutil,subprocess,sys,tarfile,tempfile,time
from pathlib import Path
from urllib.parse import urlparse
STATE=Path("/var/lib/2pny")
BASE=STATE/"updates";CACHE=BASE/"cache";BACKUPS=STATE/"backups/app-update";STATUS=BASE/"status.json"
ALLOWED_PREFIX="https://github.com/PU2PNY/2PNY-OS/releases/download/"
ALLOWED_ROOTS=("/usr/local/bin/","/usr/local/sbin/","/usr/local/lib/","/usr/share/2pny/","/etc/systemd/system/","/etc/NetworkManager/dispatcher.d/","/etc/2pny/")

def atomic_status(**kw):
    BASE.mkdir(parents=True,exist_ok=True);kw["updated"]=time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime())
    tmp=STATUS.with_suffix(".tmp");tmp.write_text(json.dumps(kw,ensure_ascii=False));os.chmod(tmp,0o600);os.replace(tmp,STATUS)

def die(msg,code=2):
    atomic_status(state="error",message=msg);print(msg,file=sys.stderr);raise SystemExit(code)

def run(*args,timeout=120):
    return subprocess.run(args,text=True,capture_output=True,timeout=timeout)

def sha256(p):
    h=hashlib.sha256()
    with open(p,"rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""):h.update(b)
    return h.hexdigest()

def safe_rel(name):
    if not name.startswith("payload/") or name.startswith("/") or ".." in Path(name).parts:return False
    rel="/"+name[len("payload/"):]
    return any(rel.startswith(root) for root in ALLOWED_ROOTS)

def list_backups():
    BACKUPS.mkdir(parents=True,exist_ok=True)
    return sorted([p.name for p in BACKUPS.glob("*.tar.gz")],reverse=True)

def install(url,digest,version,keep):
    if not url.startswith(ALLOWED_PREFIX):die("URL de atualização não pertence ao repositório oficial")
    if not re.fullmatch(r"[0-9a-fA-F]{64}",digest):die("SHA-256 inválido")
    if not re.fullmatch(r"[A-Za-z0-9._-]{3,64}",version):die("versão inválida")
    CACHE.mkdir(parents=True,exist_ok=True);BACKUPS.mkdir(parents=True,exist_ok=True)
    pkg=CACHE/(version+".tar.gz")
    atomic_status(state="downloading",message="Baixando pacote oficial verificado...",version=version)
    r=run("curl","--fail","--location","--silent","--show-error","--max-time","180","-o",str(pkg),url,timeout=200)
    if r.returncode:die("Falha ao baixar atualização oficial: "+(r.stderr.strip() or "erro de rede"))
    if sha256(pkg).lower()!=digest.lower():die("SHA-256 do pacote não confere; atualização cancelada")
    atomic_status(state="validating",message="Validando conteúdo e ponto de retorno...",version=version)
    work=Path(tempfile.mkdtemp(prefix="pny-update-",dir="/run" if Path("/run").is_dir() else None))
    try:
        with tarfile.open(pkg,"r:gz") as tf:
            members=tf.getmembers()
            for m in members:
                name=str(m.name or "")
                parts=Path(name).parts
                if not name or name.startswith("/") or ".." in parts:
                    die("Pacote contém caminho não autorizado")
                if name!="manifest.json" and name!="payload" and not name.startswith("payload/"):
                    die("Pacote contém caminho não autorizado")
                if m.issym() or m.islnk() or m.isdev():
                    die("Pacote contém tipo de arquivo não permitido")
                if m.isfile() and name!="manifest.json" and not safe_rel(name):
                    die("Pacote contém arquivo fora das áreas autorizadas")
            tf.extractall(work)
        manifest=json.loads((work/"manifest.json").read_text())
        files=manifest.get("files") or []
        if not isinstance(files,list) or not files:die("Manifesto de atualização vazio")
        targets=[]
        for rel in files:
            rel=str(rel)
            src=work/"payload"/rel.lstrip("/")
            dst=Path(rel)
            if not src.is_file() or not any(rel.startswith(root) for root in ALLOWED_ROOTS):die("Manifesto contém arquivo inválido")
            targets.append((src,dst))
        stamp=time.strftime("%Y%m%dT%H%M%SZ",time.gmtime())
        backup=BACKUPS/(stamp+"-"+str(manifest.get("from_compatible") or "current")+".tar.gz")
        existing=[str(dst).lstrip("/") for _,dst in targets if dst.exists() and dst.is_file()]
        if existing:
            r=run("tar","-C","/","-czf",str(backup),*existing,timeout=120)
            if r.returncode:die("Não foi possível criar o ponto de retorno")
        atomic_status(state="installing",message="Aplicando componentes validados...",version=version,backup=backup.name if backup.exists() else "")
        for src,dst in targets:
            dst.parent.mkdir(parents=True,exist_ok=True)
            tmp=dst.with_name("."+dst.name+".pny-update")
            shutil.copy2(src,tmp);os.replace(tmp,dst)
        (Path("/etc/2pny")).mkdir(parents=True,exist_ok=True)
        (Path("/etc/2pny/version")).write_text(version+"\n")
        run("systemctl","daemon-reload",timeout=20)
        for unit in ("2pny-station.service","2pny-display-core.service","2pny-netdiag.service"):
            run("systemctl","try-restart",unit,timeout=20)
        # Restart the web service last because it may terminate this request.
        run("systemctl","try-restart","2pnyd.service",timeout=20)
        if not keep and backup.exists():backup.unlink()
        atomic_status(state="done",message="Atualização aplicada. Reinicie o hotspot se solicitado pela nova versão.",version=version,backup=backup.name if keep and backup.exists() else "")
    finally:
        shutil.rmtree(work,ignore_errors=True)

def rollback(name):
    if name not in list_backups():die("Ponto de retorno não encontrado")
    p=BACKUPS/name
    atomic_status(state="rollback",message="Restaurando versão anterior...",backup=name)
    r=run("tar","-C","/","-xzf",str(p),timeout=120)
    if r.returncode:die("Falha ao restaurar o ponto de retorno")
    run("systemctl","daemon-reload",timeout=20)
    for u in ("2pny-station.service","2pny-display-core.service","2pny-netdiag.service","2pnyd.service"):run("systemctl","try-restart",u,timeout=20)
    atomic_status(state="done",message="Rollback aplicado. Reinicie o hotspot para concluir.",backup=name)

def main():
    cmd=sys.argv[1] if len(sys.argv)>1 else "status"
    if cmd=="status":
        st={}
        try:st=json.loads(STATUS.read_text())
        except Exception:st={"state":"idle"}
        st["backups"]=list_backups();print(json.dumps(st,ensure_ascii=False))
    elif cmd=="install" and len(sys.argv)==6:install(sys.argv[2],sys.argv[3],sys.argv[4],sys.argv[5]=="1")
    elif cmd=="rollback" and len(sys.argv)==3:rollback(sys.argv[2])
    elif cmd=="delete-backup" and len(sys.argv)==3:
        name=sys.argv[2]
        if name not in list_backups():die("Ponto de retorno não encontrado")
        (BACKUPS/name).unlink();print(json.dumps({"ok":True}))
    else:die("uso: 2pny-update-manager status|install URL SHA VERSION KEEP|rollback BACKUP|delete-backup BACKUP")
if __name__=="__main__":main()
