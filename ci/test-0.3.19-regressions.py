#!/usr/bin/env python3
"""Focused source/regression gates for PU2PNY-OS 0.3.19-alpha."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def text(p): return (ROOT/p).read_text()

main=text("src/2pnyd-main-0.3.19.go")
internet=text("src/internet-0.3.19.html")
hotspot=text("src/hotspot-0.3.19.html")
dash=text("src/dashboard-0.3.19.html")
expert=text("src/expert-0.3.19.html")
system=text("src/system-0.3.19.html")
display=text("src/display-0.3.19.html")
core=text("src/2pny-display-core-0.3.19.py")
online=text("src/2pny-display-online-detect-0.3.19")
svc=text("src/2pny-display-online-detect-0.3.19.service")
tz=text("src/2pny-timezone-apply-0.3.19.py")
ui=text("src/ui-common-0.3.19.js")
proto=text("src/2pny-protocol-network-apply-all-0.3.18.py")
station=text("src/2pny-station-worker-0.3.17.py")
switch=text("src/2pny-network-switch-0.3.16")

# NET-025/026: DNS activation and dual Wi-Fi/channel UX.
assert 'exec.Command("nmcli","device","reapply",iface)' not in main
assert '"connection","up",conn,"ifname",iface' in main
assert 'connection.autoconnect-retries 3' in switch
assert 'rede conectada' in internet
assert 'Nenhuma segunda rede encontrada' in internet
assert 'Canal em uso:' in internet and "tag=isActive?' atual':best===ch?' melhor':''" in internet
assert '<h3>Conexão via cabo</h3>' in internet
assert '<h3>Caminho da conexão</h3>' in internet

# UI-033/LIVE-018: protocol/frequency/save state and transient-only live fields/TOT.
assert 'PU2PNY — Protocolos' in hotspot and 'PU2PNY — Hotspot / Protocolos' not in hotspot
assert 'toFixed(6)' in hotspot and "replace(',','.')" in hotspot
assert "PNY.operation('Salvando perfil'" in hotspot and 'Atualizando perfil...' in hotspot
assert 'slotFact' in dash and 'ccFact' in dash
assert "classList.add('hidden')" in dash and 'TOT restante' in dash
assert "nr.link_state==='linked'" in dash
assert "setInterval(function(){show(last)},250)" in system

# PROTO-025: keep D-Star local RF module C while remote module is runtime proof.
for marker in ('"Module":"C" if proto=="DSTAR"','Band=C','ReflectorReconnect=Never',
               'LocalPort":"20011"','GatewayPort":"20010"','HBPort=20010','Port=20011'):
    assert marker in proto,marker
assert 'Link command from' in station and '"link_state":"linked"' in station
for marker in ('_______I','_______E','_______U','_______L','XLX026DL','REF030CL',
               'RPT1','RPT2','DUP+/DUP−','TG 4000','YSF/C4FM','P25','NXDN','POCSAG/DAPNET'):
    assert marker in hotspot,marker
assert '/api/diagnostics/errors' in main
assert 'wrong repeater' in main and 'non repeater rf header' in main

# APRS-013: native notifications remain browser-governed; in-panel bubble only off APRS.
assert "location.pathname==='/aprs'" in ui
assert "setTimeout(function(){t.remove()},5000)" in ui
assert "location.href='/aprs?to='" in ui

# DISPLAY-019: bounded evidence-based detection, no silent HMI/TFT flashing.
assert 'Detecção automática ao entrar na Internet' in display
assert 'timeout -k 2 25 /usr/local/sbin/2pny-display-detector' in online
assert 'After=NetworkManager-wait-online.service network-online.target' in svc
assert 'range(0,101,10)' in core and 'PU2PNY-OS' in core
assert 'tot_left=max(0,180-elapsed) if direction=="RF" and mode=="tx" else None' in core
for bad in ('NextionUpdater','\.tft','flash'):
    assert bad not in online

# SEC-026/027 and UI-034.
assert 'drain pending requests' in tz and 'for _ in range(32)' in tz
assert '["timedatectl","set-timezone",tz]' in tz
assert 'ensureVoiceDefaults' in main and '"enabled":true' in main
assert 'voice-hourly.enabled' in main
assert 'expertLiveSection' in expert
assert 'generateSSHKey' in expert and 'ecdsa-sha2-nistp256' in expert
assert 'pu2pny-erros.txt' in expert and 'Leitura sob demanda' in expert

# DMR/RF baseline must remain untouched by 0.3.19.
p18=text("src/2pny-protocol-network-apply-all-0.3.18.py")
assert proto==p18
assert 'MQTTLevel=0' in proto
print("TEST_0319_REGRESSIONS_OK")
