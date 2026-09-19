#!/usr/bin/env python3
"""Confirm a Nextion connected to the MMDVM serial display channel."""
import json,os,subprocess,time
from pathlib import Path
PROBE=Path("/var/lib/2pny/hardware-probe.json")
STATUS=Path("/var/lib/2pny/display-runtime.json")

def load(p):
    try:return json.loads(p.read_text())
    except Exception:return {}
def save(p,d):
    t=p.with_suffix(".tmp");t.write_text(json.dumps(d,ensure_ascii=False,indent=2)+"\n");os.chmod(t,0o600);os.replace(t,p)
def active(u):return subprocess.run(["systemctl","is-active","--quiet",u]).returncode==0
def probe():
    for _ in range(4):
        sub=subprocess.Popen(["mosquitto_sub","-h","127.0.0.1","-t","host/display-out","-C","1","-W","3"],
                             stdout=subprocess.PIPE,stderr=subprocess.DEVNULL)
        time.sleep(.12)
        p=subprocess.run(["mosquitto_pub","-h","127.0.0.1","-t","host/display-in","-s"],
                         input=b"connect\xff\xff\xff",stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=2)
        try:out=sub.communicate(timeout=3.5)[0]
        except Exception:sub.kill();out=b""
        clean=out.replace(b"\xff",b"").decode("ascii","replace").strip("\x00\r\n ")
        if p.returncode==0 and "comok" in clean.lower():return clean
        time.sleep(.25)
    return ""

d=load(PROBE);m=d.get("mmdvm") or {};disp=d.get("display") or {}
if not m.get("detected"):
    print("MMDVM not confirmed");raise SystemExit(2)
if not active("2pny-mmdvmhost.service"):
    print("MMDVMHost not active yet");raise SystemExit(3)
response=probe()
if response:
    parts=[x.strip() for x in response.split(",")]
    model=parts[2] if len(parts)>=3 and parts[2] else "Nextion"
    d["display"]={"detected":True,"class":"nextion_mmdvm","state":"protocol_confirmed",
                  "model":model,"port":"modem","confidence":"protocol","response":response,
                  "message":"Nextion confirmada automaticamente pelo canal serial da MMDVM."}
    save(PROBE,d)
    subprocess.run(["/usr/local/sbin/2pny-display-apply"],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    print("NEXTION_AUTO_OK");raise SystemExit(0)

# Do not fall back to the legacy Pi-Star/MMDVM-Display renderer.  Keep the
# PU2PNY renderer selected and expose a warning for Expert diagnostics.
disp.update({"class":"nextion_mmdvm","state":"auto_selected_unconfirmed","port":"modem","auto_selected":True,
             "message":"Canal Nextion via MMDVM selecionado; a tela não respondeu ao comando de identificação."})
d["display"]=disp;save(PROBE,d)
st=load(STATUS);st.update({"state":"warning","message":disp["message"],"updated":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime())});save(STATUS,st)
subprocess.run(["/usr/local/sbin/2pny-display-apply"],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
print("NEXTION_AUTO_UNCONFIRMED");raise SystemExit(4)
