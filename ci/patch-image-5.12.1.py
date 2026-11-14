#!/usr/bin/env python3
"""P1 overlay for published 5.12.000: diagnostics, display-only and UI safety.
NextionDriver/MMDVMHost/RF/NetworkManager/SSID/bootloaders are never modified.
Fails closed on unexpected rootfs, files or anchors. No automatic HMI flashing.
"""
from pathlib import Path
import os
import shutil
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
SUFFIX = '.pre-5.12.1'
NAV_EMPTY = '<nav class="nav" id="mainNav"></nav>'
STATIC_NAV = '<nav class="nav" id="mainNav">' + ''.join(
    f'<a href="{url}">{label}</a>' for url,label in (
        ('/dashboard','Ao Vivo'),('/internet','Internet'),('/hotspot','Protocolos'),
        ('/direct','Direct'),('/aprs','APRS'),('/history','Histórico'),
        ('/display','Display'),('/system','Sistema'),('/expert','Expert')
    )
) + '</nav>'
HIDDEN_CLOCK = ('<h2>Relógio</h2><style>article:has(#localClock),#clockLocal,'
                '#clockUTC,#pnyClock,.top .clock{display:none!important}</style>')

def apply(root):
    root = Path(root).resolve()
    assert root != Path('/'), 'não alterar o sistema do builder'
    version = root/'etc/2pny/version'
    assert version.is_file() and version.read_text().strip()=='5.12.000', 'base 5.12 P0 exata obrigatória'
    originals = {
        'usr/local/libexec/pu2pny/oled-502.py':'runtime/5.11/oled.py',
        'usr/local/libexec/pu2pny/lcd-504.py':'runtime/5.04/lcd.py',
        'usr/local/libexec/pu2pny/expert-cmd-504.py':'runtime/5.10/expert-cmd.py',
    }
    replacements = {
        'usr/local/libexec/pu2pny/oled-502.py':'runtime/5.12.1/oled.py',
        'usr/local/libexec/pu2pny/lcd-504.py':'runtime/5.12.1/lcd.py',
        'usr/local/libexec/pu2pny/expert-cmd-504.py':'runtime/5.12.1/expert-cmd.py',
    }
    for installed,baseline in originals.items():
        target=root/installed
        expected=(ROOT_DIR/baseline).read_bytes()
        # HOST-057/511 changed only the advertised hostname in the legacy LCD module.
        # Validate the exact variant; do not treat an arbitrary edited baseline as safe.
        variants=[expected]
        if installed.endswith('/lcd-504.py'):
            variants += [expected.replace(b'pu2pny.local',host) for host in
                         (b'pu2pny32.local',b'pu2pny64.local')]
        assert target.is_file() and target.read_bytes() in variants, 'baseline alterado: '+installed
        assert not (root/(installed+SUFFIX)).exists(), 'patch duplicado'
    folder=root/'usr/share/2pny'
    assert folder.is_dir()
    html=[]
    for p in sorted(folder.glob('*.html')):
        data=p.read_text(encoding='utf-8')
        if 'id="mainNav"' in data:
            assert data.count(NAV_EMPTY)==1, 'nav inesperada: '+p.name
            html.append(p)
    for name in ('dashboard.html','system.html','expert.html','hotspot.html'):
        assert folder.joinpath(name) in html, 'página protegida sem menu: '+name
    system=folder/'system.html'
    source=system.read_text(encoding='utf-8')
    assert source.count(HIDDEN_CLOCK)==1, 'controle de relógio oculto inesperado'
    assert source.count('Operação do rádio, voz, energia e estado do sistema.')==1, 'descrição do sistema mudou'
    assert not (root/'etc/2pny/version.pre-5.12.1').exists()
    for p in html:
        assert not p.with_name(p.name+SUFFIX).exists(),p.name
    changed=[]
    def backup(p):
        backup_path=p.with_name(p.name+SUFFIX)
        assert p.is_file() and not backup_path.exists()
        shutil.copy2(p,backup_path)
        changed.append(str(backup_path.relative_to(root)))
    # Add static anchors only as a fallback. Existing PNY.nav() still owns dynamic navigation.
    for p in html:
        backup(p)
        s=p.read_text(encoding='utf-8')
        s=s.replace(NAV_EMPTY,STATIC_NAV,1)
        if p==system:
            s=s.replace(HIDDEN_CLOCK,'<h2>Relógio</h2>',1)
            s=s.replace('Operação do rádio, voz, energia e estado do sistema.',
                        'Relógio, sincronização, operação do rádio e energia.',1)
        p.write_text(s,encoding='utf-8')
        changed.append(str(p.relative_to(root)))
    for installed,source in replacements.items():
        p=root/installed
        backup(p)
        shutil.copyfile(ROOT_DIR/source,p)
        p.chmod(0o755 if source.endswith('expert-cmd.py') else 0o644)
        compile(p.read_bytes(),str(p),'exec')
        changed.append(installed)
    backup(version)
    version.write_text('5.12.001\n')
    version.chmod(0o644)
    changed.append('etc/2pny/version')
    # No other files, services, Nextion HMI, modem or kernel are ever modified.
    print('PATCH_5121_READONLY_RF_OK',len(changed),flush=True)
    return set(changed)

if __name__=='__main__':
    assert len(sys.argv)==2
    apply(Path(sys.argv[1]))
