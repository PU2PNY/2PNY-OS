#!/usr/bin/env python3
"""PU2PNY-OS 0.3.26 focused overlay: MMDVM discovery + faster Wi-Fi/failover + reboot feedback."""
from pathlib import Path
import os,re,shutil,subprocess,sys,tempfile

root=Path(sys.argv[1]).resolve()
repo=Path(__file__).resolve().parents[1]
version="0.3.26-alpha"

def install(src,dst,mode=0o644):
    target=root/dst
    target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(repo/src,target)
    os.chmod(target,mode)

for src,dst,mode in [
    ("src/2pnyd-main-0.3.26.go","src/2pnyd/main.go",0o644),
    ("src/2pny-hardware-probe-0.3.26.py","rootfs-overlay/usr/local/sbin/2pny-hardware-probe",0o755),
    ("src/2pny-network-switch-0.3.26","rootfs-overlay/usr/local/sbin/2pny-network-switch",0o755),
    ("src/2pny-wifi-profiles-0.3.26","rootfs-overlay/usr/local/sbin/2pny-wifi-profiles",0o755),
    ("src/90-pu2pny-wifi-choice-0.3.26","rootfs-overlay/etc/NetworkManager/dispatcher.d/90-pu2pny-wifi-choice",0o755),
    ("src/internet-0.3.26.html","rootfs-overlay/usr/share/2pny/internet.html",0o644),
    ("src/system-0.3.26.html","rootfs-overlay/usr/share/2pny/system.html",0o644),
]:
    install(src,dst,mode)

(root/"rootfs-overlay/etc/2pny/version").write_text(version+"\n")

subprocess.run(["gofmt","-w",str(root/"src/2pnyd/main.go")],check=True)
subprocess.run(["go","test",str(root/"src/2pnyd/main.go")],check=True)
subprocess.run(["python3","-m","py_compile",str(root/"rootfs-overlay/usr/local/sbin/2pny-hardware-probe")],check=True)
for sh in (
    root/"rootfs-overlay/usr/local/sbin/2pny-network-switch",
    root/"rootfs-overlay/usr/local/sbin/2pny-wifi-profiles",
    root/"rootfs-overlay/etc/NetworkManager/dispatcher.d/90-pu2pny-wifi-choice",
):
    subprocess.run(["bash","-n",str(sh)],check=True)

for page in ("internet.html","system.html"):
    html=(root/"rootfs-overlay/usr/share/2pny"/page).read_text()
    for body in re.findall(r"<script(?:\s[^>]*)?>(.*?)</script>",html,re.I|re.S):
        if not body.strip(): continue
        with tempfile.NamedTemporaryFile("w",suffix=".js",delete=False) as tf:
            tf.write(body); tmp=tf.name
        try: subprocess.run(["node","--check",tmp],check=True)
        finally: os.unlink(tmp)

main=(root/"src/2pnyd/main.go").read_text()
probe=(root/"rootfs-overlay/usr/local/sbin/2pny-hardware-probe").read_text()
net=(root/"rootfs-overlay/usr/local/sbin/2pny-network-switch").read_text()
profiles=(root/"rootfs-overlay/usr/local/sbin/2pny-wifi-profiles").read_text()
internet=(root/"rootfs-overlay/usr/share/2pny/internet.html").read_text()
system=(root/"rootfs-overlay/usr/share/2pny/system.html").read_text()

assert 'appVersion            = "0.3.26-alpha"' in main
assert 'time.Sleep(120 * time.Millisecond)' in main
assert '/dev/ttyACM*' in probe and '/dev/ttyAMA*' in probe and '500000' in probe
assert 'bytes((0xE0, 0x03, 0x00))' in probe
assert 'nmcli --wait 14 connection up PU2PNY-WIFI-CANDIDATE' in net
assert 'ipv4.dhcp-timeout 12' in net
assert 'connection.autoconnect-priority 200' in profiles
assert 'connection.autoconnect-priority 150' in profiles
assert '12-point hysteresis' in profiles
assert 'id="wifiSearchSecond"' in internet
assert "PNY.q('wifiSearchSecond').onclick=wifiScan" in internet
assert "PNY.operation(rt,rt)" in system

# Explicit non-goals: this overlay does not install any protocol/RF/Direct/clock helper.
installed=[x[1] for x in [
    ("src/2pnyd-main-0.3.26.go","src/2pnyd/main.go",0o644),
    ("src/2pny-hardware-probe-0.3.26.py","rootfs-overlay/usr/local/sbin/2pny-hardware-probe",0o755),
    ("src/2pny-network-switch-0.3.26","rootfs-overlay/usr/local/sbin/2pny-network-switch",0o755),
    ("src/2pny-wifi-profiles-0.3.26","rootfs-overlay/usr/local/sbin/2pny-wifi-profiles",0o755),
    ("src/90-pu2pny-wifi-choice-0.3.26","rootfs-overlay/etc/NetworkManager/dispatcher.d/90-pu2pny-wifi-choice",0o755),
    ("src/internet-0.3.26.html","rootfs-overlay/usr/share/2pny/internet.html",0o644),
    ("src/system-0.3.26.html","rootfs-overlay/usr/share/2pny/system.html",0o644),
]]
for forbidden in ("DMRGateway","YSFGateway","DStarGateway","MMDVMHost","direct-core","2pny-timezone","display"):
    assert not any(forbidden.lower() in p.lower() for p in installed), forbidden

print("PREPARE_0326_OK")
