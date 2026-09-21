#!/usr/bin/env python3
"""Apply PU2PNY-OS 0.3.11-alpha hardware/i18n regression fixes after 0.3.10."""
from pathlib import Path
import os,re,shutil,subprocess,sys,tempfile

root=Path(sys.argv[1]).resolve()
repo=Path(__file__).resolve().parents[1]
version="0.3.11-alpha"

def install(src,dst,mode=0o644):
    target=root/dst
    target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(repo/src,target)
    os.chmod(target,mode)

install("src/2pnyd-main-0.3.11.go","src/2pnyd/main.go")
install("src/wizard-0.3.11.html","rootfs-overlay/usr/share/2pny/wizard.html")
install("src/ui-language-0.3.11.js","rootfs-overlay/usr/share/2pny/ui-language.js")
install("src/2pny-rf-apply-0.3.11","rootfs-overlay/usr/local/sbin/2pny-rf-apply",0o755)
install("src/2pny-hardware-probe-0.3.11.py","rootfs-overlay/usr/local/sbin/2pny-hardware-probe",0o755)
(root/"rootfs-overlay/etc/2pny/version").write_text(version+"\n")

subprocess.run(["gofmt","-w",str(root/"src/2pnyd/main.go")],check=True)
subprocess.run(["go","test",str(root/"src/2pnyd/main.go")],check=True)
subprocess.run(["bash","-n",str(root/"rootfs-overlay/usr/local/sbin/2pny-rf-apply")],check=True)
subprocess.run(["python3","-m","py_compile",str(root/"rootfs-overlay/usr/local/sbin/2pny-hardware-probe")],check=True)
subprocess.run(["node","--check",str(root/"rootfs-overlay/usr/share/2pny/ui-language.js")],check=True)
cache=root/"rootfs-overlay/usr/local/sbin/__pycache__"
if cache.exists():shutil.rmtree(cache)

wiz=(root/"rootfs-overlay/usr/share/2pny/wizard.html").read_text()
for body in re.findall(r"<script(?:\s[^>]*)?>(.*?)</script>",wiz,re.I|re.S):
    if not body.strip():continue
    with tempfile.NamedTemporaryFile("w",suffix=".js",delete=False) as tf:
        tf.write(body);name=tf.name
    try:subprocess.run(["node","--check",name],check=True)
    finally:os.unlink(name)

main=(root/"src/2pnyd/main.go").read_text()
rf=(root/"rootfs-overlay/usr/local/sbin/2pny-rf-apply").read_text()
probe=(root/"rootfs-overlay/usr/local/sbin/2pny-hardware-probe").read_text()
lang=(root/"rootfs-overlay/usr/share/2pny/ui-language.js").read_text()
assert '"0.3.11-alpha"' in main
assert 'flock -w 8 8' in rf
assert '2pny-mqtt-preflight --quiet' in rf
assert 'MMDVMHost failed with detected baud' not in rf
assert 'MMDVMHost não iniciou; a configuração anterior foi restaurada' in rf
assert 'bridge = probe_nextion_mmdvm' not in probe
assert 'MMDVM confirmada. A Nextion pela porta do modem' in probe
assert 'scheduleHardwareAdvance' in wiz
assert 'O assistente avançará automaticamente em 5 segundos' in wiz
assert "q('hardwareResult').className='result success'" in wiz
assert 'normalizeIncoming' in lang and 'incomingPT' in lang
assert 'MMDVMHost failed with detected baud' in lang
print("PREPARE_0311_OK")
