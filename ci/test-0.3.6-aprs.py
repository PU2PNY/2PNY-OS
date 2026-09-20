#!/usr/bin/env python3
"""Deterministic APRS-IS messaging regressions for PU2PNY-OS 0.3.6."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/"src/2pny-aprs-0.3.6.py"

def load_module():
    spec=importlib.util.spec_from_file_location("pu2pny_aprs_036",SRC)
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

class FakeSocket:
    def __init__(self,fail=False):
        self.fail=fail
        self.sent=[]
    def sendall(self,data):
        if self.fail:
            raise OSError("simulated link failure")
        self.sent.append(data.decode("ascii"))

class APRSTests(unittest.TestCase):
    def test_login_requires_explicit_verified_logresp(self):
        m=load_module()
        call="PU2ABC-10"
        line=m.login_line(call)
        self.assertIn("user PU2ABC-10 pass ",line)
        self.assertIn("vers PU2PNY-OS 0.3.6",line)
        self.assertNotIn("m/500",line)
        self.assertTrue(m.parse_logresp("# logresp PU2ABC-10 verified, server T2TEST",call))
        self.assertFalse(m.parse_logresp("# logresp PU2ABC-10 unverified, server T2TEST",call))
        self.assertIsNone(m.parse_logresp("# aprsc 2.1",call))

    def test_outbox_network_failure_preserves_message(self):
        m=load_module()
        with tempfile.TemporaryDirectory() as td:
            m.OUTBOX=Path(td)/"outbox";m.STORE=Path(td)/"messages.json"
            m.OUTBOX.mkdir()
            q=m.OUTBOX/"001.json"
            q.write_text(json.dumps({"to":"PY2ABC","text":"teste","id":"12345"}))
            store={"messages":[],"unread":0}
            with self.assertRaises(OSError):
                m.consume_outbox(FakeSocket(fail=True),"PU2ABC-10",store,100.0)
            self.assertTrue(q.exists(),"transient network failure must keep queued message")
            self.assertFalse((m.OUTBOX/"001.bad").exists())
            self.assertEqual(store["messages"],[])

    def test_outbox_send_and_ack_state(self):
        m=load_module()
        with tempfile.TemporaryDirectory() as td:
            m.OUTBOX=Path(td)/"outbox";m.STORE=Path(td)/"messages.json"
            m.OUTBOX.mkdir()
            q=m.OUTBOX/"001.json"
            q.write_text(json.dumps({"to":"PY2ABC","text":"ola","id":"54321"}))
            store={"messages":[],"unread":0}
            sock=FakeSocket()
            self.assertEqual(m.consume_outbox(sock,"PU2ABC-10",store,100.0),1)
            self.assertFalse(q.exists())
            self.assertIn("PU2ABC-10>APRS,TCPIP*::PY2ABC  :ola{54321",sock.sent[0])
            item=store["messages"][-1]
            self.assertEqual(item["status"],"waiting_ack")
            self.assertEqual(item["attempts"],1)
            self.assertTrue(m.apply_ack(store,"PY2ABC","54321","ack"))
            self.assertEqual(store["messages"][-1]["status"],"ack")

    def test_duplicate_incoming_is_not_counted_twice(self):
        m=load_module()
        with tempfile.TemporaryDirectory() as td:
            m.STORE=Path(td)/"messages.json"
            store={"messages":[],"unread":0}
            self.assertTrue(m.record_incoming(store,"PY2ABC","ola","001"))
            self.assertFalse(m.record_incoming(store,"PY2ABC","ola","001"))
            self.assertEqual(store["unread"],1)
            self.assertEqual(len(store["messages"]),1)

    def test_retry_is_bounded_and_reuses_same_id(self):
        m=load_module()
        with tempfile.TemporaryDirectory() as td:
            m.STORE=Path(td)/"messages.json"
            store={"messages":[{
                "direction":"out","station":"PY2ABC","text":"ola","id":"77777",
                "status":"waiting_ack","attempts":1,"last_attempt_epoch":10.0
            }],"unread":0}
            sock=FakeSocket()
            self.assertEqual(m.retry_unacked(sock,"PU2ABC-10",store,41.0),1)
            self.assertIn("{77777",sock.sent[-1])
            self.assertEqual(store["messages"][0]["attempts"],2)
            self.assertEqual(m.retry_unacked(sock,"PU2ABC-10",store,100.0),0)
            self.assertEqual(m.retry_unacked(sock,"PU2ABC-10",store,132.0),1)
            self.assertEqual(store["messages"][0]["attempts"],3)
            self.assertEqual(m.retry_unacked(sock,"PU2ABC-10",store,313.0),0)
            self.assertEqual(store["messages"][0]["status"],"no_ack")
            self.assertEqual(len(sock.sent),2)

    def test_direct_message_parser_and_ack(self):
        m=load_module()
        line="PY2ABC>APRS,TCPIP*::PU2ABC-10:teste{123"
        msg=m.parse_message(line,"PU2ABC-10")
        self.assertEqual(msg,{"type":"message","source":"PY2ABC","text":"teste","id":"123"})
        ack=m.parse_message("PY2ABC>APRS,TCPIP*::PU2ABC-10:ack123","PU2ABC-10")
        self.assertEqual(ack["type"],"ack")
        self.assertEqual(ack["id"],"123")

if __name__=="__main__":
    unittest.main(verbosity=2)
