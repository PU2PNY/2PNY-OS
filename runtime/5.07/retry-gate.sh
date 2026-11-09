#!/bin/sh
# BOOT-057: ExecCondition of 2pny-profile-autostart-retry.service (exit 0 = run, 1 = skip quietly).
# On a single-core Pi Zero the 90 s retry loop competed with the user's own "save" (rf-apply timed out
# at 45 s). The retry now yields while an activation runs or the CPU is busy, and backs off 90 s -> 30 min.
# It never changes configuration. Paths are overridable for tests only.
RUN="${PNY_RUN:-/run/2pny}"
STATE_DIR="${PNY_STATE:-/var/lib/2pny}"
LOADAVG="${PNY_LOADAVG:-/proc/loadavg}"
UPTIME="${PNY_UPTIME:-/proc/uptime}"
CORES="${PNY_CORES:-$(nproc 2>/dev/null || echo 1)}"
PGREP="${PNY_PGREP:-pgrep}"
mkdir -p "$RUN" 2>/dev/null || exit 0
COUNTER="$RUN/retry-gate.state"

# 1) never run next to an activation in progress
if "$PGREP" -f '2pny-(protocol-profiles|protocol-network-apply|rf-apply|dmr-apply|mode-apply|profile-autostart)' >/dev/null 2>&1; then
  exit 1
fi
# 2) never run on a busy CPU (1-minute load above 2 per core)
read -r load1 _ <"$LOADAVG" 2>/dev/null || load1=0
if awk -v l="$load1" -v c="$CORES" 'BEGIN{exit !(l > 2*c)}'; then
  exit 1
fi
# 3) exponential back-off; a newly proven/saved profile resets it
now="$(cut -d. -f1 "$UPTIME" 2>/dev/null || echo 0)"
count=0; last=0
if [ -f "$COUNTER" ]; then
  read -r count last <"$COUNTER" 2>/dev/null || { count=0; last=0; }
  if [ -f "$STATE_DIR/last-active-profile.json" ] && [ "$STATE_DIR/last-active-profile.json" -nt "$COUNTER" ]; then
    count=0; last=0
  fi
fi
wait=90; i=0
while [ "$i" -lt $((count-1)) ] && [ "$wait" -lt 1800 ]; do wait=$((wait*2)); i=$((i+1)); done
[ "$wait" -gt 1800 ] && wait=1800
if [ "$count" -gt 0 ] && [ $((now-last)) -lt "$wait" ]; then
  exit 1
fi
printf '%s %s\n' "$((count+1))" "$now" >"$COUNTER" 2>/dev/null || true
exit 0
