#!/bin/bash
# PU2PNY-OS 4.00.000 release trigger / pinned Helix packaging
set -euo pipefail
ROOT="${1:?root mount required}"
BINARY="${2:?helix-daemon binary required}"
HELIX_COMMIT="${3:?helix commit required}"

test -d "$ROOT/etc"
test -x "$BINARY"

install -D -m 0755 "$BINARY" "$ROOT/usr/local/bin/helix-daemon"
install -d -m 0755 "$ROOT/usr/share/pu2pny-os"
printf '%s\n' "$HELIX_COMMIT" > "$ROOT/usr/share/pu2pny-os/helix-commit"
chmod 0644 "$ROOT/usr/share/pu2pny-os/helix-commit"

cat > "$ROOT/etc/systemd/system/helix-voice.service" <<'EOF'
[Unit]
Description=Helix Voice Engine PCM observer (shadow only)
ConditionPathExists=/usr/local/bin/helix-daemon
After=local-fs.target

[Service]
Type=simple
ExecStartPre=/usr/local/bin/helix-daemon --self-test
ExecStart=/usr/local/bin/helix-daemon --pcm-observe /run/helix-voice/observe.sock
RuntimeDirectory=helix-voice
RuntimeDirectoryMode=0750
User=root
Group=root
Restart=on-failure
RestartSec=2s
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ProtectKernelTunables=true
ProtectKernelModules=true
ProtectControlGroups=true
RestrictAddressFamilies=AF_UNIX

[Install]
WantedBy=multi-user.target
EOF

cat > "$ROOT/etc/systemd/system/helix-voice-process.service" <<'EOF'
[Unit]
Description=Helix Voice Engine PCM processing bridge (explicit opt-in)
ConditionPathExists=/usr/local/bin/helix-daemon
Conflicts=helix-voice.service
After=local-fs.target

[Service]
Type=simple
ExecStartPre=/usr/local/bin/helix-daemon --self-test
ExecStart=/usr/local/bin/helix-daemon --pcm-bridge /run/helix-voice/process.sock
RuntimeDirectory=helix-voice
RuntimeDirectoryMode=0750
User=root
Group=root
Restart=on-failure
RestartSec=2s
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ProtectKernelTunables=true
ProtectKernelModules=true
ProtectControlGroups=true
RestrictAddressFamilies=AF_UNIX

# Deliberately no [Install] section: process mode cannot be persistently enabled
# by a generic systemctl enable. Activation must be controlled by PU2PNY-OS
# after validation and must retain fail-open fallback to the legacy audio path.
EOF

# Both modes MUST remain disabled in the produced image.
rm -f "$ROOT/etc/systemd/system/multi-user.target.wants/helix-voice.service"
rm -f "$ROOT/etc/systemd/system/multi-user.target.wants/helix-voice-process.service"

grep -Fq 'RestrictAddressFamilies=AF_UNIX' "$ROOT/etc/systemd/system/helix-voice.service"
grep -Fq -- '--pcm-observe' "$ROOT/etc/systemd/system/helix-voice.service"
grep -Fq -- '--pcm-bridge' "$ROOT/etc/systemd/system/helix-voice-process.service"
test ! -e "$ROOT/etc/systemd/system/multi-user.target.wants/helix-voice.service"
test ! -e "$ROOT/etc/systemd/system/multi-user.target.wants/helix-voice-process.service"

echo INSTALL_HELIX_400000_OK
