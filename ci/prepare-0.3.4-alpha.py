#!/usr/bin/env python3
from pathlib import Path
import os, shutil, subprocess, sys

root=Path(sys.argv[1]).resolve()
repo=Path(__file__).resolve().parents[1]
version="0.3.4-alpha"

def install(src,dst,mode):
    target=root/dst
    target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(repo/src,target)
    os.chmod(target,mode)

# 0.3.4 is a narrow corrective overlay on top of the complete 0.3.3 build.
install("src/2pnyd-main-0.3.4.go","src/2pnyd/main.go",0o644)
install("src/wizard-0.3.4.html","rootfs-overlay/usr/share/2pny/wizard.html",0o644)
install("src/dashboard-0.3.4.html","rootfs-overlay/usr/share/2pny/dashboard.html",0o644)
install("src/internet-0.3.4.html","rootfs-overlay/usr/share/2pny/internet.html",0o644)
install("src/aprs-0.3.4.html","rootfs-overlay/usr/share/2pny/aprs.html",0o644)
install("src/expert-0.3.4.html","rootfs-overlay/usr/share/2pny/expert.html",0o644)
install("src/ui-common-0.3.4.js","rootfs-overlay/usr/share/2pny/ui-common-0.3.0.js",0o644)

install("src/2pny-network-switch-0.3.4","rootfs-overlay/usr/local/sbin/2pny-network-switch",0o755)
install("src/2pny-network-core-0.3.4","rootfs-overlay/usr/local/sbin/2pny-network-core",0o755)
install("src/2pny-protocol-network-apply-all-0.3.4.py","rootfs-overlay/usr/local/sbin/2pny-protocol-network-apply",0o755)
install("src/2pny-mqtt-preflight-0.3.4.py","rootfs-overlay/usr/local/sbin/2pny-mqtt-preflight",0o755)
install("src/2pny-mmdvmhost-0.3.4.service","rootfs-overlay/etc/systemd/system/2pny-mmdvmhost.service",0o644)
install("src/2pny-netdiag-0.3.4.py","rootfs-overlay/usr/local/sbin/2pny-netdiag",0o755)
(root/"rootfs-overlay/etc/2pny/version").write_text(version+"\n")

# Nextion: preserve the proven multi-display core, but stop clearing the whole
# screen on every refresh. Add clock/uplink/IP to standby and origin/duration
# to active pages without changing HMI/TFT.
p=root/"rootfs-overlay/usr/local/sbin/2pny-display-core"
s=p.read_text()
s=s.replace(
'RUN=Path("/run/2pny")\nHW=STATE/"hardware-probe.json"',
'RUN=Path("/run/2pny")\nNETWORK=RUN/"network-status.txt"\nHW=STATE/"hardware-probe.json"')
s=s.replace(
'def baud_flag(baud):',
'''def read_network_status():
    out={}
    try:
        for raw in NETWORK.read_text(errors="ignore").splitlines():
            if "=" in raw:
                k,v=raw.split("=",1);out[k.strip()]=v.strip()
    except Exception:pass
    return out

def baud_flag(baud):''')
s=s.replace(
'self.integration=integration;self.port=port;self.baud=baud;self.w=width;self.h=height;self.fd=None',
'self.integration=integration;self.port=port;self.baud=baud;self.w=width;self.h=height;self.fd=None;self.first_render=True')
s=s.replace(
'        w,h=self.w,self.h\n        if w<=330:',
'''        ns=read_network_status();uplink=(ns.get("uplink_type") or "rede").upper();ip=ns.get("default_ip") or "-"
        direction=str(a.get("direction") or "").upper();origin="RF" if direction=="RF" else "INTERNET" if direction=="NETWORK" else ""
        started=float(a.get("started_unix_ms") or 0)/1000.0;elapsed=max(0,int(time.time()-started)) if started else 0
        duration=f"{elapsed//60:02d}:{elapsed%60:02d}"
        if mode=="standby":
            source=f"{time.strftime('%H:%M')}  {proto}";target=f"{uplink} {ip}";op={"name":"PRONTO / READY"}
        elif origin:
            op=dict(op);op["name"]=f"{origin} {op.get('name') or ''}".strip()
        w,h=self.w,self.h
        if w<=330:''')
