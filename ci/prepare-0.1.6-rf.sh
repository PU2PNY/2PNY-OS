#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-.}"
SELF_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

install -m 0755 "$SELF_DIR/../src/2pny-rf-apply" rootfs-overlay/usr/local/sbin/2pny-rf-apply
install -m 0755 "$SELF_DIR/../src/2pny-perf-snapshot" rootfs-overlay/usr/local/sbin/2pny-perf-snapshot

python3 - <<'PY'
from pathlib import Path
import re

root = Path('.')

# Version bump.
for rel in ['builder/build-image.sh', 'rootfs-overlay/usr/local/sbin/2pny-firstboot', 'src/2pnyd/main.go']:
    p = root / rel
    s = p.read_text()
    s = s.replace('0.1.5-alpha', '0.1.6-alpha').replace('Alpha 0.1.5', 'Alpha 0.1.6')
    p.write_text(s)
(root / 'rootfs-overlay/etc/2pny/version').write_text('0.1.6-alpha\n')

# Native MMDVMHost service. It remains dormant until RF is atomically applied.
svc = root / 'rootfs-overlay/etc/systemd/system/2pny-mmdvmhost.service'
svc.write_text('''[Unit]
Description=2PNY MMDVMHost radio engine
After=systemd-udev-settle.service
ConditionPathExists=/var/lib/2pny/rf-configured
StartLimitIntervalSec=30
StartLimitBurst=5

[Service]
Type=simple
User=mmdvm
Group=mmdvm
SupplementaryGroups=dialout
ExecStart=/usr/local/bin/MMDVM-Host /etc/2pny/mmdvm/MMDVM-Host.ini
Restart=on-failure
RestartSec=2
TimeoutStartSec=12
TimeoutStopSec=5
KillSignal=SIGTERM
NoNewPrivileges=yes
PrivateTmp=yes
ProtectHome=yes
ProtectSystem=strict
ProtectKernelTunables=yes
ProtectKernelModules=yes
ProtectControlGroups=yes
RestrictSUIDSGID=yes
LockPersonality=yes
MemoryMax=96M
TasksMax=64
OOMScoreAdjust=-250

[Install]
WantedBy=multi-user.target
''')

# Directories exist even before RF configuration, but no valid radio config is shipped.
(root / 'rootfs-overlay/etc/2pny/mmdvm').mkdir(parents=True, exist_ok=True)
(root / 'rootfs-overlay/var/lib/2pny/backups/rf').mkdir(parents=True, exist_ok=True)

# Keep hardware probing from fighting MMDVMHost for an already-owned serial port.
probe = root / 'rootfs-overlay/usr/local/sbin/2pny-hardware-probe'
ps = probe.read_text()
probe_marker = '# 2PNY_RF_OWNERSHIP_GUARD'
if probe_marker not in ps:
    anchor = "OUT = Path('/var/lib/2pny/hardware-probe.json')\nOUT.parent.mkdir(parents=True, exist_ok=True)\n"
    if anchor not in ps:
        raise SystemExit('hardware probe ownership anchor not found')
    guard = anchor + '''\n# 2PNY_RF_OWNERSHIP_GUARD\n# Once MMDVMHost owns the modem, do not open the same UART merely to refresh the dashboard.\ndef radio_service_active():\n    try:\n        import subprocess\n        return subprocess.run([\"systemctl\", \"is-active\", \"--quiet\", \"2pny-mmdvmhost.service\"], timeout=1).returncode == 0\n    except Exception:\n        return False\n\n'''
    ps = ps.replace(anchor, guard, 1)
probe.write_text(ps)

