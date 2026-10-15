#!/bin/bash
set -euo pipefail
ROOT="${1:?root mount required}"

test -d "$ROOT/etc"
test -f "$ROOT/etc/2pny/version"
test "$(cat "$ROOT/etc/2pny/version")" = "4.00.000"
test -f "$ROOT/usr/local/sbin/2pny-display-apply"
test -f "$ROOT/usr/share/2pny/display.html"
test -f "$ROOT/etc/systemd/system/2pny-nextiondriver.service"
test -x "$ROOT/usr/local/bin/NextionDriver-pu2pny"

# DISPLAY-032 — keep the upstream ON7LDS topology, but let systemd own the
# process.  NextionDriver -d forks; Type=simple must run it in foreground.
ROOT="$ROOT" python3 - <<'PY'
import os
from pathlib import Path
root=Path(os.environ['ROOT'])

unit=root/'etc/systemd/system/2pny-nextiondriver.service'
s=unit.read_text()
old='ExecStart=/usr/local/bin/NextionDriver-pu2pny -d -i -vv -c /var/lib/2pny/mmdvm/MMDVM-Host.ini'
new='ExecStart=/usr/local/bin/NextionDriver-pu2pny -i -vv -c /var/lib/2pny/mmdvm/MMDVM-Host.ini'
if s.count(old)!=1:
    raise SystemExit(f'DISPLAY-032 NextionDriver ExecStart anchor count={s.count(old)}')
s=s.replace(old,new,1)
if 'StandardOutput=journal\n' not in s:
    s=s.replace('RestartSec=2\n','RestartSec=2\nStandardOutput=journal\nStandardError=journal\n',1)
unit.write_text(s)

# The physical display behind a modem cannot be reliably queried by
# NextionDriver upstream.  Keep detection as diagnostics only and make the UI
# explicit that the operator selects the HMI/layout already present on screen.
p=root/'usr/share/2pny/display.html'
h=p.read_text()
repls={
    'Display Auto-Detection':'Compatibilidade Pi-Star / WPSD',
    'Detecção automática ao entrar na Internet, renderer e integração física sem disputar a serial do MMDVM.':'Configuração padrão MMDVMHost/NextionDriver. A tela ligada ao modem usa o layout que já está gravado nela; nenhum HMI/TFT é sobrescrito.',
    '<label>Modelo / tamanho</label>':'<label>Modelo / tamanho (informativo)</label>',
    '<option value="auto|" selected>Auto detectar</option>':'<option value="auto|" selected>Não informado</option>',
    '<article class="card"><h2>Auto-provisionamento</h2>':'<article class="card"><h2>Diagnóstico do display</h2>',
    'Hardware reconhecido · HMI/layout não identificado':'Tela via modem · selecione o layout já gravado',
    'Ao conectar à Internet, o PU2PNY executa uma detecção limitada do hardware. O catálogo identifica modelo/resolução quando o equipamento responde com evidência real. Um TFT só poderá ser oferecido quando existir asset oficial publicado com URL + SHA-256. Mesmo assim, a gravação exigirá confirmação explícita no painel.':'A detecção é somente diagnóstica. Em telas Nextion ligadas ao modem, o caminho padrão não depende de COMOK para aplicar a configuração. Selecione G4KLX, ON7LDS L2, L3 ou L3 HS conforme o HMI/TFT já instalado na própria tela.',
    '<div class="notice"><b>Nunca automático:</b> nenhum HMI/TFT será sobrescrito silenciosamente nesta versão.</div>':'<div class="notice"><b>Regra permanente:</b> o PU2PNY-OS não grava nem troca HMI/TFT automaticamente.</div>',
}
for old,new in repls.items():
    if old not in h:
        raise SystemExit('DISPLAY-032 UI anchor missing: '+old[:80])
    h=h.replace(old,new,1)
# Remove wording that implies COMOK is required for a modem-connected display.
h=h.replace(' · sem COMOK',' · retorno não verificável via modem')
h=h.replace('Saída ativa · retorno COMOK ainda não confirmado','Configurado · retorno da tela não verificável via modem')
p.write_text(h)
PY

