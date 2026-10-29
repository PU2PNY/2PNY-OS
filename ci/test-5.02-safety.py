#!/usr/bin/env python3
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]

def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT/'runtime/5.02'/f'{name}.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

class SafetyTests(unittest.TestCase):
    def test_nested_and_log_secrets(self):
        d = load('diagnostics')
        value = {'Password':'NEVER_EXPORT','nested':[{'api_key':'NEVER_EXPORT'}],
                 'log':'normal\n{"token":"NEVER_EXPORT"}\nsecret NEVER_EXPORT',
                 'Callsign':'TEST'}
        result = d.scrub(value)
        self.assertNotIn('NEVER_EXPORT',json.dumps(result))
        self.assertEqual(result['Callsign'],'TEST')

    def test_missing_and_oversized(self):
        d = load('diagnostics')
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory)/'big'
            p.write_bytes(b'X'*(d.LIMIT+1))
            self.assertEqual(d.read(p)['state'],'unavailable')
            self.assertEqual(d.read(p.with_name('absent'))['state'],'unavailable')

    def run_reset(self, live, request=None):
        m = load('reset')
        with tempfile.TemporaryDirectory() as directory:
            m.BASE = Path(directory)
            m.REQUEST = m.BASE/'request.json'
            m.RESULT = m.BASE/'result.json'
            m.REQUEST.write_text(json.dumps(request or {'action':'reset-mmdvm'}))
            (m.BASE/'live-state.json').write_text(json.dumps(live))
            with patch.object(m.subprocess,'run') as run:
                m.main()
                return json.loads(m.RESULT.read_text()),run.call_args_list

    def test_reset_busy_rejected_without_restart(self):
        result,calls = self.run_reset({'active':{'mode':'tx'}})
        self.assertFalse(result['ok'])
        self.assertEqual(calls,[])

    def test_arbitrary_command_rejected(self):
        result,calls = self.run_reset({'active':None},{'action':'reboot'})
        self.assertFalse(result['ok'])
        self.assertEqual(calls,[])

    def test_unknown_radio_state_rejected(self):
        result,calls = self.run_reset({})
        self.assertFalse(result['ok'])
        self.assertEqual(calls,[])

    def test_standby_only_fixed_service(self):
        result,calls = self.run_reset({'active':None,'standby':True})
        self.assertTrue(result['ok'])
        self.assertEqual(calls[0].args[0],['systemctl','try-restart','2pny-mmdvmhost.service'])
        self.assertEqual(result['hw'],'not_verified')

if __name__ == '__main__':
    unittest.main()
