#!/usr/bin/env python3
"""Deterministic source gates for PU2PNY-OS 0.3.9-alpha."""
from pathlib import Path
import re

R=Path(__file__).resolve().parents[1]
def read(p): return (R/p).read_text()

main=read("src/2pnyd-main-0.3.9.go")
proto=read("src/2pny-protocol-network-apply-all-0.3.9.py")
net=read("src/2pny-network-switch-0.3.9")
netcore=read("src/2pny-network-core-0.3.9")
internet=read("src/internet-0.3.9.html")
ui=read("src/ui-common-0.3.9.js")
expert=read("src/expert-0.3.9.html")
display_status=read("src/2pny-display-status-0.3.9.py")
display_apply=read("src/2pny-display-apply-0.3.9.py")
lang=read("src/ui-language-0.3.9.js")
prepare=read("ci/prepare-0.3.9-alpha.py")
boot=read("src/2pny-operational-restore-0.3.9.service")
op=read("src/2pny-operational-apply-0.3.9.py")

assert 'appVersion            = "0.3.9-alpha"' in main
assert "def udp_listener(port)" in proto
assert "udp_listener(20010)" in proto and "udp_listener(4200)" in proto
assert "local=cols[3]" in proto and "local=cols[4]" not in proto
assert "verify_host_bridge_config(proto)" in proto
assert "deadline=time.time()+12" in proto
assert r'(?m)\\b127\\.0\\.0\\.1:20010' not in proto
assert r'(?m)\\b127\\.0\\.0\\.1:4200' not in proto
assert 'for attempt in 1 2 3' in net
assert "merge_scan_json" in net
assert "passive_count" in net
assert "sed -i '/^dhcp-option-force=114,/d'" in netcore
assert 'if test ! -f "$STATE/provisioned"; then' in netcore
assert 'test -f "$STATE/provisioned" || return 0' in netcore
assert 'http://10.43.0.1/wizard?captive=1' in main
assert "5 GHz" in internet and "2,4 GHz" in internet and "bandgraph" in internet
assert "effective_dns" in internet
assert "addEventListener('live'" in ui and "addEventListener('live'" in expert
assert "var live=q('liveBox')" in ui
assert "main.insertBefore(sec,top.nextSibling)" in ui
assert "mmdvmhost-authoritative" in display_status
assert '"error": (0, "Erro / Error")' in display_status
assert 'não confirmou o layout Nextion solicitado' in display_apply
assert 'strings.TrimSuffix(service, ".service") + ".path"' in main
assert 'exec.Command("systemctl", "start", service)' not in main
assert "effective_dns" in main
for name in ("timezone","ssh","operational","rflevel","display-apply-request"):
    assert f"2pny-{name}" in prepare
assert "Restart=on-failure" in boot and "RestartSec=8" in boot
assert "wait_prereqs" in op and "mosquitto.service" in op
assert "if(!base){base=text;originals.set(node,base)}" in lang

# 0.3.9 must not replace proven DMR helper, Direct page, or History page.
# No 0.3.9 install() entry may replace the proven DMR helper, Direct UI or History UI.
assert not re.search(r'install\("src/[^"]*dmr[^"]*"\s*,',prepare,re.I)
assert not re.search(r'install\("src/direct[^"]*"\s*,\s*"rootfs-overlay/usr/share/2pny/direct\.html"',prepare)
assert not re.search(r'install\("src/history[^"]*"\s*,\s*"rootfs-overlay/usr/share/2pny/history\.html"',prepare)

# Captive fallback canonical address.
assert 'address=/#/10.43.0.1' in prepare
assert 'dhcp-option-force=114,http://10.43.0.1/captive-api' not in prepare

print("TEST-0.3.9-FEATURES PASS")
