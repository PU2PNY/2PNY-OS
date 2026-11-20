#!/usr/bin/env python3
"""Apply and persist PU2PNY clock changes through the existing systemd path unit."""
import datetime, json, os, re, subprocess, tempfile
from pathlib import Path

RUN=Path("/run/2pny")
TZ_RE=re.compile(r"^timezone-request-([0-9]{10,32})\.json$")
TIME_RE=re.compile(r"^time-request-([0-9]{10,32})\.json$")
ZONE_RE=re.compile(r"^[A-Za-z0-9_+.-]+(?:/[A-Za-z0-9_+.-]+)*$")
ZONEINFO=Path("/usr/share/zoneinfo")
CLOCK=Path("/var/lib/2pny/settings/clock.json")
LOCALTIME=Path("/etc/localtime")
TIMEZONE=Path("/etc/timezone")

def clock_settings():
    try:
        value=json.loads(CLOCK.read_text())
        return value if isinstance(value,dict) else {}
    except FileNotFoundError:
        return {}

def save_settings(settings):
    CLOCK.parent.mkdir(mode=0o755,parents=True,exist_ok=True)
    fd,name=tempfile.mkstemp(prefix=".clock-",dir=CLOCK.parent)
    try:
        with os.fdopen(fd,"w",encoding="utf-8") as stream:
            json.dump(settings,stream)
            os.fchmod(stream.fileno(),0o644)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name,CLOCK)
    finally:
        Path(name).unlink(missing_ok=True)

def set_ntp(enabled):
    p=run(["timedatectl","set-ntp","true" if enabled else "false"],5)
    if p.returncode:
        raise RuntimeError("falha ao configurar NTP: "+p.stderr.strip()[-240:])


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
    try:
        target=os.readlink(LOCALTIME)
        prefix=str(ZONEINFO)+"/"
        if target.startswith(prefix):
            return target[len(prefix):]
    except OSError:
        pass
    return ""

def write_zone(tz):
    with tempfile.TemporaryDirectory(prefix=".pu2pny-clock-",dir=LOCALTIME.parent) as directory:
        temporary=Path(directory)/"localtime"
        temporary.symlink_to(ZONEINFO/tz)
        os.replace(temporary,LOCALTIME)
        temporary=Path(directory)/"timezone"
        temporary.write_text(tz+"\n")
        os.chmod(temporary,0o644)
        os.replace(temporary,TIMEZONE)

def set_timezone(req,request_id):
    settings=clock_settings()
    action=req.get("action","timezone")
    if action=="initialize-zone" and (settings.get("timezone") or settings.get("time_source")=="manual"):
        finish("timezone",request_id,{"ok":True,"timezone":settings.get("timezone") or effective_timezone(),"unchanged":True})
        return
    if action=="sync-google":
        set_ntp(True)
        save_settings({**settings,"ntp":True,"time_source":"ntp"})
        finish("timezone",request_id,{"ok":True,"ntp":True})
        return
    if action=="dst-display":
        save_settings({**settings,"dst_manual":req.get("dst_manual") is True})
        finish("timezone",request_id,{"ok":True,"timezone":effective_timezone()})
        return
    if action not in ("timezone","auto-time","initialize-zone"):
        raise ValueError("ação de relógio inválida")
    tz=str(req.get("timezone") or "").strip()
    zone=ZONEINFO/tz
    if (not ZONE_RE.fullmatch(tz) or ".." in tz or len(tz)>128
            or not zone.is_file()):
        raise ValueError("fuso horário inválido")
    with zone.open("rb") as stream:
        if stream.read(4)!=b"TZif":
            raise ValueError("arquivo de fuso inválido")
    previous=effective_timezone()
    try:
        write_zone(tz)
        if action in ("auto-time","initialize-zone"):
            if action=="initialize-zone" and settings.get("ntp") is not False:
                epoch_ms=req.get("epoch_ms")
                if (type(epoch_ms) is int and 1704067200000<epoch_ms<4102444800000
                        and not Path("/run/systemd/timesync/synchronized").exists()
                        and not Path("/run/chrony/chronyd.pid").exists()):
                    epoch=epoch_ms/1000
                    now=datetime.datetime.now(datetime.timezone.utc).timestamp()
                    if abs(epoch-now)>120:
                        set_ntp(False)
                        # UTC epoch is unambiguous even across a DST transition.
                        result=run(["timedatectl","set-time","@"+str(int(epoch))],5)
                        if result.returncode:
                            set_ntp(True)
                            raise RuntimeError("não foi possível iniciar o relógio com a hora do navegador")
            set_ntp(True)
            settings.update(ntp=True,time_source="ntp")
        settings.update(timezone=tz,timezone_source="manual" if action=="timezone" else "browser-iana")
        save_settings(settings)
    except Exception:
        if previous and previous!=tz:
            write_zone(previous)
        raise
    finish("timezone",request_id,{"ok":True,"timezone":tz,"method":"symlink"})

def set_time(req,request_id):
    value=str(req.get("local_time") or "").strip()
    try:
        parsed=datetime.datetime.strptime(value,"%Y-%m-%dT%H:%M:%S")
    except ValueError:
        try:parsed=datetime.datetime.strptime(value,"%Y-%m-%dT%H:%M")
        except ValueError:raise ValueError("data/hora inválida; use AAAA-MM-DDTHH:MM[:SS]")
    if not 2020<=parsed.year<=2099:raise ValueError("ano fora do intervalo permitido")
    settings=clock_settings()
    set_ntp(False)
    wanted=parsed.strftime("%Y-%m-%d %H:%M:%S")
    p=run(["timedatectl","set-time",wanted],10)
    if p.returncode:
        if settings.get("ntp") is not False:
            set_ntp(True)
        raise RuntimeError("timedatectl: "+(p.stderr or p.stdout or "falhou").strip()[-800:])
    out=run(["date","+%Y-%m-%dT%H:%M:%S"],5)
    effective=(out.stdout or "").strip()
    try:
        actual=datetime.datetime.strptime(effective,"%Y-%m-%dT%H:%M:%S")
        if abs((actual-parsed).total_seconds())>5:raise RuntimeError(f"hora não confirmada: solicitado={value}, efetivo={effective or '—'}")
    except ValueError:raise RuntimeError("não foi possível confirmar a hora efetiva")
    if Path("/usr/sbin/fake-hwclock").is_file():
        saved=run(["/usr/sbin/fake-hwclock","save","force"],3)
        if saved.returncode:
            raise RuntimeError("não foi possível gravar a hora para o próximo boot")
    save_settings({**settings,"ntp":False,"time_source":"manual"})
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
    for _ in range(32):
        rows=candidates()
        if not rows:return 0
        process_one(rows[0])
    return 0

if __name__=="__main__":raise SystemExit(main())
