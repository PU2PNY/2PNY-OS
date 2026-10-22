#!/usr/bin/env bash
set -euo pipefail
ARCH="${1:-}"
SHA="${2:-}"
[[ "$ARCH" == arm32 || "$ARCH" == arm64 ]] || exit 2
[[ "$SHA" =~ ^[0-9a-f]{64}$ ]] || exit 2
WORK="$(mktemp -d "${RUNNER_TEMP:-/tmp}/pu2pny-display-audit.XXXXXX")"
LOOP=''
MNT=''
cleanup(){
  set +e
  [[ -n "$MNT" ]] && sudo umount "$MNT" >/dev/null 2>&1 || true
  [[ -n "$LOOP" ]] && sudo losetup -d "$LOOP" >/dev/null 2>&1 || true
  rm -rf "$WORK"
}
trap cleanup EXIT
FILE="PU2PNY-OS-5.00.000-$ARCH.img.xz"
URL="https://github.com/PU2PNY/2PNY-OS/releases/download/v5.00.000/$FILE"
curl --fail --location --retry 3 "$URL" -o "$WORK/$FILE"
printf '%s  %s\n' "$SHA" "$WORK/$FILE" | sha256sum -c -
xz -t "$WORK/$FILE"
xz -dc "$WORK/$FILE" > "$WORK/pu2pny.img"
LOOP="$(sudo losetup --find --show --partscan "$WORK/pu2pny.img")"
MNT="$WORK/root"; mkdir -p "$MNT"
sudo mount -o ro "${LOOP}p2" "$MNT"
printf 'AUDIT_RELEASE=v5.00.000\nAUDIT_ARCH=%s\nAUDIT_SHA=%s\n' "$ARCH" "$SHA"
printf '\n-- DISPLAY BINARIES --\n'
for p in usr/local/bin/MMDVM-Display usr/local/bin/MMDVM-Host usr/local/bin/NextionDriver-pu2pny usr/local/bin/NextionDriver usr/local/sbin/2pny-display-apply usr/local/sbin/2pny-display-config usr/local/sbin/2pny-display-detector; do
  if sudo test -x "$MNT/$p"; then
    printf 'PRESENT %s\n' "$p"
    [[ "$p" == usr/local/bin/* ]] && sudo file "$MNT/$p"
  else printf 'MISSING %s\n' "$p"; fi
done
printf '\n-- DISPLAY SERVICES --\n'
for unit in 2pny-display.service 2pny-display-core.service 2pny-nextiondriver.service mmdvm-display.service 2pny-display-apply-request.service 2pny-mmdvmhost.service; do
  for folder in etc/systemd/system lib/systemd/system usr/lib/systemd/system; do
    if sudo test -e "$MNT/$folder/$unit"; then
      printf 'PRESENT %s/%s\n' "$folder" "$unit"
      sudo grep -E '^(Type|ExecStart|Requires|Wants|After|User|Group|Restart)=' "$MNT/$folder/$unit" || true
    fi
  done
done
printf '\n-- CONFIG / PANEL CONTRACT --\n'
for p in etc/MMDVMHost.ini var/lib/2pny/mmdvm/MMDVM-Host.ini var/lib/2pny/display/MMDVM-Display.ini usr/share/2pny/display.html usr/share/2pny/dashboard.html etc/2pny/version; do
  if sudo test -f "$MNT/$p"; then
    printf 'PRESENT %s\n' "$p"
    if [[ "$p" == *.ini ]]; then
      # Never print passwords or secrets; inspect only section names and safe parameter keys.
      sudo grep -E '^\[(General|Nextion|OLED|HD44780|LCDproc|MQTT|Transparent Data)\]' "$MNT/$p" || true
    fi
  else printf 'MISSING %s\n' "$p"; fi
done
printf '\n-- DISPLAY HELPERS AND EXECUTABLE DEPENDENCIES --\n'
for path in "$MNT/usr/local/bin/MMDVM-Display" "$MNT/usr/local/bin/NextionDriver-pu2pny"; do
  [[ -f "$path" ]] && sudo readelf -d "$path" 2>/dev/null | grep NEEDED || true
done
printf '\nAUDIT_COMPLETE_READ_ONLY\n'
