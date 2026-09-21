#!/usr/bin/env python3
"""Regression gates for the focused PU2PNY-OS 0.3.15 onboarding fix."""
from pathlib import Path
import difflib,re

ROOT=Path(__file__).resolve().parents[1]
old_rf=(ROOT/"src/2pny-rf-apply-0.3.14").read_text()
rf=(ROOT/"src/2pny-rf-apply-0.3.15").read_text()
old_proto=(ROOT/"src/2pny-protocol-network-apply-all-0.3.14.py").read_text()
proto=(ROOT/"src/2pny-protocol-network-apply-all-0.3.15.py").read_text()
dmr=(ROOT/"src/2pny-protocol-network-apply-0.3.13.py").read_text()
main=(ROOT/"src/2pnyd-main-0.3.15.go").read_text()
wiz=(ROOT/"src/wizard-0.3.14.html").read_text()

# The hardware-proven bootstrap remains intact.
for marker in (
    'SERIAL_LOCK=/run/2pny/mmdvm-serial.lock',
    'MODEM_BAUD="$(python3',
    '[Log]\nMQTTLevel=0\nDisplayLevel=0',
    'mmdvmhost_bootstrap_failed',
    'rf-bootstrap.json',
    'RF_APPLY_OK',
):
    assert marker in rf, marker

# MQTT is no longer a first-provisioning RF gate.
for forbidden in (
    '--ensure-service',
    'enable_operational_mqtt',
    'mqtt_preflight_failed_after_uart_ok',
    'mqtt_preflight_missing_after_uart_ok',
    'mmdvmhost_mqtt_phase_failed',
    '"phase":"operational_ok"',
):
    assert forbidden not in rf, forbidden

# The only RF semantic removal is the old phase-B block after uart_ok.
assert '# RF-018 phase B / PROTO-020:' in old_rf
assert '# PROTO-021 / WIZ-008:' in rf
assert old_rf[:old_rf.index('# RF-018 phase B / PROTO-020:')] == rf[:rf.index('# PROTO-021 / WIZ-008:')]

# DMR dispatcher: direct delegation, exactly as the 0.3.6/0.3.8 working path.
start=proto.index('if proto=="DMR":')
end=proto.index('server=q(server)',start)
branch=proto[start:end]
assert 'os.execv(DMR_HELPER' in branch
assert '2pny-mqtt-preflight' not in branch
assert '--ensure-service' not in branch
old_start=old_proto.index('if proto=="DMR":')
old_end=old_proto.index('server=q(server)',old_start)
old_branch=old_proto[old_start:old_end]
assert 'Pré-verificação MQTT falhou antes de aplicar DMR' in old_branch

# DMR helper still validates real radio services and does not depend on MQTT.
assert '[Log]\nDisplayLevel=1\nMQTTLevel=0' in dmr
assert 'DMRGateway did not remain active' in dmr
assert 'MMDVMHost did not remain active with DMRGateway' in dmr
assert '2pny-mqtt-preflight' not in dmr

# Existing backend/wizard commit path remains the authority for advancing.
assert 'os.WriteFile(provisionedFile' in main
assert 'committed = true' in main
assert 'writeRFApplyState("applied", done)' in main
assert "if(s.state==='applied')" in wiz
assert "await loadConclusion();step(4)" in wiz
assert "setTimeout(function(){location.href='/dashboard'},5000)" in wiz

# No accidental version mismatch.
assert 'appVersion            = "0.3.15-alpha"' in main

print("TEST_0315_REGRESSIONS_OK")
