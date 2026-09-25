#!/usr/bin/env python3
"""Apply only the PU2PNY-OS 0.3.24 corrective overlay over staged 0.3.23."""
from pathlib import Path
import os,re,shutil,subprocess,sys,tempfile

root=Path(sys.argv[1]).resolve()
repo=Path(__file__).resolve().parents[1]
version="0.3.24-alpha"

def install(src,dst,mode=0o644):
    target=root/dst
    target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(repo/src,target)
    os.chmod(target,mode)

# No RF/MMDVM/DMR/D-Star/YSF source is replaced here.
for src,dst,mode in [
 ("src/2pnyd-main-0.3.24.go","src/2pnyd/main.go",0o644),
 ("src/ui-common-0.3.24.js","rootfs-overlay/usr/share/2pny/ui-common-0.3.0.js",0o644),
 ("src/ui-language-0.3.24.js","rootfs-overlay/usr/share/2pny/ui-language.js",0o644),
 ("src/system-0.3.24.html","rootfs-overlay/usr/share/2pny/system.html",0o644),
 ("src/direct-0.3.24.html","rootfs-overlay/usr/share/2pny/direct.html",0o644),
]:
    install(src,dst,mode)

direct=root/"src/direct-core"
direct.mkdir(parents=True,exist_ok=True)
names=("direct_types.go","direct_session.go","direct_transport.go","direct_radio.go","direct_autocall.go","direct_main.go")
for name in names:
    shutil.copy2(repo/"src/direct-core-0.3.24"/name,direct/name)
subprocess.run(["gofmt","-w",*(str(direct/n) for n in names)],check=True)
subprocess.run(["go","test",*(str(direct/n) for n in names)],check=True)
target=root/"rootfs-overlay/usr/local/bin/2pny-direct-core"
env=os.environ.copy();env.update({"GOOS":"linux","GOARCH":"arm64","CGO_ENABLED":"0"})
subprocess.run(["go","build","-trimpath","-o",str(target),*(str(direct/n) for n in names)],check=True,env=env)
os.chmod(target,0o755)

(root/"rootfs-overlay/etc/2pny/version").write_text(version+"\n")
subprocess.run(["gofmt","-w",str(root/"src/2pnyd/main.go")],check=True)
subprocess.run(["go","test",str(root/"src/2pnyd/main.go")],check=True)
for js in ("ui-common-0.3.0.js","ui-language.js"):
    subprocess.run(["node","--check",str(root/"rootfs-overlay/usr/share/2pny"/js)],check=True)
for page in ("system.html","direct.html"):
    html=(root/"rootfs-overlay/usr/share/2pny"/page).read_text()
    for body in re.findall(r"<script(?:\s[^>]*)?>(.*?)</script>",html,re.I|re.S):
        if not body.strip():continue
        with tempfile.NamedTemporaryFile("w",suffix=".js",delete=False) as tf:
            tf.write(body);tmp=tf.name
        try:subprocess.run(["node","--check",tmp],check=True)
        finally:os.unlink(tmp)

assert "seleção manual de fuso foi desativada" not in (root/"src/2pnyd/main.go").read_text()
assert "ajuste manual do relógio foi desativado" not in (root/"src/2pnyd/main.go").read_text()
assert "Direct primeiro · Relay automático" in (root/"rootfs-overlay/usr/share/2pny/direct.html").read_text()
assert "Aplicar fuso manual" in (root/"rootfs-overlay/usr/share/2pny/system.html").read_text()
print("PREPARE_0324_OK")
