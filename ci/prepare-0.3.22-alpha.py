#!/usr/bin/env python3
"""Apply the focused PU2PNY-OS 0.3.21-alpha corrective overlay.

0.3.20 is the protected HW-tested base. Only reported failures/new rules from
the 2026-09-22 test are installed here. DMR and D-Star simplex behavior must
remain inherited unless a change is explicitly guarded to duplex/runtime/UI.
"""
from pathlib import Path
import os,re,shutil,subprocess,sys,tempfile

root=Path(sys.argv[1]).resolve()
repo=Path(__file__).resolve().parents[1]
version="0.3.22-alpha"

def install(src,dst,mode=0o644):
    target=root/dst
    target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(repo/src,target)
    os.chmod(target,mode)

files=[
("src/2pnyd-main-0.3.22.go","src/2pnyd/main.go",0o644),
("src/ui-common-0.3.21.js","rootfs-overlay/usr/share/2pny/ui-common-0.3.0.js",0o644),
("src/ui-language-0.3.21.js","rootfs-overlay/usr/share/2pny/ui-language.js",0o644),
("src/dashboard-0.3.21.html","rootfs-overlay/usr/share/2pny/dashboard.html",0o644),
("src/hotspot-0.3.21.html","rootfs-overlay/usr/share/2pny/hotspot.html",0o644),
("src/internet-0.3.21.html","rootfs-overlay/usr/share/2pny/internet.html",0o644),
("src/wizard-0.3.21.html","rootfs-overlay/usr/share/2pny/wizard.html",0o644),
("src/system-0.3.21.html","rootfs-overlay/usr/share/2pny/system.html",0o644),
("src/display-0.3.21.html","rootfs-overlay/usr/share/2pny/display.html",0o644),
("src/aprs-0.3.21.html","rootfs-overlay/usr/share/2pny/aprs.html",0o644),
("src/direct-0.3.21.html","rootfs-overlay/usr/share/2pny/direct.html",0o644),
("src/2pny-protocol-network-apply-0.3.21.py","rootfs-overlay/usr/local/libexec/2pny-dmr-apply",0o755),
("src/2pny-station-worker-0.3.21.py","rootfs-overlay/usr/local/sbin/2pny-station-worker",0o755),
("src/2pny-aprs-0.3.21.py","rootfs-overlay/usr/local/sbin/2pny-aprs",0o755),
("src/2pny-display-apply-0.3.21.py","rootfs-overlay/usr/local/sbin/2pny-display-apply",0o755),
("src/2pny-display-core-0.3.21.py","rootfs-overlay/usr/local/sbin/2pny-display-core",0o755),
("src/2pny-display-detector-0.3.20.py","rootfs-overlay/usr/local/sbin/2pny-display-detector",0o755),
("src/2pny-dmr-duplex-diagnostics-0.3.21.py","rootfs-overlay/usr/local/sbin/2pny-dmr-duplex-diagnostics",0o755),
("src/2pny-wifi-profiles-0.3.21","rootfs-overlay/usr/local/sbin/2pny-wifi-profiles",0o755),
("src/90-pu2pny-wifi-choice-0.3.21","rootfs-overlay/etc/NetworkManager/dispatcher.d/90-pu2pny-wifi-choice",0o755),
("src/20-pu2pny-journald-0.3.21.conf","rootfs-overlay/etc/systemd/journald.conf.d/20-pu2pny.conf",0o644),
("src/2pny-rxoffset-apply-0.3.21.py","rootfs-overlay/usr/local/sbin/2pny-rxoffset-apply",0o755),
("src/2pny-rxoffset-apply-0.3.21.service","rootfs-overlay/etc/systemd/system/2pny-rxoffset-apply.service",0o644),
("src/2pny-rxoffset-apply-0.3.21.path","rootfs-overlay/etc/systemd/system/2pny-rxoffset-apply.path",0o644),
]
for src,dst,mode in files: install(src,dst,mode)

# Replace only the inherited 0.3.16 voice-arbitration patch with the 0.3.21
# SENDING-only gate. Other DMRGateway patches remain untouched.
install("ci/patch-dmrgateway-voice-arbiter-0.3.21.py",
        "rootfs-overlay/builder/patch-dmrgateway-voice-arbiter-0.3.21.py",0o755)
