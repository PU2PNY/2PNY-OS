#!/usr/bin/env python3
"""Run the actual pinned upstream renderer against an isolated MQTT broker.
Synthetic TEST messages are fixtures only, never installed or presented as telemetry.
"""
import configparser
import importlib.util
import json
import os
from pathlib import Path
import select
import socket
import subprocess
import sys
import tempfile
import time

repo = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo/'runtime/display'))
from mqtt_link import Link
import adapter
binary = sys.argv[1]
with tempfile.TemporaryDirectory() as work:
    work = Path(work)
    broker_cfg = work/'mosquitto.conf'
    broker_cfg.write_text('listener 18883 127.0.0.1\nallow_anonymous true\n'+('user root\n' if os.geteuid()==0 else ''))
    broker = subprocess.Popen(['mosquitto','-c',str(broker_cfg)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    renderer = bridge = None
    try:
        for _ in range(50):
            try:
                link = Link('127.0.0.1',18883,'display-smoke')
                break
            except OSError:
                time.sleep(.1)
        else:
            raise RuntimeError('Isolated MQTT broker failed')
        link.subscribe(['host/display-in', adapter.INFO+'/command'])
        host = work/'MMDVM-Host.ini'
        host.write_text('[General]\nCallsign=TEST\nId=1234567\nDuplex=0\n[Modem]\nRXFrequency=430000000\nTXFrequency=430000000\n[MQTT]\nHost=127.0.0.1\nPort=18883\nName=host\nAuth=0\n')
        settings = work/'settings.json'
        settings.write_text('{"renderer":"mmdvmhost-native","type":"nextion_mmdvm"}')
        command = 'import sys;from pathlib import Path;sys.path.insert(0,sys.argv[1]);import adapter;adapter.HOST=Path(sys.argv[2]);adapter.SETTINGS=Path(sys.argv[3]);adapter.main()'
        # Exercise the exact ON7LDS UDP framing independently of physical hardware.
        settings.write_text('{"renderer":"on7lds-compatible","type":"nextion_mmdvm"}')
        udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp.bind(('127.0.0.1',40194))
        udp.settimeout(3)
        bridge = subprocess.Popen([sys.executable,'-c',command,str(repo/'runtime/display'),str(host),str(settings)])
        time.sleep(.5)
        udp.sendto(b'\x80page MMDVM\xff\xff\xff',('127.0.0.1',40195))
        routed = False
        deadline = time.monotonic()+3
        while time.monotonic()<deadline and not routed:
            if select.select([link.sock],[],[],.2)[0]:
                routed = any(t=='host/display-in' and d==b'page MMDVM\xff\xff\xff' for t,d in link.receive())
        assert routed, 'ON7LDS command was not routed to MQTT'
        link.publish('host/display-out',b'\x01\xff\xff\xff')
        assert udp.recvfrom(512)[0] == b'\x80\x01\xff\xff\xff'
        bridge.terminate();bridge.wait(timeout=5);udp.close()
        settings.write_text('{"renderer":"mmdvmhost-native","type":"nextion_mmdvm"}')
        print('ON7LDS_MODEM_MQTT_ROUNDTRIP_SW_PASS')
        bridge = subprocess.Popen([sys.executable,'-c',command,str(repo/'runtime/display'),str(host),str(settings)])
        config = work/'display.ini'
        config.write_text('[General]\nDisplay=Nextion\nDaemon=0\n[Log]\nDisplayLevel=0\nMQTTLevel=0\n[MQTT]\nHost=127.0.0.1\nPort=18883\nKeepalive=60\nAuth=0\nName=display-smoke-renderer\nHostMQTTName=host\nInfoMQTTName='+adapter.INFO+'\nHostConfName=MMDVM-Host\n[Nextion]\nPort=modem\nSpeed=9600\nScreenLayout=0\nBrightness=50\nIdleBrightness=20\nDisplayClock=1\nUTC=0\n')
        log = open(work/'renderer.log','wb')
        renderer = subprocess.Popen([binary,str(config)],stdout=log,stderr=log)
        seen = bytearray()
        sent = False
        deadline = time.monotonic()+18
        while time.monotonic()<deadline:
            if select.select([link.sock],[],[],.2)[0]:
                for topic, data in link.receive():
                    if topic == 'host/display-in':
                        seen.extend(data)
                        # Real modem reply framing is simulated, never a physical PASS.
                        link.publish('host/display-out',b'\x01\xff\xff\xff')
            if b'TEST/1234567' in seen and not sent:
                link.publish('host/json',json.dumps({'DMR':{'action':'start','slot':2,'src_info':'TEST-CALLER','dst_id':91,'group':'yes','source':'rf'}}))
                sent = True
            if b'TEST-CALLER' in seen and b'TG91' in seen:
                break
            if renderer.poll() is not None or bridge.poll() is not None:
                raise RuntimeError('Renderer/adapter exited: '+(work/'renderer.log').read_text())
        assert b'page MMDVM' in seen, repr(seen)
        assert b'TEST/1234567' in seen, repr(seen)
        assert b'TEST-CALLER' in seen and b'TG91' in seen, repr(seen)
        print('OFFICIAL_RENDERER_MQTT_STANDBY_DMR_COMMANDS_SW_PASS')
    finally:
        for proc in (renderer, bridge, broker):
            if proc:
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()