s=s.replace('cmds=["cls 0",f"fill 0,0,{w},34,{color}"','cmds=[f"fill 0,0,{w},34,{color}"')
s=s.replace('cmds=["cls 0",f"fill 0,0,{w},42,{color}"','cmds=[f"fill 0,0,{w},42,{color}"')
s=s.replace(
'f"{target}  BER {a.get(\'ber\',\'-\')}  RSSI {a.get(\'rssi_avg\',a.get(\'rssi\',\'-\'))}"',
'f"{target}"+(f"  BER {a.get(\'ber\')}%" if a.get("ber") is not None else "")+(f"  RSSI {a.get(\'rssi_avg\',a.get(\'rssi\'))}" if a.get("rssi_avg",a.get("rssi")) is not None else "")')
s=s.replace(
'f"BER {a.get(\'ber\',\'-\')}%   RSSI {a.get(\'rssi_avg\',a.get(\'rssi\',\'-\'))} dBm"',
'(f"BER {a.get(\'ber\')}%  " if a.get("ber") is not None else "")+(f"RSSI {a.get(\'rssi_avg\',a.get(\'rssi\'))} dBm" if a.get("rssi_avg",a.get("rssi")) is not None else "") or f"{origin} {duration}"')
s=s.replace(
'        self.send(cmds)',
'''        if self.first_render:
            cmds.insert(0,"cls 0");self.first_render=False
        self.send(cmds)''',1)
s=s.replace(
'''            sig=(live.get("sequence"),active.get("source"),active.get("target"),active.get("mode"),
                 tel.get("cpu_percent"),tel.get("temperature"),(live.get("internet") or {}).get("quality"))''',
'''            cadence=int(now) if active else int(now//60)
            sig=(live.get("sequence"),active.get("source"),active.get("target"),active.get("mode"),active.get("direction"),
                 active.get("ber"),active.get("rssi_avg",active.get("rssi")),(live.get("internet") or {}).get("quality"),cadence)''')
s=s.replace('time.sleep(.35 if active else 1.5)','time.sleep(.5 if active else 2.0)')
p.write_text(s)
os.chmod(p,0o755)

# Syntax/source gates before an image build can start.
subprocess.run(["bash","-n",str(root/"rootfs-overlay/usr/local/sbin/2pny-network-switch")],check=True)
subprocess.run(["bash","-n",str(root/"rootfs-overlay/usr/local/sbin/2pny-network-core")],check=True)
for rel in (
  "rootfs-overlay/usr/local/sbin/2pny-protocol-network-apply",
  "rootfs-overlay/usr/local/sbin/2pny-mqtt-preflight",
  "rootfs-overlay/usr/local/sbin/2pny-netdiag",
  "rootfs-overlay/usr/local/sbin/2pny-display-core",
):
    subprocess.run(["python3","-m","py_compile",str(root/rel)],check=True)
    cache=(root/rel).parent/"__pycache__"
    if cache.exists():shutil.rmtree(cache)

main=(root/"src/2pnyd/main.go").read_text()
dash=(root/"rootfs-overlay/usr/share/2pny/dashboard.html").read_text()
wiz=(root/"rootfs-overlay/usr/share/2pny/wizard.html").read_text()
apply=(root/"rootfs-overlay/usr/local/sbin/2pny-protocol-network-apply").read_text()
net=(root/"rootfs-overlay/usr/local/sbin/2pny-network-core").read_text()
disp=p.read_text()
assert '"0.3.4-alpha"' in main and "hostapd.pid" in main
assert "openActivity" in dash and 'id="rfAlert"' in dash and 'id="berMetric"' in dash
assert 'id="languageWelcome"' in wiz
assert "mqtt_preflight" in apply and "old_host_active" in apply
assert "wifi_profile_link_ok" in net and "default_ip=" in net and "uplink_type=" in net
assert "self.first_render" in disp and "read_network_status" in disp
print("PU2PNY-OS 0.3.4 corrective overlay applied")
