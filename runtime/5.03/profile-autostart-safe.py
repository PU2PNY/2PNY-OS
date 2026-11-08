#!/usr/bin/env python3
"""BOOT-053: retry a proven profile if the RF service pair is not healthy."""
import subprocess

GATEWAYS = ('dmrgateway', 'dstargateway', 'ysfgateway', 'p25gateway', 'nxdngateway', 'dapnetgateway')

def active(unit):
    return subprocess.run(('systemctl','is-active','--quiet',unit), check=False,
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                          timeout=10).returncode == 0

# A gateway alone does not prove a working modem. The original autostart
# retains exclusive authority over proof, locks, uplink, and any activation.
if any(active('2pny-' + gateway + '.service') for gateway in GATEWAYS):
    if active('2pny-mmdvmhost.service'):
        raise SystemExit(0)
raise SystemExit(subprocess.run(
    ('/usr/local/sbin/2pny-profile-autostart',), check=False, timeout=105).returncode)
