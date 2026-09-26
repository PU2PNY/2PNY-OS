#!/usr/bin/env python3
from pathlib import Path
import sys
root=Path(sys.argv[1]).resolve()
p=root/"rootfs-overlay/usr/local/sbin/2pny-hostfiles-update"
s=p.read_text()
anchor='mkdir -p "$BASE" "$RUN"\n'
insert='mkdir -p "$BASE" "$RUN"\nexec 9>"$RUN/hostfiles-update.lock"\nflock -n 9 || { echo "HOSTFILES_ALREADY_RUNNING"; exit 0; }\n'
if insert not in s:
    if anchor not in s: raise SystemExit("0.3.28 hostfiles lock anchor missing")
    s=s.replace(anchor,insert,1)
p.write_text(s)
print("HOSTFILES_LOCK_0328_OK")