# BOOT-051 — browser/region selection is already persisted in clock.json by
# the backend. Re-assert that saved IANA timezone on boot without geolocation
# calls or polling. timedatectl is preferred; /etc/localtime is the safe local
# fallback if D-Bus/systemd-timedated is temporarily unavailable.
install -d -m 0755 "$ROOT/usr/local/sbin" "$ROOT/etc/systemd/system"
cat >"$ROOT/usr/local/sbin/2pny-timezone-restore" <<'EOF'
#!/bin/bash
set -euo pipefail
STATE=/var/lib/2pny/settings/clock.json
[[ -r "$STATE" ]] || exit 0
TZ_NAME="$(python3 - "$STATE" <<'PY'
import json,sys
try:
    value=str(json.load(open(sys.argv[1],encoding='utf-8')).get('timezone') or '').strip()
except Exception:
    value=''
print(value)
PY
)"
[[ -n "$TZ_NAME" ]] || exit 0
[[ "$TZ_NAME" != /* ]] || exit 2
[[ "$TZ_NAME" != *..* ]] || exit 2
[[ -e "/usr/share/zoneinfo/$TZ_NAME" ]] || exit 2
CURRENT="$(timedatectl show -p Timezone --value 2>/dev/null || true)"
if [[ "$CURRENT" != "$TZ_NAME" ]]; then
    if ! timedatectl set-timezone "$TZ_NAME" >/dev/null 2>&1; then
        ln -snf "/usr/share/zoneinfo/$TZ_NAME" /etc/localtime
        printf '%s\n' "$TZ_NAME" > /etc/timezone
    fi
fi
exit 0
EOF
chmod 0755 "$ROOT/usr/local/sbin/2pny-timezone-restore"

cat >"$ROOT/etc/systemd/system/2pny-timezone-restore.service" <<'EOF'
[Unit]
Description=PU2PNY-OS restore persisted IANA timezone
After=local-fs.target dbus.service
ConditionPathExists=/var/lib/2pny/settings/clock.json

[Service]
Type=oneshot
ExecStart=/usr/local/sbin/2pny-timezone-restore
User=root
Group=root
NoNewPrivileges=yes
PrivateTmp=yes
ProtectHome=yes
ProtectKernelTunables=yes
ProtectKernelModules=yes
ProtectControlGroups=yes

[Install]
WantedBy=multi-user.target
EOF
systemctl --root="$ROOT" enable 2pny-timezone-restore.service >/dev/null

printf '4.00.001\n' >"$ROOT/etc/2pny/version"

# Static gates on the mounted image.
python3 -m py_compile "$ROOT/usr/local/sbin/2pny-display-apply"
bash -n "$ROOT/usr/local/sbin/2pny-timezone-restore"
grep -Fq 'ExecStart=/usr/local/bin/NextionDriver-pu2pny -i -vv -c /var/lib/2pny/mmdvm/MMDVM-Host.ini' "$ROOT/etc/systemd/system/2pny-nextiondriver.service"
! grep -Fq 'NextionDriver-pu2pny -d ' "$ROOT/etc/systemd/system/2pny-nextiondriver.service"
grep -Fq 'RemotePort","40094"' "$ROOT/usr/local/sbin/2pny-display-apply"
grep -Fq 'LocalPort","40095"' "$ROOT/usr/local/sbin/2pny-display-apply"
grep -Fq 'SendFrameType","1"' "$ROOT/usr/local/sbin/2pny-display-apply"
grep -Fq 'Port","modem"' "$ROOT/usr/local/sbin/2pny-display-apply"
grep -Fq 'RequiredBy=2pny-mmdvmhost.service' "$ROOT/etc/systemd/system/2pny-nextiondriver.service"
grep -Fq 'Regra permanente:' "$ROOT/usr/share/2pny/display.html"
grep -Fq 'timedatectl set-timezone' "$ROOT/usr/local/sbin/2pny-timezone-restore"
test -L "$ROOT/etc/systemd/system/multi-user.target.wants/2pny-timezone-restore.service"
test "$(cat "$ROOT/etc/2pny/version")" = '4.00.001'
echo PATCH_IMAGE_400001_OK
