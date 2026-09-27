#!/usr/bin/env python3
from pathlib import Path
import subprocess, tempfile, shutil, sys
repo=Path(__file__).resolve().parents[1]
protected=[
"src/2pny-protocol-network-apply-0.3.21.py",
"src/2pny-protocol-network-apply-all-0.3.20.py",
"src/2pny-dstargateway-0.2.9.service",
"src/2pny-ysfgateway-0.2.9.service",
"src/2pny-mmdvmhost-0.3.13.service",
"ci/patch-dmrgateway-pu2pny-0.3.20.py",
"ci/patch-dmrgateway-voice-arbiter-0.3.21.py",
]
for p in protected:
    current=(repo/p).read_bytes()
    prior=subprocess.check_output(["git","show",f"v0.3.28-alpha:{p}"],cwd=repo)
    if current!=prior: raise SystemExit(f"protected source changed since 0.3.28: {p}")

with tempfile.TemporaryDirectory() as td:
    root=Path(td)/"stage"
    (root/"src/2pnyd").mkdir(parents=True)
    (root/"rootfs-overlay/usr/share/2pny/network").mkdir(parents=True)
    (root/"rootfs-overlay/usr/local/sbin").mkdir(parents=True)
    (root/"rootfs-overlay/usr/local/libexec").mkdir(parents=True)
    (root/"rootfs-overlay/etc/2pny").mkdir(parents=True)
    main=(repo/"src/2pnyd-main-0.3.27.go").read_text().replace('0.3.27-alpha','0.3.28-alpha',1)
    (root/"src/2pnyd/main.go").write_text(main)
    shutil.copy2(repo/"src/wizard-0.3.28.html",root/"rootfs-overlay/usr/share/2pny/wizard.html")
    shutil.copy2(repo/"src/expert-0.3.16.html",root/"rootfs-overlay/usr/share/2pny/expert.html")
    shutil.copy2(repo/"src/ui-language-0.3.27.js",root/"rootfs-overlay/usr/share/2pny/ui-language.js")
    shutil.copy2(repo/"src/2pny-network-core-0.3.9",root/"rootfs-overlay/usr/local/sbin/2pny-network-core")
    (root/"rootfs-overlay/usr/share/2pny/network/hostapd.template").write_text("interface=@IFACE@\nssid=pu2pny\n")
    (root/"rootfs-overlay/etc/2pny/version").write_text("0.3.28-alpha\n")
    for staged,src in [
      ("rootfs-overlay/usr/local/sbin/2pny-protocol-network-apply","src/2pny-protocol-network-apply-all-0.3.20.py"),
      ("rootfs-overlay/usr/local/libexec/2pny-dmr-apply","src/2pny-protocol-network-apply-0.3.21.py")]:
        shutil.copy2(repo/src,root/staged)
    subprocess.run([sys.executable,str(repo/"ci/patch-0.3.29-surgical.py"),str(root)],check=True)
    m=(root/"src/2pnyd/main.go").read_text()
    assert 'appVersion            = "0.3.29-alpha"' in m
    assert 'APSSID:            "PU2PNY-OS",' in m
    assert m.count('"ssid": "PU2PNY-OS"')==2
    assert '<TITLE>PU2PNY-OS</TITLE>' in m
    assert (root/"rootfs-overlay/usr/share/2pny/network/hostapd.template").read_text().splitlines()[-1]=="ssid=PU2PNY-OS"
    w=(root/"rootfs-overlay/usr/share/2pny/wizard.html").read_text()
    assert 'AP <b>PU2PNY-OS</b>' in w and '<title>PU2PNY-OS</title>' in w
    e=(root/"rootfs-overlay/usr/share/2pny/expert.html").read_text()
    assert 'Grupo de suporte PU2PNY-OS' in e
    assert 'chat.whatsapp.com/IEtpCZ1t8IoEgktJs2aNZq?s=cl&p=a&mlu=4&iam=0' in e
    assert 'PU2PNY-DIAG-' in e and 'Nada é enviado automaticamente' in e
    assert 'Transcoder necessário' in e and 'MMDVM-CrossMode atual usa MMDVM-Transcoder' in e
    l=(root/"rootfs-overlay/usr/share/2pny/ui-language.js").read_text()
    assert '"Transcoder necessário":["Transcoder required","Transcoder necesario"]' in l
    assert (root/"rootfs-overlay/etc/2pny/version").read_text().strip()=="0.3.29-alpha"
print("REGRESSION_0329_OK")
