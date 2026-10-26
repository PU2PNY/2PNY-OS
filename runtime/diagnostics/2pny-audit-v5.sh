#!/usr/bin/env bash
set -euo pipefail
export LC_ALL=C
# PU2PNY-OS diagnostic: deliberately read-only, no passwords, no RF restarts.
# Does not open UART, change Wi-Fi, access credentials or capture packet payload.
section() { printf '\n[%s] %s\n' "$1" "$2"; }
safe() { timeout 4s "$@" 2>/dev/null || true; }
printf 'PU2PNY-OS v5.00 — diagnostic snapshot (NOT an RF validation)\n'
printf 'utc='; date -u '+%Y-%m-%dT%H:%M:%SZ'
printf 'uptime_seconds='; cut -d ' ' -f1 /proc/uptime 2>/dev/null || printf '%s\n' unavailable
printf 'load='; cut -d ' ' -f1-3 /proc/loadavg 2>/dev/null || printf '%s\n' unavailable
section 1 'Modem serial (metadata only, never opened)'
for p in /dev/serial0 /dev/ttyAMA0 /dev/ttyS0; do
  if [[ -e "$p" ]]; then
    printf '%s => ' "$p"
    safe readlink -f "$p"
  else
    printf '%s => unavailable\n' "$p"
  fi
done
section 2 'Serial owners (PIDs only; no command lines)'
if command -v fuser >/dev/null 2>&1; then
  for p in /dev/serial0 /dev/ttyAMA0; do
    if [[ -e "$p" ]]; then
      printf '%s pid(s): ' "$p"
      safe fuser "$p"
      printf '\n'
    fi
  done
fi
section 3 'Known systemd services: active state, restarts and start timestamp'
if command -v systemctl >/dev/null 2>&1; then
  for unit in 2pny-mmdvmhost.service mmdvmhost.service 2pny-dmrgateway.service dmrgateway.service 2pny-ysfgateway.service ysfgateway.service 2pny-nextiondriver.service nextiondriver.service mmdvm-display.service 2pny-display-reconcile.service 2pny-profile-autostart.service; do
    value="$(safe systemctl show "$unit" -p LoadState -p ActiveState -p SubState -p NRestarts -p ActiveEnterTimestamp --no-pager)"
    if [[ "$value" != *'LoadState=not-found'* && -n "$value" ]]; then
      printf 'UNIT=%s\n%s\n' "$unit" "$value"
    fi
  done
fi
section 4 'Interfaces (link status only; no SSID, IP or secrets)'
if command -v ip >/dev/null 2>&1; then
  safe ip -brief link | awk '{print $1, $2}' | head -n 12
fi
section 5 'Recent system log error counts (NO raw log lines)'
if command -v journalctl >/dev/null 2>&1; then
  for unit in 2pny-mmdvmhost.service 2pny-nextiondriver.service nextiondriver.service; do
    count="$(safe journalctl --no-pager -q -u "$unit" --since '-10 minutes' -p err -o cat | wc -l)"
    printf '%s recent_error_lines=%s\n' "$unit" "${count:-0}"
  done
fi
section 6 'Interpretation'
printf 'A running process does not prove working RF or display. Compare healthy/fault snapshots.\n'
printf 'No configuration changes were made. Do not include credentials in support reports.\n'
