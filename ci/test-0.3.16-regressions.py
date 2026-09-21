#!/usr/bin/env python3
"""Source-level regression gates for PU2PNY-OS 0.3.16-alpha."""
from pathlib import Path
import importlib.util

root=Path(__file__).resolve().parents[1]

def text(p): return (root/p).read_text()

main=text("src/2pnyd-main-0.3.16.go")
net=text("src/2pny-network-switch-0.3.16")
core=text("src/2pny-network-core-0.3.16")
internet=text("src/internet-0.3.16.html")
dash=text("src/dashboard-0.3.16.html")
hotspot=text("src/hotspot-0.3.16.html")
aprs=text("src/2pny-aprs-0.3.16.py")
aprsui=text("src/aprs-0.3.16.html")
display=text("src/2pny-display-apply-0.3.16.py")
displayui=text("src/display-0.3.16.html")
dstar=text("src/2pny-protocol-network-apply-all-0.3.16.py")
expert=text("src/expert-0.3.16.html")
direct=text("src/direct-core/direct_session.go")
patch=text("ci/patch-dmrgateway-voice-arbiter-0.3.16.py")

# NET-023/024
assert 'time.Since(connectivityCacheAt) < 2*time.Second' in main
assert 'r.URL.Query().Get("fresh") == "1"' in main
assert 'writeWiFiScanState("idle", "Nova busca solicitada."' in main
assert 'connection.autoconnect-retries 3' in net
assert 'SAVED_AUTO' in net and 'SAVED_SECRET' in net
assert 'nmcli networking on' in core and 'for _ in $(seq 1 20)' in core
assert "setInterval(function(){if(!document.hidden)load()},2000)" in internet
assert "fillWifiOptions(rows)" in internet

# LIVE-016 functional proof: a NETWORK event must never receive RF metrics.
spec=importlib.util.spec_from_file_location("live0316",root/"src/2pny-live-core-0.3.16.py")
live=importlib.util.module_from_spec(spec);spec.loader.exec_module(live)
s=live.LiveState()
s._start("DMR","NETWORK","123","TG 6",1000,slot=2)
assert s._metric("DMR",2,rssi=-70,ber=1.0) is None
assert s.active["NETWORK"]["rssi"] is None and s.active["NETWORK"]["ber"] is None
s._start("DMR","RF","123","TG 6",1001,slot=2)
assert s._metric("DMR",2,rssi=-70,ber=1.0)["direction"]=="RF"
assert s.active["RF"]["rssi"]==-70.0
assert "rfMetrics=origin==='RF'" in dash

# UI-030
assert "waitProtocolConnection" in hotspot
assert "Gateway local ativo, mas a conexão remota ainda não foi confirmada." in hotspot

# SEC-023 / UI-031
assert "PathExists=/run/2pny/timezone-request.json" in text("src/2pny-timezone-apply-0.3.16.path")
assert "PathExists=/run/2pny/ssh-request.json" in text("src/2pny-ssh-apply-0.3.16.path")
assert "REQ.unlink()" in text("src/2pny-timezone-apply-0.3.16.py")
assert "REQ.unlink()" in text("src/2pny-ssh-apply-0.3.16.py")
assert 'id="sshPubFile"' in expert
assert "chave privada" in expert.lower()

# APRS-012
assert 'server_candidates' in aprs and '"rotate.aprs2.net"' in aprs
assert 'socket.TCP_NODELAY' in aprs and 'parse_logresp' in aprs
assert 'waiting_ack' in aprs
assert 'Enviada · aguardando confirmação (ACK)' in aprsui
assert 'ensureAPRSDefaults' in main and '"server": "soam.aprs2.net"' in main
assert '"port": 14580' in main
assert 'Latitude        *float64' in main and 'Longitude       *float64' in main
assert 'obj["latitude"] = *in.Latitude' in main

# DISPLAY-018
assert 'if kind=="nextion_mmdvm":' in display
assert 'renderer="mmdvmhost-native"' in display
assert 'cp.set("General","Display","Nextion")' in display
assert 'cp.set("Nextion","Port","modem")' in display
assert 'host/display-in' in display  # inherited direct/modern path remains available
assert displayui.count('value="mmdvmhost-native"')>=1
assert 'value="pu2pny-modern-v2">PU2PNY Moderno V2</option>' not in displayui

# PROTO-023 exact pinned gateway schema.
assert 'Band=B' in dstar
assert 'ReloadTimer=72' in dstar and 'ReloadTime=72' not in dstar
assert 'custom/"DStar_Hosts.json"' in dstar
assert 'reflector_type="DCS"' in dstar
assert 'HBPort=20010' in dstar and 'Port=20011' in dstar

# P2P-006
assert 'c.register()' in direct
assert 'time.Sleep(120 * time.Millisecond)' in direct
assert 'case <-time.After(4 * time.Second):' in direct
assert 'client := &http.Client{Timeout: 15 * time.Second}' in main
assert 'identity remote' not in direct.lower() or 'identidade remota diferente do pareamento salvo' in direct

# PROTO-022 build patch keeps the scope explicit.
for marker in (
    'VOICE_PRIORITY','bool isActive() const','bool isActive(unsigned int slot) const',
    'suppressing XLX network audio','suppressing network audio on slot'
):
    assert marker in patch

# 0.3.15 proven bootstrap and DMR helper remain source baselines.
rf=text("src/2pny-rf-apply-0.3.15")
dmr=text("src/2pny-protocol-network-apply-0.3.13.py")
assert '[Log]\nMQTTLevel=0\nDisplayLevel=0' in rf
assert 'RF_APPLY_OK' in rf
assert 'Name=TGIF_Network' in dmr
assert 'tgif_auth_mode="legacy" if password=="passw0rd" else "secured"' in dmr

print("TEST_0316_REGRESSIONS_OK")
