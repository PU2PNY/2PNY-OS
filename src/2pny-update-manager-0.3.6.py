#!/usr/bin/env python3
"""Verified PU2PNY staged application/component updater with local rollback."""
import fcntl,hashlib,json,os,re,shutil,subprocess,sys,tarfile,tempfile,time,urllib.request
from pathlib import Path

STATE=Path("/var/lib/2pny")
BASE=STATE/"updates";CACHE=BASE/"cache";BACKUPS=STATE/"backups/app-update";STATUS=BASE/"status.json";STAGED=BASE/"staged.json";LOCK=BASE/"update.lock"
ALLOWED_PREFIX="https://github.com/PU2PNY/2PNY-OS/releases/download/"
ALLOWED_ROOTS=("/usr/local/bin/","/usr/local/sbin/","/usr/local/lib/","/usr/share/2pny/","/etc/systemd/system/","/etc/NetworkManager/dispatcher.d/","/etc/2pny/")

def atomic_json(path,obj,mode=0o600):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_name("."+path.name+".tmp")
    tmp.write_text(json.dumps(obj,ensure_ascii=False,separators=(",",":")))
    os.chmod(tmp,mode);os.replace(tmp,path)

def atomic_status(**kw):
    kw["updated"]=time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime())
    atomic_json(STATUS,kw)

def die(msg,code=2):
    atomic_status(state="error",message=msg)
    print(msg,file=sys.stderr);raise SystemExit(code)

def run(*args,timeout=120):
    return subprocess.run(args,text=True,capture_output=True,timeout=timeout)

def sha256(p):
    h=hashlib.sha256()
    with open(p,"rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""):h.update(b)
    return h.hexdigest()

def validate_request(url,digest,version):
    if url and not url.startswith(ALLOWED_PREFIX):die("URL de atualização não pertence ao repositório oficial")
    if not re.fullmatch(r"[0-9a-fA-F]{64}",digest):die("SHA-256 inválido")
    if not re.fullmatch(r"[A-Za-z0-9._-]{3,64}",version):die("versão inválida")

def safe_rel(name):
    if not name.startswith("payload/") or name.startswith("/") or ".." in Path(name).parts:return False
    rel="/"+name[len("payload/"):]
    return any(rel.startswith(root) for root in ALLOWED_ROOTS)

def list_backups():
    BACKUPS.mkdir(parents=True,exist_ok=True)
    return sorted([p.name for p in BACKUPS.glob("*.tar.gz")],reverse=True)

def staged_info():
    try:return json.loads(STAGED.read_text())
    except Exception:return {}

def download(url,digest,version):
    validate_request(url,digest,version)
    CACHE.mkdir(parents=True,exist_ok=True)
    pkg=CACHE/(version+".tar.gz");part=CACHE/(version+".tar.gz.part")
    part.unlink(missing_ok=True)
    req=urllib.request.Request(url,headers={"User-Agent":"PU2PNY-OS/0.3.6 updater","Accept":"application/octet-stream"})
    downloaded=0;total=0;last_percent=-5;last_bytes=0
    atomic_status(state="downloading",message="Iniciando download oficial...",version=version,progress_percent=0,downloaded_bytes=0,total_bytes=None)
    try:
        with urllib.request.urlopen(req,timeout=25) as resp, open(part,"wb") as out:
            try: total=int(resp.headers.get("Content-Length") or 0)
            except Exception: total=0
            while True:
                chunk=resp.read(1024*1024)
                if not chunk:break
                out.write(chunk);downloaded+=len(chunk)
                pct=int(downloaded*100/total) if total>0 else None
                should=(pct is not None and pct>=last_percent+5) or (pct is None and downloaded-last_bytes>=8*1024*1024)
                if should:
                    if pct is not None:last_percent=pct
                    last_bytes=downloaded
                    atomic_status(state="downloading",message="Baixando pacote oficial...",version=version,
                                  progress_percent=min(99,pct) if pct is not None else None,
                                  downloaded_bytes=downloaded,total_bytes=total or None)
        if downloaded<=0:die("O download terminou vazio; nenhuma instalação foi iniciada")
        os.replace(part,pkg)
    except Exception as e:
        part.unlink(missing_ok=True)
        die("Falha ao baixar atualização oficial; nada foi instalado: "+str(e))
    atomic_status(state="verifying",message="Download concluído. Verificando SHA-256...",version=version,
                  progress_percent=100,downloaded_bytes=downloaded,total_bytes=total or downloaded)
    got=sha256(pkg)
    if got.lower()!=digest.lower():
        pkg.unlink(missing_ok=True);STAGED.unlink(missing_ok=True)
        die("SHA-256 do pacote não confere; pacote descartado e atualização cancelada")
    meta={"version":version,"sha256":digest.lower(),"path":str(pkg),"bytes":downloaded,"verified":True,
          "downloaded_at":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime())}
    atomic_json(STAGED,meta)
    atomic_status(state="downloaded",message="Download 100% concluído e SHA-256 validado. Pronto para instalar quando você confirmar.",
                  version=version,progress_percent=100,downloaded_bytes=downloaded,total_bytes=total or downloaded,verified=True)
    print(json.dumps(meta,ensure_ascii=False))

