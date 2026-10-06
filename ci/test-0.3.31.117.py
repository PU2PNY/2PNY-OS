#!/usr/bin/env python3
from pathlib import Path
import re
import subprocess

repo=Path(__file__).resolve().parents[1]
base='be75b68aa5549c15d538b1814ffd2df5987cb759'
base_branch='pu2pny-os-0.3.31.116-consolidation'

# The existing network backend already has real RSSI + canonical resume URLs.
go=(repo/'src/2pnyd-main-0.3.27.go').read_text()
for token in (
    'exec.Command("iw", "dev", iface, "link")',
    '"ACTIVE,SIGNAL", "dev", "wifi", "--rescan", "no"',
    'func lanResumeURLs(ips []string) []string',
    'out := []string{"http://pu2pny.local"}',
):
    assert token in go, token

internet=(repo/'src/internet-0.3.28.html').read_text()
assert 'async function wifiReachable(base)' in internet
assert "if(st.state==='connected')" in internet
assert "/api/network/connect/status" in internet

dash=(repo/'src/dashboard-0.3.28.html').read_text()
assert "id=\"netMeter\"" in dash
assert "dash.connectivity||{}" in dash
assert "PNY.q('netMeter').style.width=(q==='offline'?0:good?100:35)+'%'" in dash

display=(repo/'src/2pny-display-apply-0.3.30.py').read_text()
for token in ('Conflito de writer','mmdvmhost-native','No TFT/HMI is flashed by this helper'):
    assert token in display
page=(repo/'src/display-0.3.30.html').read_text()
for token in ('Compatível Pi-Star/WPSD (MMDVMHost nativo)','ON7LDS L3 · ScreenLayout 3','Nenhum TFT/HMI é gravado automaticamente'):
    assert token in page

hard=(repo/'ci/harden-nextiondriver-0.3.31.117.py').read_text()
for token in ('blocked HMI host-command request','external DB download disabled','updateDisplay call site still present'):
    assert token in hard
backend=(repo/'ci/patch-backend-0.3.31.117.py').read_text()
for token in ('on7lds-compatible','DISPLAY-025','115200','mmdvmhost-native'):
    assert token in backend
patch=(repo/'ci/patch-image-0.3.31.117.sh').read_text()
for token in ('followPrimaryToPanel','Wi-Fi / Uplink · Ethernet','on7lds-compatible','SendFrameType","1"','NoNewPrivileges=yes','IPAddressAllow=localhost'):
    assert token in patch
assert 'curl | bash' not in patch
assert 'wget ' not in patch

# No existing runtime source is edited in the branch. In shallow clones, fetch
# the immutable baseline ref and compare the two trees directly; a merge-base
# is not required for this scope gate.
if subprocess.run(['git','cat-file','-e',base+'^{commit}'],cwd=repo,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode:
    subprocess.run(['git','fetch','--no-tags','origin',base_branch+':refs/remotes/origin/'+base_branch],cwd=repo,check=True)
    got=subprocess.check_output(['git','rev-parse','refs/remotes/origin/'+base_branch],cwd=repo,text=True).strip()
    if got!=base:
        raise SystemExit(f'baseline ref moved: expected {base}, got {got}')
changed=subprocess.check_output(['git','diff','--name-only',base,'HEAD'],cwd=repo,text=True).splitlines()
allowed={
    '.github/workflows/0.3.31.117-build-release.yml',
    'ci/harden-nextiondriver-0.3.31.117.py',
    'ci/patch-backend-0.3.31.117.py',
    'ci/patch-image-0.3.31.117.sh',
    'ci/test-0.3.31.117.py',
    'ci/sync-canonical-0.3.31.117.py',
    'docs/HOTFIX-0.3.31.117.md',
    'PU2PNY-OS_MASTER_SPEC.md','PU2PNY-OS_RELEASE_STATUS.md','PU2PNY-OS_TEST_MATRIX.md','PU2PNY-OS_CHANGELOG.md',
}
bad=sorted(set(changed)-allowed)
if bad:
    raise SystemExit('0.3.31.117 scope violation: '+', '.join(bad))

# Protect RF/protocol/runtime sources explicitly.
protected=[x for x in changed if re.search(r'(^|/)(?:.*(?:dmr|dstar|ysf|mmdvm|protocol-network|network-switch|network-online|wizard).*)$',x,re.I)]
if protected:
    raise SystemExit('protected runtime source changed: '+', '.join(protected))

print('NETWORK_REAL_RSSI_BASELINE_OK')
print('WIFI_HANDOFF_PATCH_ANCHORS_OK')
print('NEXTION_COMPAT_SECURITY_POLICY_OK')
print('BACKEND_DISPLAY_POLICY_PATCH_OK')
print('SCOPE_0331117_OK',len(changed))
