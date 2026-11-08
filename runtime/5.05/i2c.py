#!/usr/bin/env python3
"""DISPLAY-055: find an I2C OLED/LCD the way Pi-Star/WPSD users expect.

The boot probe only lists I2C devices that the kernel already bound, which a
plain OLED never is, and it replaces any I2C hint with "Nextion through the
modem" whenever a MMDVM is present. This module scans the bus read-only
(read_byte on 0x3C/0x3D/0x27/0x3F, like i2cdetect) and honours an explicit
/var/lib/2pny/oled.json choice. It never overrides a proven Nextion profile.
"""
import json
import time
from pathlib import Path

OLED_ADDRESSES = (0x3C, 0x3D)
LCD_ADDRESSES = (0x27, 0x3F)
CONFIG = Path('/var/lib/2pny/oled.json')
UNPROVEN_STATES = ('', 'not_found', 'mmdvm_display_candidate', 'i2c_candidate', 'i2c_scan')
RETRY_SECONDS = 60
_cache = {'at': -1e9, 'found': None}


def scan(bus=1, smbus_factory=None, addresses=OLED_ADDRESSES + LCD_ADDRESSES):
    """Return the first responding address or None. Read-only, 4 tiny transactions."""
    try:
        if smbus_factory is None:
            import smbus
            smbus_factory = smbus.SMBus
        handle = smbus_factory(bus)
    except Exception:
        return None
    try:
        for address in addresses:
            try:
                handle.read_byte(address)
                return address
            except Exception:
                continue
    finally:
        try:
            handle.close()
        except Exception:
            pass
    return None


def read_config(path=None):
    try:
        data = json.loads((path or CONFIG).read_text())
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def choose(display, hw, settings, config=None, scanner=None, clock=time.monotonic):
    """Return fields to merge into the probe's display dict, or None to leave it alone."""
    display = display or {}
    cls, state = str(display.get('class') or ''), str(display.get('state') or '')
    if cls in ('nextion', 'nextion_mmdvm', 'oled', 'lcd') or (settings or {}).get('physical_confirmed'):
        return None
    if cls not in ('', 'display_candidate', 'unknown') or state not in UNPROVEN_STATES:
        return None
    config = read_config() if config is None else config
    wanted = str(config.get('type') or 'auto').lower()
    if wanted == 'none':
        return None
    address = None
    for item in (hw or {}).get('i2c') or []:
        try:
            value = int(str(item.get('address')), 16)
        except (TypeError, ValueError):
            continue
        if value in OLED_ADDRESSES + LCD_ADDRESSES:
            address = value
            break
    if address is None:
        now = clock()
        if now - _cache['at'] >= RETRY_SECONDS:
            _cache['found'] = (scanner or scan)()
            _cache['at'] = now
        address = _cache['found']
    if address is None:
        return None
    try:
        address = int(str(config.get('address')), 16) if config.get('address') else address
    except ValueError:
        pass
    if address in LCD_ADDRESSES or wanted == 'lcd':
        return {'class': 'lcd', 'state': 'i2c_scan', 'address': hex(address), 'bus': 1, 'model': 'HD44780 I2C',
                'lcd_cols': int(config.get('lcd_cols') or 20), 'lcd_rows': int(config.get('lcd_rows') or 4)}
    height = 32 if int(config.get('height') or 64) == 32 and wanted != 'sh1106' else 64
    model = 'SH1106' if wanted == 'sh1106' else 'SSD1306'
    return {'class': 'oled', 'state': 'i2c_scan', 'address': hex(address), 'bus': 1, 'model': model + ' I2C',
            'resolution': f'128x{height}'}