# Build MMDVMHost inside the target Debian rootfs, pinned to a verified upstream commit.
p = root / 'builder/build-image.sh'
s = p.read_text()
s = s.replace('wpasupplicant rfkill wireless-regdb', 'wpasupplicant rfkill wireless-regdb libmosquitto1')
marker = '# 2PNY_MMDVMHOST_NATIVE_0_1_6'
if marker not in s:
    m = re.search(r'(?m)^echo "\[5/9\] Aplicando overlay 2PNY\.\.\."\s*$', s)
    if not m:
        raise SystemExit('MMDVMHost build insertion anchor not found')
    block = r'''# 2PNY_MMDVMHOST_NATIVE_0_1_6
MMDVMHOST_COMMIT="590c531391dfd3146073afbc3956f70d42c62a46"
echo "[4b/9] Compilando MMDVMHost nativo (${MMDVMHOST_COMMIT:0:12})..."
chroot "$ROOT_MNT" env DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends g++ make git libmosquitto-dev
chroot "$ROOT_MNT" env MMDVMHOST_COMMIT="$MMDVMHOST_COMMIT" /bin/bash -s <<'MMDVM_BUILD'
set -euo pipefail
SRC=/tmp/MMDVM-Host
rm -rf "$SRC"
git init -q "$SRC"
cd "$SRC"
git remote add origin https://github.com/g4klx/MMDVM-Host.git
git fetch -q --depth=1 origin "$MMDVMHOST_COMMIT"
git checkout -q --detach FETCH_HEAD
test "$(git rev-parse HEAD)" = "$MMDVMHOST_COMMIT"
JOBS=$(nproc 2>/dev/null || echo 1)
[ "$JOBS" -gt 2 ] && JOBS=2
make -j"$JOBS" \
  CFLAGS='-O2 -pipe -DNDEBUG -Wall -std=c++17 -Wno-psabi -pthread -MMD -MD -I/usr/local/include' \
  LDFLAGS='-Wl,-O1 -Wl,--as-needed -L/usr/local/lib'
strip --strip-unneeded MMDVM-Host
install -D -m 0755 MMDVM-Host /usr/local/bin/MMDVM-Host
mkdir -p /usr/share/2pny/upstream
printf '%s\n' "$MMDVMHOST_COMMIT" >/usr/share/2pny/upstream/MMDVMHost.commit
cd /
rm -rf "$SRC"
getent group mmdvm >/dev/null || groupadd --system mmdvm
id mmdvm >/dev/null 2>&1 || useradd --system --gid mmdvm --groups dialout --home-dir /nonexistent --shell /usr/sbin/nologin mmdvm
usermod -a -G dialout mmdvm
apt-get purge -y g++ make git libmosquitto-dev
apt-get install -y --no-install-recommends libmosquitto1
apt-get autoremove -y --purge
apt-get clean
rm -rf /var/lib/apt/lists/*
MMDVM_BUILD

'''
    s = s[:m.start()] + block + s[m.start():]
p.write_text(s)

# Extend source validation with the RF/performance layer.
p = root / 'builder/validate-source.sh'
vs = p.read_text()
check_marker = '# 2PNY_0_1_6_SOURCE_CHECK'
if check_marker not in vs:
    vs += '''\n# 2PNY_0_1_6_SOURCE_CHECK\nfor f in \\\n  rootfs-overlay/usr/local/sbin/2pny-rf-apply \\\n  rootfs-overlay/usr/local/sbin/2pny-perf-snapshot \\\n  rootfs-overlay/etc/systemd/system/2pny-mmdvmhost.service; do\n  test -s "$f" || { echo "missing 0.1.6 file: $f" >&2; exit 1; }\ndone\ngrep -q '590c531391dfd3146073afbc3956f70d42c62a46' builder/build-image.sh\ngrep -q 'MemoryMax=96M' rootfs-overlay/etc/systemd/system/2pny-mmdvmhost.service\n'''
p.write_text(vs)
PY

chmod 0755 \
  rootfs-overlay/usr/local/sbin/2pny-rf-apply \
  rootfs-overlay/usr/local/sbin/2pny-perf-snapshot \
  builder/build-image.sh builder/validate-source.sh

echo '2PNY 0.1.6 RF/MMDVMHost and performance layer applied'
