#!/usr/bin/env python3
"""PU2PNY-OS 0.3.28 focal recovery overlay.

Restores proven network association windows, adds event-driven discovery/list
refresh/profile recovery and Live status without modifying protected RF/gateway
helpers.
"""
from pathlib import Path
import os,re,shutil,subprocess,sys,tempfile

root=Path(sys.argv[1]).resolve()
repo=Path(__file__).resolve().parents[1]
version="0.3.28-alpha"

def install(src,dst,mode=0o644):
    target=root/dst
    target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(repo/src,target)
    os.chmod(target,mode)

for src,dst,mode in [
    ("src/wizard-0.3.28.html","rootfs-overlay/usr/share/2pny/wizard.html",0o644),
    ("src/internet-0.3.28.html","rootfs-overlay/usr/share/2pny/internet.html",0o644),
    ("src/dashboard-0.3.28.html","rootfs-overlay/usr/share/2pny/dashboard.html",0o644),
    ("src/2pny-network-online-0.3.28","rootfs-overlay/usr/local/sbin/2pny-network-online",0o755),
    ("src/2pny-network-online-0.3.28.service","rootfs-overlay/etc/systemd/system/2pny-network-online.service",0o644),
    ("src/2pny-hostfiles-update-0.3.28.service","rootfs-overlay/etc/systemd/system/2pny-hostfiles-update.service",0o644),
    ("src/2pny-hostfiles-update-0.3.28.timer","rootfs-overlay/etc/systemd/system/2pny-hostfiles-update.timer",0o644),
    ("src/2pny-profile-autostart-0.3.28.py","rootfs-overlay/usr/local/sbin/2pny-profile-autostart",0o755),
    ("src/2pny-profile-autostart-0.3.28.service","rootfs-overlay/etc/systemd/system/2pny-profile-autostart.service",0o644),
    ("src/91-pu2pny-online-actions-0.3.28","rootfs-overlay/etc/NetworkManager/dispatcher.d/91-pu2pny-online-actions",0o755),
]:
    install(src,dst,mode)

# Keep the 0.3.27 backend behavior, changing only release identity.
main=root/"src/2pnyd/main.go"
s=main.read_text()
old='appVersion            = "0.3.27-alpha"'
if old not in s:
    raise SystemExit("0.3.28 backend version anchor missing")
main.write_text(s.replace(old,'appVersion            = "0.3.28-alpha"',1))
(root/"rootfs-overlay/etc/2pny/version").write_text(version+"\n")

# Restore connection reliability without undoing Wi-Fi 2 or fast scan/UI work.
subprocess.run(["python3",str(repo/"ci/patch-network-reliability-0.3.28.py"),str(root)],check=True)
subprocess.run(["python3",str(repo/"ci/patch-hostfiles-lock-0.3.28.py"),str(root)],check=True)
subprocess.run(["python3",str(repo/"ci/patch-i18n-0.3.28.py"),str(root)],check=True)

def enable(unit,target):
    d=root/f"rootfs-overlay/etc/systemd/system/{target}.wants"
    d.mkdir(parents=True,exist_ok=True)
    link=d/unit
    if link.exists() or link.is_symlink():
        link.unlink()
    link.symlink_to("../"+unit)

enable("2pny-network-online.service","multi-user.target")
enable("2pny-hostfiles-update.timer","timers.target")

# Protected protocol runtime must remain exactly the approved sources.
pairs=[
 ("rootfs-overlay/usr/local/sbin/2pny-protocol-network-apply","src/2pny-protocol-network-apply-all-0.3.20.py"),
 ("rootfs-overlay/usr/local/libexec/2pny-dmr-apply","src/2pny-protocol-network-apply-0.3.21.py"),
]
for staged,source in pairs:
    if (root/staged).read_bytes()!=(repo/source).read_bytes():
        raise SystemExit("0.3.28 protected protocol helper changed: "+staged)

subprocess.run(["gofmt","-w",str(main)],check=True)
subprocess.run(["go","test",str(main)],check=True)
subprocess.run(["python3","-m","py_compile",
                str(root/"rootfs-overlay/usr/local/sbin/2pny-profile-autostart"),
                str(root/"rootfs-overlay/usr/local/sbin/2pny-aprs")],check=True)
subprocess.run(["bash","-n",
                str(root/"rootfs-overlay/usr/local/sbin/2pny-network-online"),
                str(root/"rootfs-overlay/etc/NetworkManager/dispatcher.d/91-pu2pny-online-actions"),
                str(root/"rootfs-overlay/usr/local/sbin/2pny-network-switch"),
                str(root/"rootfs-overlay/usr/local/sbin/2pny-wifi-profiles"),
                str(root/"rootfs-overlay/usr/local/sbin/2pny-hostfiles-update")],check=True)
subprocess.run(["node","--check",str(root/"rootfs-overlay/usr/share/2pny/ui-language.js")],check=True)

for page in ("wizard.html","internet.html","dashboard.html","hotspot.html","aprs.html"):
    html=(root/"rootfs-overlay/usr/share/2pny"/page).read_text()
    for body in re.findall(r"<script(?:\s[^>]*)?>(.*?)</script>",html,re.I|re.S):
        if not body.strip(): continue
        with tempfile.NamedTemporaryFile("w",suffix=".js",delete=False) as tf:
            tf.write(body); tmp=tf.name
        try: subprocess.run(["node","--check",tmp],check=True)
        finally: os.unlink(tmp)

n=(root/"rootfs-overlay/usr/local/sbin/2pny-network-switch").read_text()
w=(root/"rootfs-overlay/usr/local/sbin/2pny-wifi-profiles").read_text()
assert "nmcli --wait 45 connection up PU2PNY-WIFI-CANDIDATE" in n
assert "ipv4.dhcp-timeout 30" in n
assert "connection.autoconnect-priority 200 connection.autoconnect-retries 3" in n
assert 'nm --wait 18 connection up "$chosen"' in w
assert 'nm --wait 22 connection up "$SECONDARY"' in w
assert "connection.autoconnect-priority 150 connection.autoconnect-retries 3" in w
assert "appVersion            = \"0.3.28-alpha\"" in main.read_text()
print("PREPARE_0328_OK")
