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
proto=text("src/2pny-protocol-network-apply-all-0.3.19.py")
dmr=text("src/2pny-protocol-network-apply-0.3.19.py")
mode=text("src/2pny-mode-apply-0.3.19")
station=text("src/2pny-station-worker-0.3.17.py")
switch=text("src/2pny-network-switch-0.3.16")
prep18=text("ci/prepare-0.3.18-alpha.py")
prep19=text("ci/prepare-0.3.19-alpha.py")

# NET-025/026: DNS activation and dual Wi-Fi/channel UX.
compact="".join(main.split())
assert 'exec.Command("nmcli","device","reapply",iface)' not in compact
assert '"connection","up",conn,"ifname",iface' in compact
assert 'connection.autoconnect-retries 3' in switch
assert 'rede conectada' in internet
assert 'Nenhuma segunda rede encontrada' in internet
assert 'Canal em uso:' in internet and "tag=isActive?' atual':best===ch?' melhor':''" in internet
assert '<h3>Conexão via cabo</h3>' in internet
assert '<h3>Caminho da conexão</h3>' in internet

# UI-035: canonical browser-tab title.
for page in (internet,hotspot,dash,expert,system,display):
    assert '<title>PU2PNY-OS</title>' in page
assert "document.title='PU2PNY-OS'" in ui
assert 'ui_dir=root/"rootfs-overlay/usr/share/2pny"' in prep19
assert '<title>PU2PNY-OS</title>' in prep19

# UI-033/LIVE-018: protocol/frequency/save state and transient-only live fields/TOT.
assert '<h1>Protocolos</h1>' in hotspot and 'PU2PNY — Hotspot / Protocolos' not in hotspot
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
assert "setTimeout(function(){if(a&&a.parentNode)a.remove()},5000)" in ui
assert "a.href='/aprs?to='" in ui

# DISPLAY-019: bounded evidence-based detection, no silent HMI/TFT flashing.
assert 'Detecção automática ao entrar na Internet' in display
assert 'timeout -k 2 25 /usr/local/sbin/2pny-display-detector' in online
assert 'After=NetworkManager-wait-online.service network-online.target' in svc
assert 'range(0,101,10)' in core and 'PU2PNY-OS' in core
assert 'tot_left=max(0,180-elapsed) if direction=="RF" and mode=="tx" else None' in core
for bad in ('NextionUpdater','.tft','flash'):
    assert bad not in online

# SEC-026/027 and UI-034.
assert 'drain pending requests' in tz and 'for _ in range(32)' in tz
assert '["timedatectl","set-timezone",tz]' in tz
assert 'ensureVoiceDefaults' in main and '"enabled":true' in compact
assert 'voice-hourly.enabled' in main
assert 'expertLiveSection' in expert
assert 'generateSSHKey' in expert and 'ecdsa-sha2-nistp256' in expert
assert 'pu2pny-erros.txt' in expert and 'Leitura sob demanda' in expert

# REL-014 / PROTO-027: YSF local bridge remains the previously established
# 3200/4200 contract, but Startup is now deterministically resolvable.
for marker in ('LocalPort":"3200"','GatewayPort":"4200"','WiresXCommandPassthrough=0','Port=42000'):
    assert marker in proto,marker
assert 'CYSFReflectors::findByName' in proto
assert 'selected is None' in proto and 'startup=full_name(selected)' in proto
assert 'startup_name' in proto
assert 'Linked to' in station and 'Link has failed, polls lost' in station

# RF-019/LIVE-019: duplex is coherent across activation paths and visible.
assert 'setsec(cp,"General",{"Duplex":"1" if usemode=="repeater" else "0"})' in proto
assert 'out.append("Duplex="+duplex)' in mode
assert "if(c.use_mode==='repeater')return 'RX '+a+' MHz · TX '+bb+' MHz'" in dash
assert 'toFixed(6)' in dash

# PROTO-028: DMR duplex keeps both local timeslots available, while XLX keeps
# one remote network slot selected by the operator.
assert 'MQTTLevel=0' in dmr
assert 'duplex=1 if usemode=="repeater" else 0' in dmr
assert 'slot1=True if duplex' in dmr and 'slot2=True if duplex' in dmr
assert '"Slot1":"1" if slot1 else "0"' in dmr and '"Slot2":"1" if slot2 else "0"' in dmr
assert 'route_slots=(1,2) if duplex' in dmr
assert 'Slot={remote_slot}' in dmr
assert 'DMR duplex candidate did not enable TS1/TS2 local transport' in dmr
# Preserve TGIF 0.3.13 routing/auth baseline while extending it to both local
# slots in duplex mode.
for marker in ('Name=TGIF_Network','TGRewrite{idx}={s},1,2,1,9999998',
               'SrcRewrite{idx}=2,1,{s},1,9999998',
               'tgif_auth_mode="legacy" if password=="passw0rd" else "secured"',
               'Password="{password}"','"auth_mode":tgif_auth_mode'):
    assert marker in dmr,marker
# Preserve critical DMR baseline ports/auth/audio behavior.
for marker in ('GatewayPort":"62031"','LocalPort":"62032"','RptPort=62032','LocalPort=62031',
               'TG4000=unlink','voice_dir="/usr/share/2pny/audio/dmrgateway"'):
    assert marker in dmr,marker
# REL-012 build reproducibility: radio-admin patch must run before DStarGateway compile.
assert 'make -j"$JOBS" DStarGateway/dstargateway' in prep18
assert 'exact DStarGateway target make anchor missing' in prep18
assert 'DSTAR_RF_ADMIN_SRC=' in prep18
# REL-011/PROTO-024: voice assets must be staged from the exact pinned
# DStarGateway checkout before /tmp/DStarGateway-029 is removed.
for marker in ('PU2PNY_DSTAR_VOICE_ASSETS_0318',
               "find Data -maxdepth 1 -type f",
               "test -s /usr/local/share/dstargateway.d/en_GB.ambe",
               "test -s /usr/local/share/dstargateway.d/en_GB.indx"):
    assert marker in prep18,marker
print("TEST_0319_REGRESSIONS_OK")
