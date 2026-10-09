#!/bin/bash
set -euo pipefail
ROOT="${1:?root mount required}"

test "$(cat "$ROOT/etc/2pny/version")" = '0.3.31.119'
test -f "$ROOT/usr/local/sbin/2pny-display-apply"
test -x "$ROOT/usr/local/bin/NextionDriver-pu2pny"
test -f "$ROOT/etc/systemd/system/2pny-nextiondriver.service"
test -f "$ROOT/etc/avahi/avahi-daemon.conf"
test -x "$ROOT/usr/sbin/avahi-daemon"
test -d "$ROOT/etc/NetworkManager/dispatcher.d"

cp -a "$ROOT/usr/local/sbin/2pny-display-apply" "$ROOT/usr/local/sbin/2pny-display-apply.0.3.31.119.bak"
cp -a "$ROOT/etc/avahi/avahi-daemon.conf" "$ROOT/etc/avahi/avahi-daemon.conf.0.3.31.119.bak"

ROOT="$ROOT" python3 - <<'PY'
import os
from pathlib import Path
root = Path(os.environ['ROOT'])

# DISPLAY-028: after the atomic MMDVMHost/NextionDriver configuration write,
# an already-running NextionDriver must be restarted so it reads the new
# renderer/layout/Transparent Data settings. Keep the existing rollback path.
p = root/'usr/local/sbin/2pny-display-apply'
s = p.read_text()
old = 'if not ctl("enable","--now",NEXTIONDRIVER):'
new = 'if (not ctl("enable",NEXTIONDRIVER)) or (not ctl("restart",NEXTIONDRIVER)):'
if s.count(old) != 1:
    raise SystemExit(f'DISPLAY-028 anchor count={s.count(old)}')
s = s.replace(old, new, 1)
p.write_text(s)

# NET-038: make the canonical hostname explicit in Avahi without changing
# NetworkManager, Wi-Fi profiles, DHCP, RF or protocol routing.
p = root/'etc/avahi/avahi-daemon.conf'
s = p.read_text()
lines = s.splitlines()
out = []
in_server = False
seen_server = False
seen_host = False
seen_ipv4 = False
for line in lines:
    stripped = line.strip()
    if stripped.startswith('[') and stripped.endswith(']'):
        if in_server:
            if not seen_host: out.append('host-name=pu2pny')
            if not seen_ipv4: out.append('use-ipv4=yes')
        in_server = stripped.lower() == '[server]'
        if in_server:
            seen_server = True
            seen_host = False
            seen_ipv4 = False
        out.append(line)
        continue
    if in_server and (stripped.startswith('host-name=') or stripped.startswith('#host-name=')):
        if not seen_host:
            out.append('host-name=pu2pny')
            seen_host = True
        continue
    if in_server and (stripped.startswith('use-ipv4=') or stripped.startswith('#use-ipv4=')):
        if not seen_ipv4:
            out.append('use-ipv4=yes')
            seen_ipv4 = True
        continue
    out.append(line)
if in_server:
    if not seen_host: out.append('host-name=pu2pny')
    if not seen_ipv4: out.append('use-ipv4=yes')
if not seen_server:
    out.extend(['', '[server]', 'host-name=pu2pny', 'use-ipv4=yes'])
p.write_text('\n'.join(out).rstrip()+'\n')
PY

cat >"$ROOT/etc/NetworkManager/dispatcher.d/90-pu2pny-mdns" <<'EOF'
#!/bin/sh
# NET-038: event-driven re-announcement of pu2pny.local after an uplink change.
# No polling and no modification of Wi-Fi/Ethernet profiles.
case "${2:-}" in
  up|dhcp4-change|dhcp6-change|connectivity-change)
    /bin/systemctl try-restart avahi-daemon.service >/dev/null 2>&1 || true
    ;;
esac
exit 0
EOF
chmod 0755 "$ROOT/etc/NetworkManager/dispatcher.d/90-pu2pny-mdns"

# Ensure Avahi is enabled in the image; do not start host services while mounted.
systemctl --root="$ROOT" enable avahi-daemon.service >/dev/null

printf '0.3.31.120\n' >"$ROOT/etc/2pny/version"

python3 -m py_compile "$ROOT/usr/local/sbin/2pny-display-apply"
grep -Fq 'if (not ctl("enable",NEXTIONDRIVER)) or (not ctl("restart",NEXTIONDRIVER)):' "$ROOT/usr/local/sbin/2pny-display-apply"
grep -Fq 'host-name=pu2pny' "$ROOT/etc/avahi/avahi-daemon.conf"
grep -Fq 'use-ipv4=yes' "$ROOT/etc/avahi/avahi-daemon.conf"
grep -Fq 'try-restart avahi-daemon.service' "$ROOT/etc/NetworkManager/dispatcher.d/90-pu2pny-mdns"
test "$(cat "$ROOT/etc/2pny/version")" = '0.3.31.120'
echo PATCH_IMAGE_0331120_OK
