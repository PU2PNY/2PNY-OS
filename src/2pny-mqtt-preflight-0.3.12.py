#!/usr/bin/env python3
"""PU2PNY-OS 0.3.12 MQTT protocol readiness gate.

Validates the effective MQTT endpoint used by MMDVMHost with a real MQTT 3.1.1
CONNECT/CONNACK exchange. It does not change RF, broker credentials or radio state.
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

def check(ep, attempts=10, delay=.3):
    if ep is None:return True,"MQTT não habilitado no MMDVMHost"
    last=""
    for _ in range(attempts):
        try:
            ok,msg=check_once(ep)
            if ok:return True,msg
            last=msg
        except OSError as exc:
            last=str(exc)
        time.sleep(delay)
    target=ep["host"] if ep["kind"]=="unix" else f'{ep["host"]}:{ep["port"]}'
    return False,f"MQTT não respondeu corretamente em {target}: {last or 'sem resposta'}"

def publish(ok,msg,ep=None):
    STATUS.parent.mkdir(parents=True,exist_ok=True)
    target=""
    if ep:
        target=ep["host"] if ep["kind"]=="unix" else f'{ep["host"]}:{ep["port"]}'
    tmp=STATUS.with_suffix(".tmp")
    tmp.write_text(json.dumps({"ok":bool(ok),"target":target,"message":msg,
        "updated":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime())},ensure_ascii=False)+"\n")
    os.chmod(tmp,0o644);os.replace(tmp,STATUS)

def main():
    ap=argparse.ArgumentParser(add_help=False);ap.add_argument("--quiet",action="store_true")
    args,_=ap.parse_known_args()
    try: ep=endpoint()
    except Exception as exc:
        msg=f"MQTT não pôde ser validado: {exc}";publish(False,msg,None)
        print("MQTT_PRECHECK_ERROR "+msg,file=sys.stderr);return 2
    ok,msg=check(ep);publish(ok,msg,ep)
    if not ok:
        print("MQTT_PRECHECK_ERROR "+msg,file=sys.stderr);return 3
    if not args.quiet: print("MQTT_PRECHECK_OK "+msg)
    return 0

if __name__=="__main__":
    raise SystemExit(main())
