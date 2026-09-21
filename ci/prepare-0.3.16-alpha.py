#!/usr/bin/env python3
"""Apply PU2PNY-OS 0.3.16-alpha bugfix-only overlay after 0.3.15.

Everything outside the HW-reported bug list remains inherited and frozen.
"""
from pathlib import Path
import os,re,shutil,subprocess,sys,tempfile

root=Path(sys.argv[1]).resolve()
repo=Path(__file__).resolve().parents[1]
version="0.3.16-alpha"

def install(src,dst,mode=0o644):
    target=root/dst
    target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(repo/src,target)
    os.chmod(target,mode)

# Web/backend: only reported regressions.
for src,dst in (
    ("src/2pnyd-main-0.3.16.go","src/2pnyd/main.go"),
    ("src/dashboard-0.3.16.html","rootfs-overlay/usr/share/2pny/dashboard.html"),
    ("src/internet-0.3.16.html","rootfs-overlay/usr/share/2pny/internet.html"),
    ("src/hotspot-0.3.16.html","rootfs-overlay/usr/share/2pny/hotspot.html"),
    ("src/aprs-0.3.16.html","rootfs-overlay/usr/share/2pny/aprs.html"),
    ("src/display-0.3.16.html","rootfs-overlay/usr/share/2pny/display.html"),
    ("src/expert-0.3.16.html","rootfs-overlay/usr/share/2pny/expert.html"),
):
    install(src,dst)

# Runtime helpers.
for src,dst in (
    ("src/2pny-network-switch-0.3.16","rootfs-overlay/usr/local/sbin/2pny-network-switch"),
    ("src/2pny-network-core-0.3.16","rootfs-overlay/usr/local/sbin/2pny-network-core"),
    ("src/2pny-live-core-0.3.16.py","rootfs-overlay/usr/local/lib/2pny-live-core.py"),
    ("src/2pny-aprs-0.3.16.py","rootfs-overlay/usr/local/sbin/2pny-aprs"),
    ("src/2pny-display-apply-0.3.16.py","rootfs-overlay/usr/local/sbin/2pny-display-apply"),
    ("src/2pny-protocol-network-apply-all-0.3.16.py","rootfs-overlay/usr/local/sbin/2pny-protocol-network-apply"),
    ("src/2pny-timezone-apply-0.3.16.py","rootfs-overlay/usr/local/sbin/2pny-timezone-apply"),
    ("src/2pny-ssh-apply-0.3.16.py","rootfs-overlay/usr/local/sbin/2pny-ssh-apply"),
):
    install(src,dst,0o755)

for src,dst in (
    ("src/2pny-timezone-apply-0.3.16.path","rootfs-overlay/etc/systemd/system/2pny-timezone-apply.path"),
    ("src/2pny-ssh-apply-0.3.16.path","rootfs-overlay/etc/systemd/system/2pny-ssh-apply.path"),
):
    install(src,dst)

# Updated Direct source, rebuilt without changing the wire protocol/identity model.
direct_dir=root/"src/direct-core"
direct_dir.mkdir(parents=True,exist_ok=True)
for name in ("direct_types.go","direct_session.go","direct_transport.go","direct_radio.go","direct_main.go"):
    shutil.copy2(repo/"src/direct-core"/name,direct_dir/name)
subprocess.run(["gofmt","-w",*(str(direct_dir/n) for n in ("direct_types.go","direct_session.go","direct_transport.go","direct_radio.go","direct_main.go"))],check=True)
subprocess.run(["go","test",*(str(direct_dir/n) for n in ("direct_types.go","direct_session.go","direct_transport.go","direct_radio.go","direct_main.go"))],check=True)
target=root/"rootfs-overlay/usr/local/bin/2pny-direct-core"
env=os.environ.copy();env.update({"GOOS":"linux","GOARCH":"arm64","CGO_ENABLED":"0"})
subprocess.run(["go","build","-trimpath","-o",str(target),*(str(direct_dir/n) for n in ("direct_types.go","direct_session.go","direct_transport.go","direct_radio.go","direct_main.go"))],check=True,env=env)
os.chmod(target,0o755)

# PROTO-022: stage a surgical patch into the existing pinned DMRGateway build.
install("ci/patch-dmrgateway-voice-arbiter-0.3.16.py",
        "rootfs-overlay/builder/patch-dmrgateway-voice-arbiter-0.3.16.py",0o755)
builder=root/"builder/build-image.sh"
s=builder.read_text()
stage_anchor='cp "$ROOT_DIR/rootfs-overlay/builder/patch-dmrgateway-hourly-0.2.9.py" "$ROOT_MNT/builder/"'
stage_add=stage_anchor+'\ncp "$ROOT_DIR/rootfs-overlay/builder/patch-dmrgateway-voice-arbiter-0.3.16.py" "$ROOT_MNT/builder/"'
if "patch-dmrgateway-voice-arbiter-0.3.16.py" not in s:
    if stage_anchor not in s: raise SystemExit("0.3.16 builder: DMR patch staging anchor missing")
    s=s.replace(stage_anchor,stage_add,1)
apply_anchor='python3 /builder/patch-dmrgateway-hourly-0.2.9.py "$DG"'
apply_add=apply_anchor+'\npython3 /builder/patch-dmrgateway-voice-arbiter-0.3.16.py "$DG"'
if 'python3 /builder/patch-dmrgateway-voice-arbiter-0.3.16.py "$DG"' not in s:
    if apply_anchor not in s: raise SystemExit("0.3.16 builder: DMR patch apply anchor missing")
    s=s.replace(apply_anchor,apply_add,1)
