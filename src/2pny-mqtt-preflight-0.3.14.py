#!/usr/bin/env python3
"""PU2PNY-OS 0.3.14 MQTT protocol readiness gate.

Validates the effective MQTT endpoint used by MMDVMHost with a real MQTT 3.1.1
CONNECT/CONNACK exchange. It does not change RF, broker credentials or radio state.
"""
import argparse, configparser, json, os, socket, subprocess, sys, time
from pathlib import Path

CONFIG=Path("/var/lib/2pny/mmdvm/MMDVM-Host.ini")
STATUS=Path("/run/2pny/mqtt-preflight.json")
SERVICE="mosquitto.service"

def mqtt_log_enabled():
    """Return True only when MMDVMHost logging is configured to use MQTT."""
    cp=configparser.ConfigParser(interpolation=None,strict=False)
    cp.optionxform=str
    if not CONFIG.exists():
        return False
    cp.read(CONFIG)
    try:
        return int((cp.get("Log","MQTTLevel",fallback="0") or "0").strip()) > 0
    except (ValueError,TypeError):
        return False

def endpoint():
    cp=configparser.ConfigParser(interpolation=None,strict=False)
    cp.optionxform=str
    if not CONFIG.exists():
        raise RuntimeError("configuração MMDVMHost ausente")
    cp.read(CONFIG)
    if not cp.has_section("MQTT"):
        return None
    sec=cp["MQTT"]
    host=(sec.get("Host") or sec.get("Address") or "").strip()
    if not host:
        return None
    try: port=int((sec.get("Port") or "1883").strip())
    except ValueError: raise RuntimeError("porta MQTT inválida na configuração")
    if not 1 <= port <= 65535:
        raise RuntimeError("porta MQTT fora do intervalo válido")
    auth=str(sec.get("Auth") or "0").strip().lower() in ("1","true","yes","on")
    return {
        "kind":"unix" if host.startswith("/") else "tcp",
        "host":host,"port":port,
        "username":(sec.get("Username") or "") if auth else "",
        "password":(sec.get("Password") or "") if auth else "",
    }

def enc_len(n):
    out=bytearray()
    while True:
        digit=n%128;n//=128
        if n: digit|=0x80
        out.append(digit)
        if not n:return bytes(out)

def enc_str(value):
    data=str(value).encode("utf-8")
    if len(data)>65535: raise ValueError("campo MQTT muito longo")
    return len(data).to_bytes(2,"big")+data

def mqtt_connect_packet(ep):
    flags=0x02
    payload=enc_str("2pny-preflight-%d"%os.getpid())
    if ep.get("username"):
        flags|=0x80
        payload+=enc_str(ep["username"])
        flags|=0x40
        payload+=enc_str(ep.get("password",""))
    variable=enc_str("MQTT")+bytes((4,flags))+int(10).to_bytes(2,"big")
    body=variable+payload
    return bytes((0x10,))+enc_len(len(body))+body

def check_once(ep):
    if ep["kind"]=="unix":
        s=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM);s.settimeout(1.2);s.connect(ep["host"])
    else:
        s=socket.create_connection((ep["host"],ep["port"]),timeout=1.2)
    try:
        s.sendall(mqtt_connect_packet(ep))
        reply=b""
        while len(reply)<4:
            chunk=s.recv(4-len(reply))
            if not chunk: break
            reply+=chunk
        if len(reply)<4 or reply[0]!=0x20 or reply[1]!=0x02:
            return False,"broker respondeu sem CONNACK MQTT válido"
        rc=reply[3]
        if rc!=0:
            reasons={1:"protocolo rejeitado",2:"client ID rejeitado",3:"broker indisponível",4:"credenciais rejeitadas",5:"não autorizado"}
            return False,"CONNACK recusado: "+reasons.get(rc,"código %d"%rc)
        return True,"handshake MQTT confirmado"
    finally:
        try:
            s.sendall(b"\xe0\x00")
        except OSError:
            pass
        s.close()

def check(ep, attempts=12, delay=.4):
    if ep is None:return True,"MQTT não habilitado no MMDVMHost"
    last=""
    attempts=max(1,min(int(attempts),30))
    delay=max(.05,min(float(delay),2.0))
    for idx in range(attempts):
        try:
            ok,msg=check_once(ep)
            if ok:return True,msg
            last=msg
        except OSError as exc:
            last=str(exc)
        if idx+1<attempts:
            # Bounded short backoff: fast first retries, never aggressive polling.
            time.sleep(min(delay*(1.0+idx/4.0),1.5))
    target=ep["host"] if ep["kind"]=="unix" else f'{ep["host"]}:{ep["port"]}'
    return False,f"MQTT não respondeu corretamente em {target}: {last or 'sem resposta'}"

