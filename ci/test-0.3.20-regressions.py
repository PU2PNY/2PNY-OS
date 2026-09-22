#!/usr/bin/env python3
"""Focused source/regression gates for PU2PNY-OS 0.3.20-alpha."""
from pathlib import Path
import ast,re
ROOT=Path(__file__).resolve().parents[1]
def text(p):return (ROOT/p).read_text()
def pyok(p):ast.parse(text(p),filename=p)

main=text("src/2pnyd-main-0.3.20.go")
ui=text("src/ui-common-0.3.20.js")
internet=text("src/internet-0.3.20.html")
hotspot=text("src/hotspot-0.3.20.html")
dash=text("src/dashboard-0.3.20.html")
system=text("src/system-0.3.20.html")
display=text("src/display-0.3.20.html")
detector=text("src/2pny-display-detector-0.3.20.py")
dapply=text("src/2pny-display-apply-0.3.20.py")
dcore=text("src/2pny-display-core-0.3.20.py")
proto=text("src/2pny-protocol-network-apply-all-0.3.20.py")
proto19=text("src/2pny-protocol-network-apply-all-0.3.19.py")
dmr=text("src/2pny-protocol-network-apply-0.3.20.py")
profiles=text("src/2pny-protocol-profiles-0.3.20.py")
station=text("src/2pny-station-worker-0.3.20.py")
hostfiles=text("src/2pny-hostfiles-update-0.3.20")
aprs=text("src/2pny-aprs-0.3.20.py")
aprsui=text("src/aprs-0.3.20.html")
updater=text("src/2pny-update-manager-0.3.20.py")
direct=text("src/direct-core/direct_autocall.go")
dpatch=text("ci/patch-dmrgateway-pu2pny-0.3.20.py")

for p in (
 "src/2pny-display-detector-0.3.20.py","src/2pny-display-apply-0.3.20.py",
 "src/2pny-display-core-0.3.20.py","src/2pny-protocol-network-apply-all-0.3.20.py",
 "src/2pny-protocol-network-apply-0.3.20.py","src/2pny-protocol-profiles-0.3.20.py",
 "src/2pny-station-worker-0.3.20.py","src/2pny-aprs-0.3.20.py",
 "src/2pny-update-manager-0.3.20.py","ci/prepare-0.3.20-alpha.py",
 "ci/patch-dmrgateway-pu2pny-0.3.20.py",
):pyok(p)

# REL-016 / UI-037: no empty facts/cards and no false timeout rollback claim.
assert "pny-real-hidden" in ui and "sweepRealOnly" in ui
assert "A confirmação demorou além do limite do navegador" in ui
assert "body:JSON.stringify({provider:p})},45000)" in internet

# LIVE-020/021: 2:30 yellow, 2:50 red, RF-only S-meter; native 180s cutoff untouched.
assert "sec>=150" in dash and "danger=sec>=170" in dash
assert "tot-warn" in dash and "tot-danger" in dash
assert "0</span><span>1</span><span>5</span><span>9</span><span>9+30" in dash
assert "rfMetrics=origin==='RF'" in dash and "hasSMeter" in dash
assert 'Timeout=180' in text("src/2pny-rf-apply-0.3.15")

# PROTO-029/030 and PERF-004.
assert "families:[['XLX','XLX'],['BrandMeister','BrandMeister']" in hotspot
assert "if kind.lower()==\"xlx\": essid=\"\"" in dmr
assert "observeProtocolConnection" in hotspot and "Perfil aplicado localmente" in hotspot
assert "waitProtocolConnection" not in hotspot

# RF-020: DMR duplex candidate keeps both local slots while simplex semantics remain.
assert 'duplex=1 if usemode=="repeater" else 0' in dmr
assert 'slot1=True if duplex' in dmr and 'slot2=True if duplex' in dmr
assert 'route_slots=(1,2) if duplex' in dmr
assert dmr.rindex('restart",HOST_SERVICE') < dmr.rindex('restart",GW_SERVICE')
for marker in ('MQTTLevel=0','Jitter":"360"','TG4000=unlink','TG4099=status voice'):
    assert marker in dmr

# PROTO-027 baseline: YSF implementation block must remain byte-identical to 0.3.19.
def block(s,a,b):
    i=s.index(a);j=s.index(b,i);return s[i:j]
assert block(proto,'    elif proto=="YSF":','    elif proto=="P25":') == block(proto19,'    elif proto=="YSF":','    elif proto=="P25":')

# RF-021/022 + radio command truth.
assert 'DSTAR_LOCAL=' in proto and '"Module":dstar_local' in proto and 'Band={dstar_local}' in proto
assert 'dstarLocalModule' in hotspot and 'B (padrão PU2PNY)' in hotspot
assert 'XLXHosts.txt' in proto and '"reflector_type":"DCS"' in proto
assert 'requested_server' in station and 'last_command_error' in station
assert 'runtime["server_name"]=target' not in station
assert 'is unknown, ignoring link request' in station

# PROTO-033: XLX radio TG control accepted on either RF timeslot.
assert '(slotNo == 1U || slotNo == 2U)' in dpatch
assert 'requested_module' in station

# UI-038 network truth.
assert "netOnline=conn.internet===true" in hotspot
assert "Internet disponível / link remoto pendente" in hotspot

# P2P-008: RF-driven Direct only from real RF, D-Star callsign or DMR private ID.
assert 'live.Active.Direction' in direct and '"RF"' in direct
assert 'proto=="DSTAR"' in direct and 'proto=="DMR"' in direct
assert 'strings.HasPrefix(target,"TG ")' in direct
assert 'c.call(target)' in direct

# APRS-014: page name and XLX026-style command set with real local data.
assert "<h1>APRS</h1>" in aprsui and "APRS / D-PRS" not in aprsui
for cmd in ("PING","STATUS","LAST","MYLAST","ONLINE","MODULE","INFO","HELP"):
    assert f'command=="{cmd}"' in aprs or cmd in aprs
assert 'login_unverified' in aprs and 'retry_unacked' in aprs

# DISPLAY-020/021: real COMOK via MMDVM MQTT bridge and V2 is authoritative.
assert 'host/display-in' in detector and 'host/display-out' in detector
assert 'parse_connect(out or b"")' in detector and '"physical_confirmed":True' in detector
assert 'renderer="pu2pny-modern-v2"' in dapply and 'DISPLAY_NOT_CONFIRMED' in dapply
assert 'range(0,101,10)' in dcore and 'PU2PNY-OS' in dcore
assert "Ativo · tela confirmada" in display

# SYS-001/002/003.
assert 'case "set-time":' in main and 'runClockRequest' in main
assert '/api/system/timezones' in main and 'timedatectl","list-timezones' in main
assert '/api/diagnostics/errors/download' in main and 'Content-Disposition' in main
assert 'Baixar logs de erro' in system and 'datetime-local' in system

# UPDATE-007.
assert 'restore_backup_file' in updater and 'state="rolled_back"' in updater
assert 'Instalar agora' in system and 'Instalar depois' in system

# NET-027 host catalog merger exists both update-time and apply-time.
assert 'DStar_Hosts.json' in hostfiles and 'XLXHosts.txt' in hostfiles
assert 'name="XLX"+ident' in hostfiles

print("TEST_0320_REGRESSIONS_OK")
