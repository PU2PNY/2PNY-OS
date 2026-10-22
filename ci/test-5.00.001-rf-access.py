#!/usr/bin/env python3
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch

SRC = Path(__file__).resolve().parents[1] / "runtime/5x/2pny-rf-access.py"
spec = importlib.util.spec_from_file_location("access", SRC)
access = importlib.util.module_from_spec(spec)
spec.loader.exec_module(access)

BASE = """[General]
Callsign=PU2PNY
Id=7241234
Display=None
[Modem]
Port=/dev/serial0
RXFrequency=439000000
TXFrequency=439000000
[DMR]
Enable=1
ColorCode=1
SelfOnly=0
[DMR Network]
Password=NOT-A-REAL-SECRET-TEST
[System Fusion]
Enable=0
SelfOnly=0
[D-Star]
Enable=1
SelfOnly=0
[Nextion]
Port=modem
"""

def expect_error(src, request, contains):
    try:
        access.render_policy(src, request)
    except access.AccessError as err:
        assert contains in str(err), (contains, err)
    else:
        raise AssertionError("should reject:" + contains)

expect_error(BASE, {"mode": "semi_public", "allowed": []}, "empty_acl_fail_closed")
expect_error(BASE, {"mode": "semi_public", "allowed": [{"callsign": "PY2ABC"}]}, "requires_ids")
expect_error(BASE, {"mode": "public"}, "requires_explicit_confirmation")
expect_error(BASE.replace("Enable=0\nSelfOnly=0", "Enable=1\nSelfOnly=0"),
             {"mode": "semi_public", "allowed": [{"callsign": "PY2ABC", "dmr_id": "7247777"}]},
             "semi_public_not_supported_for_active")
expect_error(BASE, {"mode": "semi_public", "allowed": [{"callsign": "INVALID CALL", "dmr_id": "7247777"}]}, "invalid_callsign")

semi, state = access.render_policy(BASE, {
    "mode": "semi_public",
    "allowed": [{"callsign": "PY2ABC", "dmr_id": "7247777"}],
})
assert state["mode"] == "semi_public"
assert "WhiteList=7241234,7247777" in semi
assert "WhiteList=PU2PNY,PY2ABC" in semi
assert "[Nextion]\nPort=modem" in semi
assert "[DMR Network]\nPassword=NOT-A-REAL-SECRET-TEST" in semi
assert "RXFrequency=439000000" in semi
assert "ColorCode=1" in semi
assert access.sections(semi)["DMR"]["selfonly"] == "0"
assert access.sections(semi)["D-Star"]["selfonly"] == "0"
private, state = access.render_policy(BASE, {"mode": "private"})
assert state["mode"] == "private"
assert access.sections(private)["DMR"]["selfonly"] == "1"
assert access.sections(private)["D-Star"]["selfonly"] == "1"
public, state = access.render_policy(BASE, {"mode": "public", "confirmation": "ABRIR RF PUBLICO"})
assert access.sections(public)["DMR"]["selfonly"] == "0"
assert access.sections(public)["D-Star"]["selfonly"] == "0"
assert access.sections(public)["DMR"].get("whitelist", "none") == ""
assert access.sections(public)["D-Star"].get("whitelist", "none") == ""

with tempfile.TemporaryDirectory() as temp:
    ini = Path(temp) / "MMDVM-Host.ini"
    state = Path(temp) / "policy.json"
    ini.write_text(BASE)
    request = {"mode": "semi_public", "allowed": [{"callsign": "PY2ABC", "dmr_id": "7247777"}]}
    assert access.apply(ini, state, "2pny-mmdvmhost.service", request, True)["dry_run"]
    assert ini.read_text() == BASE
    with patch.object(access, "service", side_effect=[True, False, True]):
        try:
            access.apply(ini, state, "2pny-mmdvmhost.service", request, False)
            raise AssertionError("expected failure")
        except access.AccessError as exc:
            assert "policy_rolled_back" in str(exc)
    assert ini.read_text() == BASE
    assert not state.exists()
    with patch.object(access, "service", side_effect=[True, True, True]):
        outcome = access.apply(ini, state, "2pny-mmdvmhost.service", request, False)
    assert outcome["ok"] and outcome["applied"]
    assert state.is_file()
    assert state.stat().st_mode & 0o077 == 0

print("RF_ACCESS_500001_SW_TEST_OK")
