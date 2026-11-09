#!/bin/bash
# CLOCK-058: restore the persisted IANA zone at boot by the /etc/localtime link (the zone libc uses).
# `timedatectl show` reads /etc/timezone and could report a zone that /etc/localtime did not follow.
set -euo pipefail
STATE=/var/lib/2pny/settings/clock.json
ZONEINFO=/usr/share/zoneinfo
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
[[ "$TZ_NAME" =~ ^[A-Za-z0-9_+./-]+$ ]] || exit 2
[[ -f "$ZONEINFO/$TZ_NAME" ]] || exit 2
CURRENT="$(readlink -f /etc/localtime 2>/dev/null || true)"
if [[ "$CURRENT" != "$(readlink -f "$ZONEINFO/$TZ_NAME")" ]]; then
    ln -snf "$ZONEINFO/$TZ_NAME" /etc/.localtime.pu2pny
    mv -Tf /etc/.localtime.pu2pny /etc/localtime
    printf '%s\n' "$TZ_NAME" > /etc/timezone
fi
exit 0
