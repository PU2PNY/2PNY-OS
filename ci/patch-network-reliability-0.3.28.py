#!/usr/bin/env python3
from pathlib import Path
import sys

root=Path(sys.argv[1]).resolve()
net=root/"rootfs-overlay/usr/local/sbin/2pny-network-switch"
wifi=root/"rootfs-overlay/usr/local/sbin/2pny-wifi-profiles"

def replace_exact(text, old, new, label, count=None):
    found=text.count(old)
    if found==0:
        raise SystemExit(f"0.3.28 network patch: missing {label}")
    if count is not None and found!=count:
        raise SystemExit(f"0.3.28 network patch: unexpected {label} count={found}")
    return text.replace(old,new)

n=net.read_text()
n=replace_exact(n,"sleep 0.3\n  rfkill unblock wifi","sleep 1\n  rfkill unblock wifi","radio reset settle",1)
n=replace_exact(n,'ip link set "$iface" up >/dev/null 2>&1 || true\n  sleep 0.3','ip link set "$iface" up >/dev/null 2>&1 || true\n  sleep 1',"radio reset up settle",1)
n=replace_exact(n,"ipv4.method auto ipv4.dhcp-timeout 12 ipv4.route-metric 50","ipv4.method auto ipv4.dhcp-timeout 30 ipv4.route-metric 50","candidate DHCP")
n=replace_exact(n,"nmcli --wait 14 connection up PU2PNY-WIFI-CANDIDATE","nmcli --wait 45 connection up PU2PNY-WIFI-CANDIDATE","association wait",1)
n=replace_exact(n,"connection.autoconnect yes connection.autoconnect-priority 200 connection.autoconnect-retries 2","connection.autoconnect yes connection.autoconnect-priority 200 connection.autoconnect-retries 3","primary retries")
n=replace_exact(n,"for _ in $(seq 1 16); do","for _ in $(seq 1 30); do","IPv4 confirmation",1)
n=replace_exact(n,"    sleep 0.5\n  done","    sleep 1\n  done","IPv4 confirmation interval",1)
net.write_text(n)

w=wifi.read_text()
w=replace_exact(w,"connection.autoconnect-priority 150 connection.autoconnect-retries 2","connection.autoconnect-priority 150 connection.autoconnect-retries 3","secondary retries")
w=replace_exact(w,'nm --wait 6 connection up "$chosen" ifname "$iface"','nm --wait 18 connection up "$chosen" ifname "$iface"',"auto-select wait",1)
w=replace_exact(w,'nm --wait 8 connection up "$SECONDARY" ifname "$iface"','nm --wait 22 connection up "$SECONDARY" ifname "$iface"',"secondary switch wait",1)
w=replace_exact(w,'nm --wait 6 connection up uuid "$old_uuid" ifname "$iface"','nm --wait 15 connection up uuid "$old_uuid" ifname "$iface"',"secondary rollback wait")
w=replace_exact(w,"for _ in $(seq 1 8); do","for _ in $(seq 1 15); do","secondary confirm loop",1)
w=replace_exact(w,"    sleep 0.5\n  done","    sleep 1\n  done","secondary confirm interval",1)
w=replace_exact(w,"connection.autoconnect-priority 200 connection.autoconnect-retries 2","connection.autoconnect-priority 200 connection.autoconnect-retries 3","swapped primary retries")
w=replace_exact(w,"connection.autoconnect-priority 150 connection.autoconnect-retries 2","connection.autoconnect-priority 150 connection.autoconnect-retries 3","swapped secondary retries")
wifi.write_text(w)

print("NETWORK_RELIABILITY_0328_OK")
