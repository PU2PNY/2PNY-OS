#!/usr/bin/env bash
set -euo pipefail
ARCH="${1:?architecture}"
BASE_SHA="${2:?checksum}"
tmp="$(mktemp -d)"; loop=""
finish() { set +e; mountpoint -q "$tmp/root" && sudo umount "$tmp/root"; [[ -n "$loop" ]] && sudo losetup -d "$loop"; rm -rf "$tmp"; }
trap finish EXIT
curl -fL --retry 3 "https://github.com/PU2PNY/2PNY-OS/releases/download/v5.00.004/PU2PNY-OS-5.00.004-$ARCH.img.xz" -o "$tmp/base.img.xz"
printf '%s  %s\n' "$BASE_SHA" "$tmp/base.img.xz" | sha256sum -c -
xz -dc "$tmp/base.img.xz" > "$tmp/base.img"
mkdir "$tmp/root"
loop="$(sudo losetup --find --show --partscan "$tmp/base.img")"
sudo mount -o ro "${loop}p2" "$tmp/root"
python3 - "$tmp/root" <<'PY'
import pathlib,sys,re,configparser
root=pathlib.Path(sys.argv[1])
for p in sorted((root/'etc/NetworkManager/system-connections').glob('*')):
    if not p.is_file(): continue
    cp=configparser.ConfigParser(interpolation=None);cp.read(p)
    print("NM",p.name,"id",cp.get('connection','id',fallback='?'),"mode",cp.get('wifi','mode',fallback=cp.get('802-11-wireless','mode',fallback='?')),"ssid",cp.get('wifi','ssid',fallback=cp.get('802-11-wireless','ssid',fallback='?')),"ipv4",cp.get('ipv4','method',fallback='?'))
for dirname in ('usr/local/sbin','usr/local/bin','etc/systemd/system','etc/NetworkManager'):
    for p in (root/dirname).rglob('*'):
        if not p.is_file() or p.stat().st_size>200000: continue
        try: s=p.read_text()
        except (UnicodeError,OSError):continue
        hits=[]
        for line in s.splitlines():
            if re.search('PU2PNY-OS|pu2pny-os|ssid',line,re.I):
                if re.search('password|passwd|psk|secret|token|key',line,re.I):continue
                if re.search('PU2PNY-OS|pu2pny-os',line,re.I):hits.append(line[:135])
        if hits: print("SOURCE",str(p.relative_to(root)),len(hits)," | ".join(hits[:2]))
print("DISPLAY_FILES")
for p in ('usr/local/libexec/pu2pny/display/adapter.py','usr/local/sbin/2pny-display-apply','usr/share/2pny/display.html'):
    f=root/p; print(p, f.is_file(),f.stat().st_size if f.exists() else 0)
PY