def extract_validated(pkg):
    work=Path(tempfile.mkdtemp(prefix="pny-update-",dir="/run" if Path("/run").is_dir() else None))
    try:
        with tarfile.open(pkg,"r:gz") as tf:
            members=tf.getmembers()
            for m in members:
                name=str(m.name or "");parts=Path(name).parts
                if not name or name.startswith("/") or ".." in parts:die("Pacote contém caminho não autorizado")
                if name!="manifest.json" and name!="payload" and not name.startswith("payload/"):die("Pacote contém caminho não autorizado")
                if m.issym() or m.islnk() or m.isdev():die("Pacote contém tipo de arquivo não permitido")
                if m.isfile() and name!="manifest.json" and not safe_rel(name):die("Pacote contém arquivo fora das áreas autorizadas")
            tf.extractall(work)
        manifest=json.loads((work/"manifest.json").read_text())
        files=manifest.get("files") or []
        if not isinstance(files,list) or not files:die("Manifesto de atualização vazio")
        targets=[]
        for rel in files:
            rel=str(rel);src=work/"payload"/rel.lstrip("/");dst=Path(rel)
            if not src.is_file() or not any(rel.startswith(root) for root in ALLOWED_ROOTS):die("Manifesto contém arquivo inválido")
            targets.append((src,dst))
        return work,manifest,targets
    except Exception:
        shutil.rmtree(work,ignore_errors=True);raise

def install_staged(digest,version,keep):
    validate_request("",digest,version)
    meta=staged_info()
    if not meta.get("verified") or meta.get("version")!=version or str(meta.get("sha256","")).lower()!=digest.lower():
        die("Não existe download verificado desta versão. Baixe novamente antes de instalar.")
    pkg=Path(str(meta.get("path") or ""))
    if not pkg.is_file():die("Pacote baixado não foi encontrado. Baixe novamente.")
    if sha256(pkg).lower()!=digest.lower():die("O pacote baixado mudou após a validação; instalação cancelada.")
    BACKUPS.mkdir(parents=True,exist_ok=True)
    atomic_status(state="validating",message="Validando conteúdo local antes de alterar o sistema...",version=version,progress_percent=100,verified=True)
    work,manifest,targets=extract_validated(pkg)
    backup=None
    try:
        stamp=time.strftime("%Y%m%dT%H%M%SZ",time.gmtime())
        backup=BACKUPS/(stamp+"-"+str(manifest.get("from_compatible") or "current")+".tar.gz")
        existing=[str(dst).lstrip("/") for _,dst in targets if dst.exists() and dst.is_file()]
        if existing:
            r=run("tar","-C","/","-czf",str(backup),*existing,timeout=120)
            if r.returncode:die("Não foi possível criar o ponto de retorno; instalação cancelada")
        atomic_status(state="installing",message="Aplicando componentes já baixados e validados. Não desligue a alimentação.",version=version,
                      progress_percent=100,backup=backup.name if backup and backup.exists() else "",verified=True)
        for src,dst in targets:
            dst.parent.mkdir(parents=True,exist_ok=True)
            tmp=dst.with_name("."+dst.name+".pny-update")
            shutil.copy2(src,tmp);os.replace(tmp,dst)
        Path("/etc/2pny").mkdir(parents=True,exist_ok=True)
        Path("/etc/2pny/version").write_text(version+"\n")
        run("systemctl","daemon-reload",timeout=20)
        for unit in ("2pny-station.service","2pny-display-core.service","2pny-netdiag.service"):
            run("systemctl","try-restart",unit,timeout=20)
        run("systemctl","try-restart","2pnyd.service",timeout=20)
        if not keep and backup and backup.exists():backup.unlink()
        STAGED.unlink(missing_ok=True)
        atomic_status(state="done",message="Atualização aplicada. Reinicie o hotspot se a nova versão solicitar.",version=version,
                      progress_percent=100,backup=backup.name if keep and backup and backup.exists() else "",verified=True)
    finally:
        shutil.rmtree(work,ignore_errors=True)

def install(url,digest,version,keep):
    # Backward-compatible CLI: still stages/validates first, then applies.
    download(url,digest,version)
    install_staged(digest,version,keep)

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
    BASE.mkdir(parents=True,exist_ok=True)
    lock=open(LOCK,"a+")
    try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    except BlockingIOError:die("Já existe uma operação de atualização em andamento",3)
    cmd=sys.argv[1] if len(sys.argv)>1 else "status"
    if cmd=="status":
        st={}
        try:st=json.loads(STATUS.read_text())
        except Exception:st={"state":"idle"}
        staged=staged_info()
        st["staged"]=staged if staged.get("verified") else None
        st["backups"]=list_backups();print(json.dumps(st,ensure_ascii=False))
    elif cmd=="download" and len(sys.argv)==5:download(sys.argv[2],sys.argv[3],sys.argv[4])
    elif cmd=="install-staged" and len(sys.argv)==5:install_staged(sys.argv[2],sys.argv[3],sys.argv[4]=="1")
    elif cmd=="install" and len(sys.argv)==6:install(sys.argv[2],sys.argv[3],sys.argv[4],sys.argv[5]=="1")
    elif cmd=="rollback" and len(sys.argv)==3:rollback(sys.argv[2])
    elif cmd=="delete-backup" and len(sys.argv)==3:
        name=sys.argv[2]
        if name not in list_backups():die("Ponto de retorno não encontrado")
        (BACKUPS/name).unlink();print(json.dumps({"ok":True}))
    else:die("uso: 2pny-update-manager status|download URL SHA VERSION|install-staged SHA VERSION KEEP|install URL SHA VERSION KEEP|rollback BACKUP|delete-backup BACKUP")
if __name__=="__main__":main()
