#!/usr/bin/env python3
from pathlib import Path
import os,shutil,subprocess,tempfile

root=Path(__file__).resolve().parents[1]

# Protected radio/gateway implementation remains byte-identical to 0.3.27/0.3.26.
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
    prior=subprocess.check_output(["git","show","v0.3.27-alpha:"+p],cwd=root)
    assert (root/p).read_bytes()==prior, "protected protocol changed: "+p

# Exercise the real network patch on disposable copies.
with tempfile.TemporaryDirectory() as td:
    stage=Path(td)
    (stage/"rootfs-overlay/usr/local/sbin").mkdir(parents=True)
    shutil.copy2(root/"src/2pny-network-switch-0.3.26",stage/"rootfs-overlay/usr/local/sbin/2pny-network-switch")
    shutil.copy2(root/"src/2pny-wifi-profiles-0.3.26",stage/"rootfs-overlay/usr/local/sbin/2pny-wifi-profiles")
    subprocess.run(["python3",str(root/"ci/patch-network-reliability-0.3.28.py"),str(stage)],check=True)
    n=(stage/"rootfs-overlay/usr/local/sbin/2pny-network-switch").read_text()
    w=(stage/"rootfs-overlay/usr/local/sbin/2pny-wifi-profiles").read_text()
    assert "nmcli --wait 45 connection up PU2PNY-WIFI-CANDIDATE" in n
    assert "ipv4.dhcp-timeout 30" in n
    assert "for _ in $(seq 1 30); do" in n
    assert "connection.autoconnect-priority 200 connection.autoconnect-retries 3" in n
    assert 'nm --wait 18 connection up "$chosen"' in w
    assert 'nm --wait 22 connection up "$SECONDARY"' in w
    assert 'nm --wait 15 connection up uuid "$old_uuid"' in w
    assert "connection.autoconnect-priority 150 connection.autoconnect-retries 3" in w

timer=(root/"src/2pny-hostfiles-update-0.3.28.timer").read_text()
assert "OnUnitActiveSec=8h" in timer and "Persistent=true" in timer
svc=(root/"src/2pny-hostfiles-update-0.3.28.service").read_text()
assert "ExecStart=/usr/local/sbin/2pny-hostfiles-update" in svc
online=(root/"src/2pny-network-online-0.3.28").read_text()
assert "2pny-mdns-guard" in online
assert "2pny-hostfiles-update.service" in online
assert "2pny-profile-autostart.service" in online
assert "restart" not in online.lower()
dispatch=(root/"src/91-pu2pny-online-actions-0.3.28").read_text()
assert "up|dhcp4-change|connectivity-change" in dispatch
assert "systemctl start --no-block 2pny-network-online.service" in dispatch
assert "nmcli" not in dispatch

auto=(root/"src/2pny-profile-autostart-0.3.28.py").read_text()
guard='if active("2pny-mmdvmhost.service") and active(gateway):'
activate='"/usr/local/sbin/2pny-protocol-profiles","activate",proto'
assert guard in auto and activate in auto and auto.index(guard)<auto.index(activate)
assert "restart" not in auto
assert "password" not in auto.lower() and "secret" not in auto.lower()

live=(root/"src/dashboard-0.3.28.html").read_text()
for token in ("Perfil selecionado não está ativo.","Não conectado ao servidor.","Ativar perfil selecionado","activateSelectedProfile"):
    assert token in live
internet=(root/"src/internet-0.3.28.html").read_text()
assert "pu2pny-wifi2-target" in internet and "location.replace('/dashboard')" in internet
wizard=(root/"src/wizard-0.3.28.html").read_text()
assert "handoffEthernetToLAN" in wizard and "http://pu2pny.local" in wizard
assert "setInterval(pollConnectivity,600)" in wizard

# 0.3.27 requested APRS/BM behavior remains in the corrective branch.
main=(root/"src/2pnyd-main-0.3.27.go").read_text()
hot=(root/"src/hotspot-0.3.27.html").read_text()
aprs=(root/"src/2pny-aprs-0.3.27.py").read_text()
assert 'id="bmSecurityPassword"' in hot and 'type="password"' in hot
assert 'hotspot_security_configured' in main
assert 'cfg.get("latitude")' not in aprs and 'cfg.get("longitude")' not in aprs
print("REGRESSION_0328_OK")
