#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-}"
[[ -n "$ROOT" && "$ROOT" == /* && -d "$ROOT" ]] || { echo "usage: $0 <mounted-root>" >&2; exit 2; }
[[ -f "$ROOT/etc/2pny/version" ]] || { echo "PU2PNY root marker missing" >&2; exit 2; }
BASE_VERSION="$(cat "$ROOT/etc/2pny/version")"
[[ "$BASE_VERSION" == "4.00.001" ]] || { echo "expected 4.00.001 base, got $BASE_VERSION" >&2; exit 2; }

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DISPLAY_HELPER="$REPO/runtime/2pny-display-config.py"
HELIX_HELPER="$REPO/runtime/2pny-helix-mode.py"
DISPLAY_HTML="$REPO/runtime/display-4.00.002.html"
HELIX_HTML="$REPO/runtime/helix-4.00.002.html"
for p in "$DISPLAY_HELPER" "$HELIX_HELPER" "$DISPLAY_HTML" "$HELIX_HTML"; do
  [[ -s "$p" ]] || { echo "required source missing: $p" >&2; exit 2; }
done

PYTHONPYCACHEPREFIX="/tmp/pu2pny-400002-pycache" python3 -m py_compile "$DISPLAY_HELPER" "$HELIX_HELPER"
install -d -m 0755 "$ROOT/usr/local/sbin" "$ROOT/usr/share/2pny" "$ROOT/etc/systemd/system"
install -d -m 0700 "$ROOT/var/lib/2pny/display" "$ROOT/var/lib/2pny/helix"
install -m 0755 "$DISPLAY_HELPER" "$ROOT/usr/local/sbin/2pny-display-config"
install -m 0755 "$HELIX_HELPER" "$ROOT/usr/local/sbin/2pny-helix-mode"
install -m 0644 "$DISPLAY_HTML" "$ROOT/usr/share/2pny/display.html"
install -m 0644 "$HELIX_HTML" "$ROOT/usr/share/2pny/helix.html"

# DISPLAY-035: supervise the official ON7LDS driver in foreground. In the
# upstream source, -d means debug/foreground (become_daemon=FALSE), not
# "daemonize". The driver is disabled until an enhanced Nextion mode is chosen.
cat > "$ROOT/etc/systemd/system/2pny-nextiondriver.service" <<'EOF'
[Unit]
Description=PU2PNY-OS ON7LDS NextionDriver
After=local-fs.target network.target
Before=2pny-mmdvmhost.service
ConditionPathExists=/usr/local/bin/NextionDriver-pu2pny
ConditionPathExists=/var/lib/2pny/mmdvm/MMDVM-Host.ini

[Service]
Type=simple
ExecStart=/usr/local/bin/NextionDriver-pu2pny -d -i -c /var/lib/2pny/mmdvm/MMDVM-Host.ini
Restart=on-failure
RestartSec=2
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=full
ProtectHome=true
ReadWritePaths=/run /var/lib/2pny /var/log

[Install]
WantedBy=multi-user.target
EOF

# Fresh 4.00.002 images do not silently enable enhanced-driver mode. The
# configurator enables it only when the user selects an enhanced Nextion type.
rm -f "$ROOT/etc/systemd/system/multi-user.target.wants/2pny-nextiondriver.service"

# Retire the prior custom display-apply path from active policy while preserving
# the historical endpoint as a compatibility shim. New configuration is owned
# only by 2pny-display-config and MMDVMHost/NextionDriver semantics.
cat > "$ROOT/usr/local/sbin/2pny-display-apply" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
action="${1:-status}"
case "$action" in
  status) exec /usr/local/sbin/2pny-display-config status ;;
  apply)  exec /usr/local/sbin/2pny-display-config apply ;;
  *) printf '{"ok":false,"error":"deprecated_display_command"}\n'; exit 1 ;;
esac
EOF
chmod 0755 "$ROOT/usr/local/sbin/2pny-display-apply"

printf '%s\n' '4.00.002' > "$ROOT/etc/2pny/version"

# Helix services/binary already come from the validated 4.00.001 base and stay
# disabled by default. The new controller only starts them after an explicit
# user action; no RF or gateway service is modified here.
[[ -x "$ROOT/usr/local/bin/helix-daemon" ]] || echo "HELIX_BINARY_NOT_PRESENT_IN_BASE" >&2

# Static/offline structural gates.
grep -Fq 'NextionDriver-pu2pny -d -i -c /var/lib/2pny/mmdvm/MMDVM-Host.ini' "$ROOT/etc/systemd/system/2pny-nextiondriver.service"
grep -Fq 'Nextion (enhanced w/driver, attached to modem)' "$ROOT/usr/share/2pny/display.html"
grep -Fq 'ON7LDS L3 HS' "$ROOT/usr/share/2pny/display.html"
grep -Fq 'Rotacionar tela' "$ROOT/usr/share/2pny/display.html"
grep -Fq 'legacy_protocol_transcoding_available' "$ROOT/usr/local/sbin/2pny-helix-mode"
! grep -Rqs --include='*.service' 'helix-voice.*WantedBy=multi-user.target' "$ROOT/etc/systemd/system" || true

echo "PATCH_IMAGE_400002_OK"
