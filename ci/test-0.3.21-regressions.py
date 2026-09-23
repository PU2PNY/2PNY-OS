#!/usr/bin/env python3
"""Focused source/regression gates for PU2PNY-OS 0.3.21-alpha."""
from pathlib import Path
import ast,re
ROOT=Path(__file__).resolve().parents[1]
def text(p): return (ROOT/p).read_text()
def pyok(p): ast.parse(text(p),filename=p)

main=text("src/2pnyd-main-0.3.21.go")
dmr=text("src/2pny-protocol-network-apply-0.3.21.py")
station=text("src/2pny-station-worker-0.3.21.py")
voice=text("ci/patch-dmrgateway-voice-arbiter-0.3.21.py")
dash=text("src/dashboard-0.3.21.html")
hot=text("src/hotspot-0.3.21.html")
internet=text("src/internet-0.3.21.html")
wizard=text("src/wizard-0.3.21.html")
system=text("src/system-0.3.21.html")
display=text("src/display-0.3.21.html")
dapply=text("src/2pny-display-apply-0.3.21.py")
dcore=text("src/2pny-display-core-0.3.21.py")
wifi=text("src/2pny-wifi-profiles-0.3.21")
dispatch=text("src/90-pu2pny-wifi-choice-0.3.21")
aprs=text("src/2pny-aprs-0.3.21.py")
aprsui=text("src/aprs-0.3.21.html")
journal=text("src/20-pu2pny-journald-0.3.21.conf")
rxoff=text("src/2pny-rxoffset-apply-0.3.21.py")
direct_session=text("src/direct-core-0.3.21/direct_session.go")
direct_transport=text("src/direct-core-0.3.21/direct_transport.go")
direct_auto=text("src/direct-core-0.3.21/direct_autocall.go")
direct_ui=text("src/direct-0.3.21.html")

for p in (
 "src/2pny-protocol-network-apply-0.3.21.py","src/2pny-station-worker-0.3.21.py",
 "src/2pny-display-apply-0.3.21.py","src/2pny-display-core-0.3.21.py",
 "src/2pny-dmr-duplex-diagnostics-0.3.21.py","src/2pny-aprs-0.3.21.py",
 "src/2pny-rxoffset-apply-0.3.21.py","ci/patch-dmrgateway-voice-arbiter-0.3.21.py",
 "ci/prepare-0.3.21-alpha.py",
): pyok(p)

# REL-018: protected physical baselines remain explicit.
assert "PROTO-036" in dmr and "simplex-protected" in dmr
assert 'duplex=1 if usemode=="repeater" else 0' in dmr
assert 'slot1=True if duplex' in dmr and 'slot2=True if duplex' in dmr
assert 'if duplex:' in dmr and '"Type":"Gateway"' in dmr
assert 'route_slots=(1,2) if duplex' in dmr
assert 'DMRDelay' not in dmr  # do not misuse TX timing as a duplex audio fix

# PROTO-034: system voice blocks network audio only while actually SENDING.
assert "XLXVOICE_STATUS::SENDING" in voice and "DYNVOICE_STATUS::SENDING" in voice
assert "m_status != XLXVOICE_STATUS::NONE" not in voice

# LIVE-022 / PROTO-035: requested vs confirmed TG, UI displays TG not stale module.
assert "requested_tg" in station and "connected_tg" in station
assert "requested_tg" in dash and "connected_tg" in dash and "TG '+dmrTG" in dash
assert "TG conectado" in hot and "TG4001" in hot and "TG4099" in hot
assert 'id="rxFrequencyMetric"' in dash and 'id="txFrequencyMetric"' in dash
assert '<th>Módulo / TG</th>' in dash

# UI-039: profile operation remains open until real gateway/network evidence.
assert "observeProtocolConnection(proto,op)" in hot
assert "Aguardando confirmação real do gateway/rede" in hot
assert "op.done('Perfil aplicado localmente.'" not in hot

# NET-028/029: truthful DNS convergence and automatic backup Wi-Fi with hysteresis.
assert 'r.pending' in internet and 'Internet reconectada' in internet
assert "Salvar rede de backup" in internet and "wifiSavePrimary" in internet
assert 'action:\'auto-select\'' in internet
assert "12-point hysteresis" in wifi and "current_sig+12" in wifi.replace(" ","")
assert "connectivity-change" in dispatch or "up)" in dispatch

# UI-040 / WIZ-010: language persists server-side and normal post-Wi-Fi resume starts at Hardware.
assert '"selected":fileExists(path)' in main
assert "/api/language" in wizard and "languageInfo&&languageInfo.selected" in wizard
assert "lastConnectivity&&lastConnectivity.internet" in wizard and "step(2);startHardware()" in wizard
assert "<title>PU2PNY-OS</title>" in wizard

# DISPLAY-022/023: writer can be truthfully active without faking physical confirmation.
assert "tx_only_unconfirmed" in dapply or "candidate_native_fallback" in dapply
assert '"physical_confirmed":bool(d.get("physical_confirmed"))' in dapply
assert 'tx_only_unconfirmed=d.get("physical_confirmed") is not True' in dapply
assert '"physical_confirmed":True' not in dapply
assert "Saída ativa · retorno COMOK ainda não confirmado" in display
for marker in ("BOOT","Rastreando","BER","RSSI"):
    assert marker.lower() in dcore.lower()
assert "display_hm" in dcore

# P2P-009: server may rendezvous, but media relay is rejected; radio starts calls.
assert "relay desativado" in direct_session
assert "caminho P2P direto indisponível" in direct_session
assert 'case "relay-data"' in direct_transport and "deliberately rejected" in direct_transport
assert 'Direction' in direct_auto and '"RF"' in direct_auto and 'proto=="DSTAR"' in direct_auto.replace(" ","")
assert "DMR" in direct_auto and "Private" in direct_ui
assert "Chamada pelo rádio" in direct_ui or "rádio" in direct_ui.lower()

# APRS-015: exact source+ID ACK matching, manual location and M/H-SMS documentation.
assert 'item.get("station")==source' in aprs and 'str(item.get("id"))==str(mid)' in aprs
assert "ACKDIAG" in aprs and "ack_diagnostics" in aprs
assert "latitude" in aprsui and "longitude" in aprsui
assert "M-SMS" in aprsui and "H-SMS" in aprsui
assert "experimental" in aprsui.lower()

# PERF-005: persistent journal is bounded.
for marker in ("SystemMaxUse=64M","SystemMaxFileSize=8M","MaxRetentionSec=7day","Compress=yes"):
    assert marker in journal

# RF-022: BER advisor changes only RXOffset, requires Standby and preserves rollback.
assert "RXOffset" in rxoff and "TXOffset" not in rxoff
assert 'if live.get("active")' in rxoff
assert "backup" in rxoff.lower() and "restaurado" in rxoff.lower()
assert "/api/rf/ber-calibration" in main
for marker in ("Aplicar e medir","Salvar melhor ajuste","Restaurar ajuste salvo","100 Hz"):
    assert marker in hot

# SYS-004: automatic network/NTP clock; DST is display-only.
assert 'case "auto-time":' in main
assert "dst_manual" in main and "browser-iana" in main
assert "Horário de verão manual" in system and "UTC, logs e protocolos" in system
assert "display-only" in dcore or "presentation-only" in dcore

print("TEST_0321_REGRESSIONS_OK")
