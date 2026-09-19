#!/usr/bin/env python3
"""PU2PNY-OS 0.3.1 regression contract.

0.3.1 must be a strict functional superset of the 0.2.9 modular baseline.
This test intentionally checks capabilities instead of visual equivalence.
"""
from pathlib import Path
R=Path(__file__).resolve().parents[1]

def text(p): return (R/p).read_text(errors="ignore")
def has(p,*needles):
    s=text(p)
    missing=[x for x in needles if x not in s]
    assert not missing, f"{p}: missing {missing}"

# 0.2.9 live/operator baseline.
has("src/2pny-live-core-0.2.9.py","DSTAR_START_RE","YSF_RF_START_RE","P25_START_RE","NXDN_START_RE","clear_stale")
has("src/2pny-station-worker-0.3.0.py","operators.sqlite","radioid.net/api/dmr/user/","qrz_photo","country_code","history-summary.json")
has("ci/patch-dmrgateway-pu2pny-0.2.9.py","TG4000","TG4099","XLX module control")
has("ci/patch-dmrgateway-hourly-0.2.9.py","hourly")

# Physical display baseline + 0.3.1 Nextion correction.
has("src/2pny-display-core-0.2.9.py","nextion_mmdvm","SSD1306","class LCD","CPU","RX ")
has("src/2pny-hardware-probe-0.3.1.py",'b"connect\\xff\\xff\\xff"',"nextion_mmdvm")
has("src/2pny-display-apply-0.3.1.py","PU2PNY Display Core is authoritative",'disable","--now",LEGACY',"nextion_mmdvm")
has("src/2pny-nextion-autodetect-0.3.1.py",'input=b"connect\\xff\\xff\\xff"',"NEXTION_AUTO_OK")

# 0.2.9 Wi-Fi safety retained, but 0.3.1 no longer depends on a post-AP scan.
has("src/2pny-network-switch-0.3.1","restore_on_error","create_candidate","try_profile","connection.autoconnect-retries 0","wpa-psk","sae")
has("src/2pny-mdns-guard-0.3.1","host-name","pu2pny","_http._tcp","publish-addresses")

# Complete protocol stack remains present.
for p in ("2pny-dstargateway-0.2.9.service","2pny-ysfgateway-0.2.9.service","2pny-p25gateway-0.2.9.service",
          "2pny-nxdngateway-0.2.9.service","2pny-dapnetgateway-0.2.9.service"):
    assert (R/"src"/p).is_file(), p
has("src/2pny-protocol-network-apply-all-0.3.0.py","DSTAR","YSF","P25","NXDN","POCSAG","configuration rolled back")
has("src/2pny-server-catalog-0.3.0.py","DPlus_Hosts.txt","DExtra_Hosts.txt","DCS_Hosts.txt","YSFHosts.txt","P25Hosts.txt","NXDNHosts.txt")
has("src/protocols-0.3.1.html","REF / DPlus","XRF / DExtra","DCS","XLX","Servidor / refletor","Avançado — endereço, porta e credenciais")
assert 'id="search"' not in text("src/protocols-0.3.1.html")
assert "Buscar servidor" not in text("src/protocols-0.3.1.html")

# APRS remains APRS-only, with messaging/status modules.
has("src/2pny-aprs-0.3.0.py","APRS","message","ack")
has("src/2pny-aprs-0.3.0.py","APRS-IS")

# Dedicated 0.3 pages are additive, not replacements for capability.
for p in ("dashboard-0.3.0.html","internet-0.3.0.html","history-0.3.0.html","aprs-0.3.0.html","system-0.3.0.html","expert-0.3.0.html"):
    assert (R/"src"/p).is_file(), p
has("src/ui-common-0.3.0.js","Ao Vivo","Internet","Protocolos","Mais usado","APRS","Sistema","Expert")

# Full local flag pack is still built from the pinned 0.2.9 path.
has("ci/prepare-0.2.9-alpha.py","flag-icons","flags/4x3","LICENSE-MIT")

print("PU2PNY-OS 0.3.1: 0.2.9 feature-parity source contract OK")
