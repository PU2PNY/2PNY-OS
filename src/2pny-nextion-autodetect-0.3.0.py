#!/usr/bin/env python3
"""PU2PNY Nextion auto-detection 0.3.0.

Never opens the modem UART while MMDVMHost owns it. It first asks the local
MMDVM MQTT display bridge for a Nextion connect reply. If the board exposes a
display channel but identification is silent, it applies the safe Nextion-via-
MMDVM profile and accepts it only when the display core remains operational.
"""
import json,os,subprocess,time
from pathlib import Path
PROBE=Path("/var/lib/2pny/hardware-probe.json");OVR=Path("/var/lib/2pny/display-override.json")

def load():
    try:return json.loads(PROBE.read_text())
    except Exception:return {}
def save(d):
    t=PROBE.with_suffix(".tmp");t.write_text(json.dumps(d,ensure_ascii=False,indent=2)+"\n");os.chmod(t,0o600);os.replace(t,PROBE)
def active(unit):
    return subprocess.run(["systemctl","is-active","--quiet",unit]).returncode==0
def mqtt_probe():
    for _ in range(3):
        sub=subprocess.Popen(["mosquitto_sub","-h","127.0.0.1","-t","host/display-out","-C","1","-W","2"],stdout=subprocess.PIPE,stderr=subprocess.DEVNULL)
        time.sleep(.15)
        try:
            subprocess.run(["bash","-lc","printf 'connect\\377\\377\\377' | mosquitto_pub -h 127.0.0.1 -t host/display-in -s"],timeout=2,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
            out=sub.communicate(timeout=3)[0]
        except Exception:
            sub.kill();out=b""
        if b"comok" in out.lower():return out.replace(b"\xff",b"").decode("ascii","replace").strip()
    return ""
def main():
    d=load();m=d.get("mmdvm") or {};disp=d.get("display") or {}
    if not m.get("detected"):print("MMDVM not confirmed");return 2
    if disp.get("detected") and disp.get("class") in ("nextion","nextion_mmdvm"):
        print("Nextion already confirmed");return 0
    if disp.get("state")!="mmdvm_display_candidate":
        print("No MMDVM display candidate");return 3
    response=mqtt_probe() if active("2pny-mmdvmhost.service") else ""
    override={"enabled":True,"type":"nextion_mmdvm","speed":9600,"layout":2,"auto":True,"updated":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime())}
    OVR.write_text(json.dumps(override,ensure_ascii=False));os.chmod(OVR,0o600)
    p=subprocess.run(["/usr/local/sbin/2pny-display-apply"],text=True,capture_output=True,timeout=12)
    time.sleep(1)
    core=active("2pny-display-core.service") or active("2pny-display.service")
    if response or core:
        d["display"]={"detected":True,"class":"nextion_mmdvm","state":"auto_configured","model":"Nextion via MMDVM","port":"modem",
                      "confidence":"protocol" if response else "operational","response":response,
                      "message":"Nextion configurada automaticamente pelo canal de display da MMDVM."}
        save(d);print("NEXTION_AUTO_OK");return 0
    # Leave candidate intact so Expert can diagnose; do not alter RF.
    print((p.stderr or p.stdout or "Nextion did not become operational").strip());return 4
if __name__=="__main__":raise SystemExit(main())