builder.write_text(s);os.chmod(builder,0o755)

(root/"rootfs-overlay/etc/2pny/version").write_text(version+"\n")

# Syntax/compile gates before the expensive image build.
subprocess.run(["gofmt","-w",str(root/"src/2pnyd/main.go")],check=True)
subprocess.run(["go","test",str(root/"src/2pnyd/main.go")],check=True)
for rel in (
    "rootfs-overlay/usr/local/lib/2pny-live-core.py",
    "rootfs-overlay/usr/local/sbin/2pny-aprs",
    "rootfs-overlay/usr/local/sbin/2pny-display-apply",
    "rootfs-overlay/usr/local/sbin/2pny-protocol-network-apply",
    "rootfs-overlay/usr/local/sbin/2pny-timezone-apply",
    "rootfs-overlay/usr/local/sbin/2pny-ssh-apply",
):
    subprocess.run(["python3","-m","py_compile",str(root/rel)],check=True)
for rel in ("rootfs-overlay/usr/local/sbin/2pny-network-switch","rootfs-overlay/usr/local/sbin/2pny-network-core"):
    subprocess.run(["bash","-n",str(root/rel)],check=True)
for base in (root/"rootfs-overlay/usr/local/lib",root/"rootfs-overlay/usr/local/sbin"):
    cache=base/"__pycache__"
    if cache.exists():shutil.rmtree(cache)

# Parse corrected inline JS.
for html in ("dashboard.html","internet.html","hotspot.html","aprs.html","display.html","expert.html"):
    txt=(root/"rootfs-overlay/usr/share/2pny"/html).read_text()
    for body in re.findall(r"<script(?:\s[^>]*)?>(.*?)</script>",txt,re.I|re.S):
        if not body.strip():continue
        with tempfile.NamedTemporaryFile("w",suffix=".js",delete=False) as tf:
            tf.write(body);name=tf.name
        try:subprocess.run(["node","--check",name],check=True)
        finally:os.unlink(name)

main=(root/"src/2pnyd/main.go").read_text()
internet=(root/"rootfs-overlay/usr/share/2pny/internet.html").read_text()
dash=(root/"rootfs-overlay/usr/share/2pny/dashboard.html").read_text()
hotspot=(root/"rootfs-overlay/usr/share/2pny/hotspot.html").read_text()
aprs=(root/"rootfs-overlay/usr/local/sbin/2pny-aprs").read_text()
aprsui=(root/"rootfs-overlay/usr/share/2pny/aprs.html").read_text()
display=(root/"rootfs-overlay/usr/local/sbin/2pny-display-apply").read_text()
dstar=(root/"rootfs-overlay/usr/local/sbin/2pny-protocol-network-apply").read_text()
tzpath=(root/"rootfs-overlay/etc/systemd/system/2pny-timezone-apply.path").read_text()
sshpath=(root/"rootfs-overlay/etc/systemd/system/2pny-ssh-apply.path").read_text()
direct=(direct_dir/"direct_session.go").read_text()

assert '"0.3.16-alpha"' in main
assert 'time.Since(connectivityCacheAt) < 2*time.Second' in main
assert 'r.URL.Query().Get("fresh") == "1"' in main
assert 'connection.autoconnect-retries 3' in (root/"rootfs-overlay/usr/local/sbin/2pny-network-switch").read_text()
assert 'nmcli networking on' in (root/"rootfs-overlay/usr/local/sbin/2pny-network-core").read_text()
assert 'setInterval(function(){if(!document.hidden)load()},2000)' in internet
assert "rfMetrics=origin==='RF'" in dash
assert 'waitProtocolConnection' in hotspot
assert 'PathExists=/run/2pny/timezone-request.json' in tzpath
assert 'PathExists=/run/2pny/ssh-request.json' in sshpath
assert 'sshPubFile' in (root/"rootfs-overlay/usr/share/2pny/expert.html").read_text()
assert 'server_candidates' in aprs and 'rotate.aprs2.net' in aprs
assert 'waiting_ack' in aprs and 'Enviada · aguardando confirmação (ACK)' in aprsui
assert 'ensureAPRSDefaults' in main and '"enabled": true' in main
assert 'renderer="mmdvmhost-native"' in display and 'if kind=="nextion_mmdvm"' in display
assert 'ReloadTimer=72' in dstar and 'DStar_Hosts.json' in dstar and 'reflector_type="DCS"' in dstar
assert 'time.After(4 * time.Second)' in direct and 'c.register()' in direct
assert 'client := &http.Client{Timeout: 15 * time.Second}' in main
assert 'patch-dmrgateway-voice-arbiter-0.3.16.py' in builder.read_text()

# Critical inherited baseline: do not silently replace the DMR helper/RF bootstrap.
dmr=(root/"rootfs-overlay/usr/local/libexec/2pny-dmr-apply").read_text()
rf=(root/"rootfs-overlay/usr/local/sbin/2pny-rf-apply").read_text()
assert '[Log]\nDisplayLevel=1\nMQTTLevel=0' in dmr
assert 'DMRGateway did not remain active' in dmr
assert '[Log]\nMQTTLevel=0\nDisplayLevel=0' in rf
assert 'RF_APPLY_OK' in rf

print("PREPARE_0316_OK")