def service_snapshot():
    data={"service":SERVICE}
    try:
        p=subprocess.run(
            ["systemctl","show",SERVICE,"--no-pager",
             "--property=ActiveState,SubState,Result,ExecMainStatus"],
            text=True,capture_output=True,timeout=4)
        for line in (p.stdout or "").splitlines():
            if "=" in line:
                k,v=line.split("=",1);data[k]=v
    except Exception as exc:
        data["show_error"]=str(exc)
    return data

def ensure_service(wait_seconds=10.0):
    if os.geteuid()!=0:
        return False,"preflight sem privilégio não pode iniciar o broker",service_snapshot()
    wait_seconds=max(1.0,min(float(wait_seconds),20.0))
    for args in (
        ["systemctl","reset-failed",SERVICE],
        ["systemctl","enable",SERVICE],
    ):
        try: subprocess.run(args,text=True,capture_output=True,timeout=6)
        except Exception: pass
    try:
        p=subprocess.run(["systemctl","start",SERVICE],text=True,capture_output=True,timeout=12)
    except Exception as exc:
        snap=service_snapshot();return False,f"falha ao iniciar {SERVICE}: {exc}",snap
    if p.returncode!=0:
        msg=(p.stderr or p.stdout or "systemctl start falhou").strip()
        snap=service_snapshot();return False,f"{SERVICE} não iniciou: {msg}",snap
    deadline=time.monotonic()+wait_seconds
    while time.monotonic()<deadline:
        try:
            if subprocess.run(["systemctl","is-active","--quiet",SERVICE],timeout=3).returncode==0:
                return True,"broker service active",service_snapshot()
        except Exception:
            pass
        time.sleep(.25)
    snap=service_snapshot()
    return False,f"{SERVICE} não ficou active dentro de {wait_seconds:.0f}s",snap

def publish(ok,msg,ep=None,service=None):
    STATUS.parent.mkdir(parents=True,exist_ok=True)
    target=""
    if ep:
        target=ep["host"] if ep["kind"]=="unix" else f'{ep["host"]}:{ep["port"]}'
    payload={"ok":bool(ok),"target":target,"message":msg,
        "updated":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime())}
    if service: payload["service"]=service
    tmp=STATUS.with_suffix(".tmp")
    tmp.write_text(json.dumps(payload,ensure_ascii=False)+"\n")
    os.chmod(tmp,0o644);os.replace(tmp,STATUS)

def main():
    ap=argparse.ArgumentParser(add_help=False)
    ap.add_argument("--quiet",action="store_true")
    ap.add_argument("--no-publish",action="store_true")
    ap.add_argument("--respect-log-level",action="store_true")
    ap.add_argument("--ensure-service",action="store_true")
    ap.add_argument("--attempts",type=int,default=12)
    ap.add_argument("--delay",type=float,default=.4)
    ap.add_argument("--service-wait",type=float,default=10.0)
    args,_=ap.parse_known_args()

    # The systemd pre-start check runs as the unprivileged mmdvm user. During
    # RF bootstrap MQTTLevel=0 by design, so UART proof remains independent.
    if args.respect_log_level and not mqtt_log_enabled():
        if not args.quiet:
            print("MQTT_PRECHECK_OK MQTT desativado durante bootstrap")
        return 0

    service=None
    if args.ensure_service:
        ok_s,msg_s,service=ensure_service(args.service_wait)
        if not ok_s:
            if not args.no_publish:
                try: publish(False,msg_s,None,service)
                except OSError: pass
            print("MQTT_PRECHECK_ERROR "+msg_s,file=sys.stderr);return 4

    try:
        ep=endpoint()
    except Exception as exc:
        msg=f"MQTT não pôde ser validado: {exc}"
        if not args.no_publish:
            try: publish(False,msg,None,service)
            except OSError: pass
        print("MQTT_PRECHECK_ERROR "+msg,file=sys.stderr);return 2

    ok,msg=check(ep,args.attempts,args.delay)
    if service is None and os.geteuid()==0:
        service=service_snapshot()
    if not args.no_publish:
        try: publish(ok,msg,ep,service)
        except OSError as exc:
            # Diagnostic persistence must never turn a valid MQTT handshake
            # into a false radio failure.
            if not args.quiet:
                print("MQTT_PRECHECK_WARN status não persistido: "+str(exc),file=sys.stderr)
    if not ok:
        print("MQTT_PRECHECK_ERROR "+msg,file=sys.stderr);return 3
    if not args.quiet: print("MQTT_PRECHECK_OK "+msg)
    return 0

if __name__=="__main__":
    raise SystemExit(main())
