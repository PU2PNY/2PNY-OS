#!/usr/bin/env python3
import json,re,subprocess,time
from pathlib import Path
OUT=Path("/run/2pny/dmr-duplex-diagnostics.json")
def journal(unit):
    p=subprocess.run(["journalctl","-u",unit,"-n","180","--no-pager","-o","cat"],text=True,capture_output=True)
    return p.stdout or ""
host=journal("2pny-mmdvmhost.service");gw=journal("2pny-dmrgateway.service")
def hits(text,pattern): return len(re.findall(pattern,text,re.I))
data={
 "generated":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),
 "downlink_activate":hits(host,r"Downlink Activate received"),
 "invalid_downlink_activate":hits(host,r"Invalid Downlink Activate"),
 "rf_dmr_events":hits(host,r"DMR, received RF|DMR Slot [12], received RF"),
 "network_dmr_events":hits(host,r"DMR, received network|DMR Slot [12], received network"),
 "gateway_connected":hits(gw,r"MMDVM has connected|Opening DMR Network"),
 "gateway_overflow":hits(gw,r"buffer overflow"),
 "note":"Contadores são observação de log, não prova de RF/áudio físico."
}
OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n")
print(json.dumps(data,ensure_ascii=False))