builder=root/"builder/build-image.sh"
bs=builder.read_text()
old_stage='cp "$ROOT_DIR/rootfs-overlay/builder/patch-dmrgateway-voice-arbiter-0.3.16.py" "$ROOT_MNT/builder/"'
new_stage='cp "$ROOT_DIR/rootfs-overlay/builder/patch-dmrgateway-voice-arbiter-0.3.21.py" "$ROOT_MNT/builder/"'
old_apply='python3 /builder/patch-dmrgateway-voice-arbiter-0.3.16.py "$DG"'
new_apply='python3 /builder/patch-dmrgateway-voice-arbiter-0.3.21.py "$DG"'
if old_stage in bs: bs=bs.replace(old_stage,new_stage,1)
elif new_stage not in bs: raise SystemExit("0.3.21 builder: voice patch staging anchor missing")
if old_apply in bs: bs=bs.replace(old_apply,new_apply,1)
elif new_apply not in bs: raise SystemExit("0.3.21 builder: voice patch apply anchor missing")
builder.write_text(bs);os.chmod(builder,0o755)

# Direct 0.3.21: rendezvous may assist discovery, but the QSO transport itself
# is direct-only. Build the exact reviewed source set for ARM64.
direct=root/"src/direct-core";direct.mkdir(parents=True,exist_ok=True)
direct_src=repo/"src/direct-core-0.3.21"
direct_names=("direct_types.go","direct_session.go","direct_transport.go","direct_radio.go","direct_autocall.go","direct_main.go")
for name in direct_names: shutil.copy2(direct_src/name,direct/name)
subprocess.run(["gofmt","-w",*(str(direct/n) for n in direct_names)],check=True)
subprocess.run(["go","test",*(str(direct/n) for n in direct_names)],check=True)
target=root/"rootfs-overlay/usr/local/bin/2pny-direct-core";target.parent.mkdir(parents=True,exist_ok=True)
env=os.environ.copy();env.update({"GOOS":"linux","GOARCH":"arm64","CGO_ENABLED":"0"})
subprocess.run(["go","build","-trimpath","-o",str(target),*(str(direct/n) for n in direct_names)],check=True,env=env)
os.chmod(target,0o755)

# Enable one-shot privileged RXOffset helper; it remains idle until a request.
wants=root/"rootfs-overlay/etc/systemd/system/multi-user.target.wants";wants.mkdir(parents=True,exist_ok=True)
link=wants/"2pny-rxoffset-apply.path"
if link.exists() or link.is_symlink(): link.unlink()
link.symlink_to("../2pny-rxoffset-apply.path")

# Keep browser title canonical after all page overlays.
for page in (root/"rootfs-overlay/usr/share/2pny").glob("*.html"):
    html=page.read_text()
    if "<head" not in html.lower(): continue
    normalized,count=re.subn(r"(?is)<title>.*?</title>","<title>PU2PNY-OS</title>",html,count=1)
    if count==0: normalized=re.sub(r"(?is)(<head[^>]*>)",r"\1<title>PU2PNY-OS</title>",normalized,count=1)
    page.write_text(normalized)

(root/"rootfs-overlay/etc/2pny/version").write_text(version+"\n")

# Cheap gates before the expensive image build.
subprocess.run(["gofmt","-w",str(root/"src/2pnyd/main.go")],check=True)
subprocess.run(["go","test",str(root/"src/2pnyd/main.go")],check=True)
for p in (
 root/"rootfs-overlay/usr/local/sbin/2pny-station-worker",
 root/"rootfs-overlay/usr/local/sbin/2pny-aprs",
 root/"rootfs-overlay/usr/local/sbin/2pny-display-apply",
 root/"rootfs-overlay/usr/local/sbin/2pny-display-core",
 root/"rootfs-overlay/usr/local/sbin/2pny-dmr-duplex-diagnostics",
 root/"rootfs-overlay/usr/local/sbin/2pny-rxoffset-apply",
 root/"rootfs-overlay/usr/local/libexec/2pny-dmr-apply",
):
    subprocess.run(["python3","-m","py_compile",str(p)],check=True)
subprocess.run(["bash","-n",str(root/"rootfs-overlay/usr/local/sbin/2pny-wifi-profiles")],check=True)
subprocess.run(["bash","-n",str(root/"rootfs-overlay/etc/NetworkManager/dispatcher.d/90-pu2pny-wifi-choice")],check=True)
for cache in root.rglob("__pycache__"): shutil.rmtree(cache,ignore_errors=True)
for js in ("ui-common-0.3.0.js","ui-language.js"):
    subprocess.run(["node","--check",str(root/"rootfs-overlay/usr/share/2pny"/js)],check=True)
for page in ("dashboard.html","hotspot.html","internet.html","wizard.html","system.html","display.html","aprs.html","direct.html"):
    html=(root/"rootfs-overlay/usr/share/2pny"/page).read_text()
    for body in re.findall(r"<script(?:\s[^>]*)?>(.*?)</script>",html,re.I|re.S):
        if not body.strip(): continue
        with tempfile.NamedTemporaryFile("w",suffix=".js",delete=False) as tf:
            tf.write(body);tmp=tf.name
        try: subprocess.run(["node","--check",tmp],check=True)
        finally: os.unlink(tmp)

print("PREPARE_0321_OK")

# CI: release candidate for physical testing.
