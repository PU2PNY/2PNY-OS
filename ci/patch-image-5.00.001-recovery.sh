#!/usr/bin/env bash
set -euo pipefail
[[ "$#" -eq 3 ]] || { echo "usage: $0 ROOT BACKEND APPLY" >&2; exit 2; }
ROOT="$1"
BACKEND="$2"
APPLY="$3"
[[ "$ROOT" == /* && -d "$ROOT" ]] || { echo "root path invalid" >&2; exit 2; }
[[ -f "$ROOT/etc/2pny/version" && "$(cat "$ROOT/etc/2pny/version")" == '5.00.000' ]] || { echo "expected immutable 5.00.000 root" >&2; exit 2; }
[[ -s "$BACKEND" && -s "$APPLY" ]] || { echo "backend/apply payload missing" >&2; exit 2; }
REPO="$(cd "$(dirname "$0")/.." && pwd)"
for p in \
  usr/local/bin/MMDVM-Host \
  usr/local/bin/DMRGateway \
  usr/local/bin/NextionDriver-pu2pny \
  usr/local/bin/MMDVM-Display \
  usr/local/sbin/2pny-display-apply \
  usr/share/2pny/hotspot.html \
  etc/systemd/system/2pny-mmdvmhost.service; do
  [[ -e "$ROOT/$p" ]] || { echo "missing published baseline $p" >&2; exit 3; }
done
[[ -f "$REPO/runtime/5x/2pny-rf-access.py" ]] || exit 3
[[ -f "$REPO/runtime/5x/2pny-rf-access-request.py" ]] || exit 3
[[ -f "$REPO/runtime/rf-access-5.00.001.html" ]] || exit 3
python3 -m py_compile "$REPO/runtime/5x/2pny-rf-access.py" "$REPO/runtime/5x/2pny-rf-access-request.py" "$APPLY"
# Rootfs is a disposable copy of a SHA-proven release asset; preserve originals as rollback.
install -m 0755 "$BACKEND" "$ROOT/usr/local/bin/2pnyd"
cp -a "$ROOT/usr/local/sbin/2pny-display-apply" "$ROOT/usr/local/sbin/2pny-display-apply.pre-5.00.001"
install -m 0755 "$APPLY" "$ROOT/usr/local/sbin/2pny-display-apply"
install -d -m 0755 "$ROOT/usr/local/libexec/pu2pny"
install -m 0755 "$REPO/runtime/5x/2pny-rf-access.py" "$ROOT/usr/local/libexec/pu2pny/2pny-rf-access"
install -m 0755 "$REPO/runtime/5x/2pny-rf-access-request.py" "$ROOT/usr/local/libexec/pu2pny/2pny-rf-access-request"
install -m 0644 "$REPO/runtime/rf-access-5.00.001.html" "$ROOT/usr/share/2pny/rf-access.html"
cat >"$ROOT/etc/systemd/system/2pny-rf-access.service" <<'EOF'
[Unit]
Description=PU2PNY-OS restricted RF access policy request
After=2pny-mmdvmhost.service
[Service]
Type=oneshot
User=root
Group=root
ExecStart=/usr/local/libexec/pu2pny/2pny-rf-access-request
NoNewPrivileges=yes
PrivateTmp=yes
ProtectHome=yes
ProtectSystem=full
ReadWritePaths=/run/2pny /var/lib/2pny/mmdvm /var/lib/2pny/access
EOF
cat >"$ROOT/etc/systemd/system/2pny-rf-access.path" <<'EOF'
[Unit]
Description=PU2PNY-OS monitor explicit RF access change request
[Path]
PathChanged=/run/2pny/access-request.json
Unit=2pny-rf-access.service
[Install]
WantedBy=multi-user.target
EOF
# Enable the watcher only. Never apply a policy on boot or after update.
systemctl --root="$ROOT" enable 2pny-rf-access.path >/dev/null
# Link from existing Protocols view without altering its scripts or layout structure.
python3 - "$ROOT/usr/share/2pny/hotspot.html" <<'PY'
from pathlib import Path
import sys
p=Path(sys.argv[1])
text=p.read_text(encoding='utf-8')
anchor='<section class="section" id="protocols">'
link=('<div style="text-align:right;margin:8px 0">'
      '<a href="/rf-access" title="Controle de acesso do rádio" '
      'style="color:var(--blue);font-size:13px">🔒 Acesso RF: Privado / Semi-público / Público</a></div>\n')
if text.count(anchor)!=1 or '/rf-access' in text:
    raise SystemExit('hotspot navigation anchor mismatch')
p.write_text(text.replace(anchor,link+anchor,1),encoding='utf-8')
PY
printf '5.00.001\n' >"$ROOT/etc/2pny/version"
grep -Fq 'href="/rf-access"' "$ROOT/usr/share/2pny/hotspot.html"
grep -Fq 'PathChanged=/run/2pny/access-request.json' "$ROOT/etc/systemd/system/2pny-rf-access.path"
[[ -L "$ROOT/etc/systemd/system/multi-user.target.wants/2pny-rf-access.path" ]]
[[ "$(cat "$ROOT/etc/2pny/version")" == "5.00.001" ]]
echo PATCH_IMAGE_500001_DISPLAY_ACCESS_OK
