#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:?mounted arm image root required}"
[[ "$ROOT" == /* && -d "$ROOT" ]] || exit 2
[[ "$(cat "$ROOT/etc/2pny/version")" == '5.00.002' ]] || exit 2
REPO="$(cd "$(dirname "$0")/.." && pwd)"
for p in usr/local/sbin/2pny-display-apply usr/local/sbin/2pny-profile-autostart etc/systemd/system/2pny-profile-autostart.service; do
  test -s "$ROOT/$p"
done
# Preserve the approved production program for forensic rollback.
cp -a "$ROOT/usr/local/sbin/2pny-display-apply" "$ROOT/usr/local/sbin/2pny-display-apply.pre-5.00.003"
install -m 0755 "$REPO/runtime/display/apply.py" "$ROOT/usr/local/sbin/2pny-display-apply"
install -d -m 0755 "$ROOT/etc/systemd/system/2pny-profile-autostart.service.d"
cat >"$ROOT/etc/systemd/system/2pny-profile-autostart.service.d/after-uplink.conf" <<'EOF'
[Unit]
After=network-online.target 2pny-network-online.service 2pny-hardware-detect.service mosquitto.service
Wants=network-online.target
EOF
# Service is present in v5.00.002 but was not symlinked into multi-user target.
install -d -m 0755 "$ROOT/etc/systemd/system/multi-user.target.wants"
ln -sfn ../2pny-profile-autostart.service "$ROOT/etc/systemd/system/multi-user.target.wants/2pny-profile-autostart.service"
# Retry only when no gateway is active; no RF rewriting or silent protocol switching.
cat >"$ROOT/usr/local/sbin/2pny-profile-autostart-safe" <<'EOF'
#!/usr/bin/env python3
import subprocess
import sys
GATEWAYS = ('dmrgateway', 'dstargateway', 'ysfgateway', 'p25gateway', 'nxdngateway', 'dapnetgateway')
for gateway in GATEWAYS:
    cp = subprocess.run(('systemctl', 'is-active', '--quiet', '2pny-'+gateway+'.service'), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False, timeout=10)
    if cp.returncode == 0:
        raise SystemExit(0)
raise SystemExit(subprocess.run(('/usr/local/sbin/2pny-profile-autostart',), check=False, timeout=105).returncode)
EOF
chmod 0755 "$ROOT/usr/local/sbin/2pny-profile-autostart-safe"
cat >"$ROOT/etc/systemd/system/2pny-profile-autostart-retry.service" <<'EOF'
[Unit]
Description=PU2PNY restore proven protocol if no gateway is running
After=network-online.target mosquitto.service 2pny-hardware-detect.service
Wants=network-online.target
[Service]
Type=oneshot
ExecStart=/usr/local/sbin/2pny-profile-autostart-safe
TimeoutStartSec=120
NoNewPrivileges=yes
[Install]
WantedBy=multi-user.target
EOF
cat >"$ROOT/etc/systemd/system/2pny-profile-autostart-retry.timer" <<'EOF'
[Unit]
Description=PU2PNY safe retry last proven profile after uplink delay
[Timer]
OnBootSec=45s
OnUnitInactiveSec=90s
Unit=2pny-profile-autostart-retry.service
[Install]
WantedBy=timers.target
EOF
install -d -m 0755 "$ROOT/etc/systemd/system/timers.target.wants"
ln -sfn ../2pny-profile-autostart-retry.timer "$ROOT/etc/systemd/system/timers.target.wants/2pny-profile-autostart-retry.timer"
# On reboot reconcile persisted display config after the hardware probe, never RF.
cat >"$ROOT/etc/systemd/system/2pny-display-reconcile.service" <<'EOF'
[Unit]
Description=PU2PNY reapply saved display on boot
After=2pny-hardware-detect.service mosquitto.service 2pny-mmdvmhost.service
Wants=2pny-hardware-detect.service mosquitto.service
ConditionPathExists=/var/lib/2pny/display-settings.json
[Service]
Type=oneshot
ExecStart=/usr/local/sbin/2pny-display-apply
TimeoutStartSec=75
[Install]
WantedBy=multi-user.target
EOF
ln -sfn ../2pny-display-reconcile.service "$ROOT/etc/systemd/system/multi-user.target.wants/2pny-display-reconcile.service"
python3 -m py_compile "$ROOT/usr/local/sbin/2pny-display-apply" "$ROOT/usr/local/sbin/2pny-profile-autostart-safe"
python3 - "$ROOT" <<'PY'
import sys
from pathlib import Path
root=Path(sys.argv[1])
exe=root/'usr/local/bin/2pnyd'
raw=exe.read_bytes()
assert b'5.00.002' in raw, 'prior image identity mismatch'
exe.write_bytes(raw.replace(b'5.00.002',b'5.00.003'))
(root/'etc/2pny/version').write_text('5.00.003\n')
PY
echo PU2PNY_500003_OVERLAY_OK
