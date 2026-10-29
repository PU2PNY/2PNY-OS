#!/usr/bin/env python3
"""Official MMDVM-Display metadata + ON7LDS modem transport. Never owns RF UART."""
import configparser
import json
import select
import socket
import subprocess
import time
from pathlib import Path
from mqtt_link import Link

HOST = Path('/var/lib/2pny/mmdvm/MMDVM-Host.ini')
SETTINGS = Path('/var/lib/2pny/display-settings.json')
INFO = 'pu2pny-display-info'
RX_PORT, TX_PORT = 40195, 40194


def host_config():
    cp = configparser.ConfigParser(interpolation=None, strict=False)
    cp.optionxform = str
    cp.read(HOST)
    return cp


def public_config(cp):
    # Explicit whitelist: passwords, network credentials and tokens never leave host.
    allowed = {'General': ('Callsign', 'Id', 'Duplex'), 'Modem': ('RXFrequency', 'TXFrequency')}
    return {'MMDVM-Host': {section: {key: cp.get(section, key) for key in keys if cp.has_option(section, key)}
                           for section, keys in allowed.items()}}


def addresses():
    result = subprocess.run(['ip', '-j', 'address', 'show', 'up'], capture_output=True, text=True, timeout=3, check=True)
    out = []
    for item in json.loads(result.stdout):
        if item.get('ifname') == 'lo':
            continue
        row = {'name': item['ifname']}
        for addr in item.get('addr_info', []):
            if addr.get('scope') == 'global' and addr.get('family') in ('inet', 'inet6'):
                row['ipv4' if addr['family'] == 'inet' else 'ipv6'] = addr['local']
        if len(row) > 1:
            out.append(row)
    return {'Addresses': out}


def cpu_metadata(thermal=Path('/sys/class/thermal/thermal_zone0/temp'),
                 frequency=Path('/sys/devices/system/cpu/cpu0/cpufreq/cpuinfo_cur_freq'),
                 load=Path('/proc/loadavg')):
    """MMDVM-Info compatible CPU metrics from real kernel state; never estimates."""
    result = {}
    for path, key, scale in ((thermal, 'temperature', 1000.0),
                              (frequency, 'frequency', 1000.0)):
        try:
            value = int(path.read_text().strip())
            if value > 0:
                result[key] = round(value / scale, 3)
        except (OSError, ValueError):
            pass
    try:
        avg = float(load.read_text().split()[0])
        if 0 <= avg < 100000:
            result['load'] = avg
    except (OSError, ValueError, IndexError):
        pass
    return result


def main():
    cp = host_config()
    section = 'MQTT'
    name = cp.get(section, 'Name', fallback='host')
    auth = cp.get(section, 'Auth', fallback='0') == '1'
    link = Link(cp.get(section, 'Host', fallback='127.0.0.1'), cp.get(section, 'Port', fallback='1883'),
                'pu2pny-display-adapter', cp.get(section, 'Username') if auth else None,
                cp.get(section, 'Password') if auth else None)
    settings = json.loads(SETTINGS.read_text())
    on7 = settings.get('renderer') == 'on7lds-compatible'
    topics = [INFO+'/command']
    udp = None
    if on7 and settings.get('type') == 'nextion_mmdvm':
        udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp.bind(('127.0.0.1', RX_PORT))
        topics.append(name+'/display-out')
    link.subscribe(topics)
    cpu_deadline = 0.0
    while True:
        if time.monotonic() >= cpu_deadline:
            # Host config polling stops after the first reply in the pinned official
            # renderer. Refresh real identity/frequencies after user configuration changes.
            link.publish(INFO+'/json', json.dumps(public_config(host_config()), separators=(',', ':')))
            cpu = cpu_metadata()
            if cpu:
                link.publish(INFO+'/json', json.dumps({'CPU': cpu}, separators=(',', ':')))
            cpu_deadline = time.monotonic() + 60.0
        ready, _, _ = select.select([link.sock] + ([udp] if udp else []), [], [], 1)
        if udp and udp in ready:
            data, peer = udp.recvfrom(4096)
            # Only display serial frames; reject unrelated transparent-data commands.
            if peer[0] == '127.0.0.1' and data[:1] == b'\x80' and len(data) > 1:
                link.publish(name+'/display-in', data[1:])
        if link.sock in ready:
            for topic, payload in link.receive():
                if topic == name+'/display-out' and udp:
                    udp.sendto(b'\x80'+payload, ('127.0.0.1', TX_PORT))
                elif topic == INFO+'/command':
                    if payload == b'Config MMDVM-Host':
                        link.publish(INFO+'/json', json.dumps(public_config(host_config())))
                    elif payload == b'Addresses':
                        try:
                            link.publish(INFO+'/json', json.dumps(addresses()))
                        except (OSError, ValueError, subprocess.SubprocessError):
                            pass  # No invented fallback IP.
        link.ping()


if __name__ == '__main__':
    main()
