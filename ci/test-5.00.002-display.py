#!/usr/bin/env python3
"""Display config/secret/scope regression tests; no claim of physical RF or HMI."""
import configparser
import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'runtime/display'))
from mqtt_link import packet
import adapter
spec = importlib.util.spec_from_file_location('display_apply', ROOT/'runtime/display/apply.py')
app = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app)

class DisplayTests(unittest.TestCase):
    def host(self):
        cp = configparser.ConfigParser(interpolation=None)
        cp.optionxform = str
        cp.read_string('[General]\nCallsign=TEST\nId=1234567\nDuplex=0\n[Modem]\nPort=/dev/serial0\nRXFrequency=430000000\nTXFrequency=430000000\n[MQTT]\nName=host\nHost=127.0.0.1\nPort=1883\nAuth=0\nPassword=SECRET\n[DMR Network]\nPassword=SECRET\n')
        return cp

    def test_all_layouts_use_official_renderer(self):
        for layout in (0, 2, 3, 4):
            host = self.host()
            before = app.ini_bytes(host)
            cp, driver, on7, effective, port = app.make_config(host, {'layout':layout}, {}, 'nextion_mmdvm')
            self.assertEqual(app.ini_bytes(host), before)
            self.assertEqual(cp['General']['Display'], 'Nextion')
            self.assertEqual(cp['Nextion']['ScreenLayout'], str(3 if layout in (3,4) else layout))
            self.assertEqual(cp['Nextion']['Port'], str(app.PTY) if on7 else 'modem')
            self.assertEqual(driver['Nextion']['ScreenLayout'], str(layout))
            self.assertEqual(driver['Transparent Data']['LocalPort'], '40195')
            self.assertNotIn('SECRET', app.ini_bytes(driver).decode())

    def test_public_metadata_whitelist(self):
        data = adapter.public_config(self.host())
        self.assertNotIn('SECRET', str(data))
        self.assertEqual(set(data['MMDVM-Host']), {'General', 'Modem'})

    def test_invalid_layout(self):
        with self.assertRaises(ValueError):
            app.make_config(self.host(), {'layout':9}, {}, 'nextion_mmdvm')

    def test_modem_uart_cannot_be_opened_as_display(self):
        with self.assertRaisesRegex(ValueError, 'reservada'):
            app.make_config(self.host(), {'layout':0}, {'port':'/dev/serial0'}, 'nextion')

    def test_mqtt_remaining_length(self):
        self.assertEqual(packet(0x30, b'a'*128)[:3], b'\x30\x80\x01')

    def test_no_rf_mutation_or_restart(self):
        text = (ROOT/'runtime/display/apply.py').read_text()
        self.assertNotIn('ctl(\'restart\', MMDVM', text)
        self.assertNotIn('atomic(HOST', text)
        self.assertNotIn('shutil.copy2', text)
        self.assertNotIn('ctl(\'stop\', \'2pny-mmdvmhost', text)

if __name__ == '__main__':
    unittest.main()
