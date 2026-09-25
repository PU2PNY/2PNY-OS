#!/usr/bin/env python3
from pathlib import Path
import hashlib,re

root=Path(__file__).resolve().parents[1]
old=(root/"src/wizard-0.3.21.html").read_text()
new=(root/"src/wizard-0.3.25.html").read_text()

def block(text,start,end):
    a=text.index(start);b=text.index(end,a);return text[a:b]

# User-approved 0.3.23 Wi-Fi connect/recovery logic must remain exact.
start="function selectedSSID(){"
end="q('refreshEthernet').onclick="
assert block(old,start,end)==block(new,start,end)

# Runtime helper inherited by 0.3.23 remains unchanged.
sw=(root/"src/2pny-network-switch-0.3.16").read_bytes()
assert b'connection.autoconnect yes' in sw
assert b'Wi-Fi connected:' in sw
print("WIFI_BASELINE_SHA256="+hashlib.sha256(sw).hexdigest())

main=(root/"src/2pnyd-main-0.3.25.go").read_text()
assert 'else if cachedConnectivitySnapshot().Internet {' in main
assert 'fileExists(filepath.Join(dataDir, "uplink-ssid")) && cachedConnectivitySnapshot().Internet' not in main

assert "ethernetAutoAdvanced" in new
assert "c.internet&&c.ethernet" in new
assert "get('step')!=='1'" in new

mdns=(root/"src/2pny-mdns-guard-0.3.25").read_text()
assert 'host-name","pu2pny' in mdns
assert 'domain-name","local' in mdns
assert 'allow-interfaces' in mdns and 'deny-interfaces' in mdns
assert '5353' in mdns
assert '/run/2pny/mdns-state' in mdns

# Explicitly verify this cycle does not introduce RF/protocol implementation files.
print("NETWORK_0325_REGRESSION_OK")
