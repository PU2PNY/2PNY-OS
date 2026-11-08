#!/usr/bin/env python3
"""DISPLAY-045 regression: saved Nextion-via-MMDVM profile must survive a reboot.

After a reboot the hardware probe rewrites hardware-probe.json with
class=display_candidate / state=mmdvm_display_candidate when the modem answered
but no display has been proven yet. The display applier used to treat that as a
real OLED/LCD classification, ignored the saved user profile and fell through to
the legacy OLED/LCD path, so the Nextion never came back.

SW-level test only. It does not prove anything about a physical Nextion (HW).
"""
import importlib.util
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REL = 'runtime/display/apply.py'


def load(source_text, label):
    with tempfile.TemporaryDirectory(prefix='pu2pny-display045-') as td:
        path = Path(td) / (label + '.py')
        path.write_text(source_text)
        spec = importlib.util.spec_from_file_location(label, path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module


fixed = load((ROOT / REL).read_text(), 'apply_fixed')

SAVED_L3 = {'enabled': True, 'type': 'nextion_mmdvm', 'requested_layout': 3}
SAVED_L4 = {'enabled': True, 'type': 'nextion_mmdvm', 'requested_layout': 4}
BOOT_CANDIDATE = {'detected': False, 'state': 'mmdvm_display_candidate',
                  'class': 'display_candidate', 'port': 'modem'}
I2C_CANDIDATE = {'detected': False, 'state': 'i2c_candidate',
                 'class': 'display_candidate', 'address': '0x3c'}


def select(module, d, saved, override=None):
    return module.select_persisted_modem_display(d, saved, override or {})


# 1. The reported defect: boot probe candidate must not hide the saved profile.
for saved in (SAVED_L3, SAVED_L4):
    got = select(fixed, BOOT_CANDIDATE, saved)
    assert got['class'] == 'nextion_mmdvm' and got['port'] == 'modem', got
    assert got['source'] == 'saved_user_profile'
    assert got['physical_confirmed'] is False, 'saved profile is not hardware proof'

# 2. Protections that must not change.
assert select(fixed, I2C_CANDIDATE, SAVED_L3) == I2C_CANDIDATE, 'I2C OLED/LCD candidate must stay protected'
for real in ({'class': 'oled'}, {'class': 'hat_display'}, {'class': 'framebuffer'},
             {'class': 'spi_display'}, {'class': 'usb_display'}):
    assert select(fixed, real, SAVED_L3) == real, real
assert select(fixed, BOOT_CANDIDATE, SAVED_L3, {'enabled': False}) == BOOT_CANDIDATE, 'user disable wins'
assert select(fixed, BOOT_CANDIDATE, {'enabled': True, 'type': 'nextion_mmdvm', 'requested_layout': 2}) == BOOT_CANDIDATE
assert select(fixed, BOOT_CANDIDATE, {'enabled': False, 'type': 'nextion_mmdvm', 'requested_layout': 3}) == BOOT_CANDIDATE
assert select(fixed, BOOT_CANDIDATE, {'enabled': True, 'type': 'oled', 'requested_layout': 3}) == BOOT_CANDIDATE
assert select(fixed, BOOT_CANDIDATE, {}) == BOOT_CANDIDATE, 'never invent a display without a saved profile'

# 3. Behavior that already worked stays identical.
confirmed = {'class': 'nextion_mmdvm', 'detected': True, 'port': 'modem'}
assert select(fixed, confirmed, SAVED_L3) == confirmed
assert select(fixed, {}, SAVED_L3)['source'] == 'saved_user_profile'
assert select(fixed, {'class': 'unknown'}, SAVED_L3)['class'] == 'nextion_mmdvm'

print('TEST_DISPLAY_045_BOOT_REAPPLY_OK')
sys.exit(0)
