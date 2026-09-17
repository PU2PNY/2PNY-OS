#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-.}"
cd "$ROOT"

python3 - <<'PY'
from pathlib import Path
p=Path('rootfs-overlay/usr/local/sbin/2pny-network-core')
s=p.read_text()
repls={
    '  HOSTAPD_PID=$!\n  sleep 1': '  HOSTAPD_PID=$!\n  echo "$HOSTAPD_PID" >"$RUN/hostapd.pid"\n  sleep 1',
    '  DNS_AP_PID=$!\n  sleep .5': '  DNS_AP_PID=$!\n  echo "$DNS_AP_PID" >"$RUN/dnsmasq-ap.pid"\n  sleep .5',
    '  DNS_ETH_PID=$!\n  sleep .5': '  DNS_ETH_PID=$!\n  echo "$DNS_ETH_PID" >"$RUN/dnsmasq-eth.pid"\n  sleep .5',
}
for old,new in repls.items():
    if old not in s:
        raise SystemExit(f'network pid anchor not found: {old!r}')
    s=s.replace(old,new,1)
p.write_text(s)
PY

bash -n rootfs-overlay/usr/local/sbin/2pny-network-core
grep -Fq 'echo "$HOSTAPD_PID" >"$RUN/hostapd.pid"' rootfs-overlay/usr/local/sbin/2pny-network-core
grep -Fq 'echo "$DNS_AP_PID" >"$RUN/dnsmasq-ap.pid"' rootfs-overlay/usr/local/sbin/2pny-network-core
grep -Fq 'echo "$DNS_ETH_PID" >"$RUN/dnsmasq-eth.pid"' rootfs-overlay/usr/local/sbin/2pny-network-core

echo 'PU2PNY 0.1.9 deterministic network pid state applied'
