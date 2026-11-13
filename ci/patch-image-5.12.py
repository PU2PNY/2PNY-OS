#!/usr/bin/env python3
"""BOOT-512: serviços opcionais fora do caminho crítico de boot, mantendo timers e rollback."""
import os
import shutil
import sys
from pathlib import Path

def apply(root: Path):
    root = root.resolve()
    assert root != Path('/'), "nunca operar no host de build"
    version = root / 'etc/2pny/version'
    assert version.read_text().strip() == '5.11.000', 'exigir base 5.11 exata'
    previous = version.with_name('version.pre-5.12')
    assert not previous.exists(), 'patch duplicado'
    shutil.copy2(version, previous)

    units = root / 'etc/systemd/system'
    delayed = ('2pny-auto-maintenance', '2pny-hostfiles-update')
    for name in delayed:
        delay = units / f'{name}.service.d/60-delay.conf'
        assert delay.is_file(), 'BOOT-512: delay esperado ausente: ' + str(delay)
        assert delay.read_text().count('ExecStartPre=/bin/sleep 300') == 1, (
            'BOOT-512: mudou o contrato do delay; investigar antes de alterar: ' + name)
        backup = delay.with_name('60-delay.conf.pre-5.12')
        assert not backup.exists(), 'BOOT-512: backup já presente'
        shutil.copy2(delay, backup)
        delay.unlink()

        # Unidades opcinais não devem ser WantedBy do multi-user.target.
        link = units / 'multi-user.target.wants' / f'{name}.service'
        if link.is_symlink():
            assert os.path.basename(os.readlink(link)) == f'{name}.service', (
                'BOOT-512: link não reconhecido: ' + str(link))
            link.unlink()
        assert not link.exists() and not link.is_symlink(), (
            'BOOT-512: serviço ainda diretamente habilitado no boot: ' + name)

    host_timer = units / '2pny-hostfiles-update.timer'
    host_wanted = units / 'timers.target.wants/2pny-hostfiles-update.timer'
    assert host_timer.is_file() and host_wanted.is_symlink(), (
        'BOOT-512: timer de hostfiles já aprovado precisa ser preservado')

    maintenance_timer = units / '2pny-auto-maintenance.timer'
    assert not maintenance_timer.exists() and not maintenance_timer.is_symlink(), (
        'BOOT-512: timer manutenção existente; avaliar em vez de sobrescrever')
    maintenance_timer.write_text(
        '[Unit]\n'
        'Description=PU2PNY manutenção eventual fora do boot\n'
        '[Timer]\n'
        'OnBootSec=8min\n'
        'OnUnitInactiveSec=24h\n'
        'AccuracySec=1min\n'
        'Unit=2pny-auto-maintenance.service\n'
        '[Install]\n'
        'WantedBy=timers.target\n'
    )
    maintenance_timer.chmod(0o644)
    timer_link = units / 'timers.target.wants/2pny-auto-maintenance.timer'
    assert not timer_link.exists() and not timer_link.is_symlink()
    timer_link.parent.mkdir(parents=True, exist_ok=True)
    timer_link.symlink_to('../2pny-auto-maintenance.timer')
    version.write_text('5.12.000\n')
    version.chmod(0o644)
    assert (units / '2pny-hostfiles-update.service').is_file()
    assert (units / '2pny-auto-maintenance.service').is_file()
    print('BOOT_512_SERVICES_DEFERRED_OK')

if __name__ == '__main__':
    assert len(sys.argv) == 2, 'uso: patch-image-5.12.py ROOTFS'
    apply(Path(sys.argv[1]))
