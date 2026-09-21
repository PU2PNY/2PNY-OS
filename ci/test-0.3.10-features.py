#!/usr/bin/env python3
from pathlib import Path
import json,re

ROOT=Path(__file__).resolve().parents[1]
read=lambda p:(ROOT/p).read_text()

main=read("src/2pnyd-main-0.3.10.go")
proto=read("src/2pny-protocol-network-apply-all-0.3.10.py")
mqtt=read("src/2pny-mqtt-preflight-0.3.10.py")
oper=read("src/2pny-operational-apply-0.3.10.py")
apply=read("src/2pny-display-apply-0.3.10.py")
core=read("src/2pny-display-core-0.3.10.py")
det=read("src/2pny-display-detector-0.3.9.py")
ui=read("src/ui-common-0.3.10.js")
wizard=read("src/wizard-0.3.10.html")
hotspot=read("src/hotspot-0.3.10.html")
display=read("src/display-0.3.10.html")
expert=read("src/expert-0.3.10.html")
catalog=json.loads(read("src/display-catalog-0.3.9.json"))
udev=read("src/99-pu2pny-display-hotplug-0.3.9.rules")

assert 'appVersion            = "0.3.10-alpha"' in main
assert '/api/display/detection' in main and '/api/diagnostics' in main
for state in ('"associating"','"associated"','"ipv4"','"route"','"dns"','"connected"'):assert state in main
assert 'local=cols[3]' in proto and 'local=cols[4]' not in proto
assert 'wait_bridge' in proto and 'waiting_bridge' in proto
assert 'protocol-health.json' in proto and 'last-protocol-rollback.json' in proto
assert 'verify_host_bridge_config(proto)' in proto
assert 'mqtt-preflight.json' in mqtt
assert 'MQTT local indisponível' in mqtt
assert 'mqtt_ready' in oper and 'wait_bridge' in oper and 'last-boot-restore.json' in oper
assert 'pu2pny-modern-v2' in apply and 'mmdvmhost-native' in apply
assert 'patch_modern_transport' in apply and 'patch_native_nextion' in apply
assert 'host/display-in' in core and '"1060"' in core
assert 'get pnyver.txt' in det and 'comok' in det.lower()
assert 'auto_download' in json.dumps(catalog) and catalog['policy']['flash_requires_explicit_confirmation']
assert all((not p.get('tft')) or p['tft'].get('status')=='unpublished' or (p['tft'].get('url') and p['tft'].get('sha256')) for p in catalog['profiles'])
assert 'syncClock' in ui and "/api/system" in ui and "60000" in ui
assert 'wizardOperation' in wizard and "op.step(s.message" in wizard
assert '<iframe' not in hotspot.lower() and 'Perfis rápidos nativos · sem iframe' in hotspot
assert 'rendererSelect' in display and 'modelSelect' in display and 'nextion-101-1024x600' in display
assert 'Nunca automático' in display and '/api/display/detection' in display
assert 'Diagnóstico operacional' in expert and '/api/diagnostics' in expert
assert 'ACTION=="add|change"' not in udev and 'ACTION=="add"' in udev and 'ACTION=="change"' in udev
print("TEST_0310_FEATURES_OK")
