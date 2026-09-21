#!/usr/bin/env python3
"""PU2PNY-OS 0.3.10 MQTT readiness gate.

Checks only the local MQTT endpoint declared by MMDVMHost.  It never changes
RF, protocol, broker configuration, credentials or the active radio state.
"""
import argparse, configparser, json, os, socket, sys, time
from pathlib import Path

CONFIG=Path("/var/lib/2pny/mmdvm/MMDVM-Host.ini")
STATUS=Path("/run/2pny/mqtt-preflight.json")

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
    if host.startswith("/"):
        return ("unix",host,0)
    if not 1 <= port <= 65535:
        raise RuntimeError("porta MQTT fora do intervalo válido")
    return ("tcp",host,port)

def check(ep, attempts=8, delay=.25):
    if ep is None:
        return True,"MQTT não habilitado no MMDVMHost"
    kind,host,port=ep
    last=""
    for _ in range(attempts):
        try:
            if kind=="unix":
                s=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM);s.settimeout(.7);s.connect(host)
            else:
                s=socket.create_connection((host,port),timeout=.7)
            s.close()
            return True,(f"MQTT pronto em {host}" if kind=="unix" else f"MQTT pronto em {host}:{port}")
        except OSError as exc:
            last=str(exc)
            time.sleep(delay)
    target=host if kind=="unix" else f"{host}:{port}"
    return False,f"MQTT local indisponível em {target}: {last or 'sem resposta'}"

def publish(ok,msg,ep=None):
    STATUS.parent.mkdir(parents=True,exist_ok=True)
    target=""
    if ep:
        kind,host,port=ep; target=host if kind=="unix" else f"{host}:{port}"
    tmp=STATUS.with_suffix(".tmp")
    tmp.write_text(json.dumps({"ok":bool(ok),"target":target,"message":msg,"updated":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime())},ensure_ascii=False)+"\n")
    os.chmod(tmp,0o644);os.replace(tmp,STATUS)

def main():
    ap=argparse.ArgumentParser(add_help=False)
    ap.add_argument("--quiet",action="store_true")
    args,_=ap.parse_known_args()
    try: ep=endpoint()
    except Exception as exc:
        msg=f"MQTT não pôde ser validado: {exc}";publish(False,msg,None);print(f"MQTT_PRECHECK_ERROR {msg}",file=sys.stderr);return 2
    ok,msg=check(ep)
    publish(ok,msg,ep)
    if not ok:
        print(f"MQTT_PRECHECK_ERROR {msg}",file=sys.stderr);return 3
    if not args.quiet: print(f"MQTT_PRECHECK_OK {msg}")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
