#!/usr/bin/env python3
"""Offline 5.08 overlay on the published 5.07 image.

CLOCK-058 (zone written and confirmed through /etc/localtime, status read from files),
DISPLAY-058 (i2c-dev at boot, OLED/LCD found next to an unconfirmed Nextion, display core kept running),
SPEED-058 (operator data before the photo, lighter background timers/services, longer display apply),
UI-058 (Wi-Fi % from dBm with green/yellow/red bars, logo and favicon), BOOT-058 (no first-boot user dialog),
EXPERT-058 (Wi-Fi, warnings and boot timeline evidence). Edits must match exactly once.
Never touches MMDVMHost, DMRGateway, NextionDriver, the probe, the autostart scripts or the RF apply scripts.
"""
import os
import shutil
import sys
from pathlib import Path

root, arch, binary = Path(sys.argv[1]).resolve(), sys.argv[2], Path(sys.argv[3]).resolve()
repo = Path(__file__).resolve().parents[1]
fix = repo/'ci/fixtures/5.03'
assert arch in ('arm32', 'arm64')
assert root != Path('/') and (root/'etc/2pny/version').read_text().strip() == '5.07.000'
assert binary.is_file() and binary.stat().st_size > 1000000
backed = set()
SUFFIX = '.pre-5.08'


def backup(path):
    src, dst = root/path, root/(path + SUFFIX)
    if path in backed:
        return
    assert src.is_file() and not dst.exists()
    shutil.copy2(src, dst)
    backed.add(path)


def replace(path, old, new, count=1):
    p = root/path
    text = p.read_text()
    assert text.count(old) == count, (path, old[:70], text.count(old))
    p.write_text(text.replace(old, new))


def baseline(path, name):
    assert (root/path).read_bytes() == (fix/name).read_bytes(), 'unexpected baseline: ' + path


def upgrade(target, source, expected, mode):
    installed = root/target
    expected_bytes = expected.read_bytes() if isinstance(expected, Path) else expected
    assert installed.read_bytes() == expected_bytes, 'unexpected baseline: ' + target
    backup(target)
    shutil.copyfile(source, installed)
    installed.chmod(mode)


def create(target, content, mode):
    path = root/target
    assert not path.exists(), target
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(content, Path):
        shutil.copyfile(content, path)
    else:
        path.write_text(content)
    path.chmod(mode)


def mask(unit, wants):
    """Mask a unit (link to /dev/null) and drop its enable link. Reversible: remove the mask link."""
    link = root/'etc/systemd/system'/unit
    assert not link.exists() and not link.is_symlink(), unit
    enabled = root/'etc/systemd/system'/wants/unit
    assert enabled.is_symlink(), (unit, wants)
    enabled.unlink()
    os.symlink('/dev/null', link)


backup('usr/local/bin/2pnyd')
shutil.copyfile(binary, root/'usr/local/bin/2pnyd')
(root/'usr/local/bin/2pnyd').chmod(0o755)

# CLOCK-058 ------------------------------------------------------------------------------------------
upgrade('usr/local/sbin/2pny-timezone-apply', repo/'runtime/5.08/tz-apply.py', repo/'runtime/5.06/tz-apply.py', 0o755)
upgrade('usr/local/sbin/2pny-timezone-restore', repo/'runtime/5.08/tz-restore.sh', fix/'2pny-timezone-restore', 0o755)

# EXPERT-058 -----------------------------------------------------------------------------------------
upgrade('usr/local/libexec/pu2pny/expert-cmd-504.py', repo/'runtime/5.08/expert-cmd.py', repo/'runtime/5.07/expert-cmd.py', 0o755)

# DISPLAY-058 ----------------------------------------------------------------------------------------
upgrade('usr/local/libexec/pu2pny/i2c-505.py', repo/'runtime/5.08/i2c.py', repo/'runtime/5.05/i2c.py', 0o644)
create('etc/modules-load.d/2pny-i2c.conf', '# PU2PNY-OS 5.08: /dev/i2c-* only exists with i2c-dev; OLED/LCD scan needs it.\ni2c-dev\n', 0o644)
create('etc/systemd/system/2pny-display-core.service.d/58-i2c.conf', '[Service]\nExecStartPre=-+/sbin/modprobe i2c-dev\n', 0o644)
apply = 'usr/local/sbin/2pny-display-apply'
baseline(apply, '2pny-display-apply')
backup(apply)
replace(apply,
        "                            'updated': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}, 0o644)\n"
        "    except Exception:\n"
        "        for u in units:\n"
        "            ctl('stop', u, check=False)\n",
        "                            'updated': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}, 0o644)\n"
        "        # DISPLAY-058: Nextion through the modem and an I2C OLED/LCD use different buses and can coexist.\n"
        "        # The display core stays up only when the read-only bus scan really finds an I2C display.\n"
        "        try:\n"
        "            import importlib.util as _iu\n"
        "            _spec = _iu.spec_from_file_location('i2c505', '/usr/local/libexec/pu2pny/i2c-505.py')\n"
        "            _mod = _iu.module_from_spec(_spec)\n"
        "            _spec.loader.exec_module(_mod)\n"
        "            if _mod.scan() is not None:\n"
        "                ctl('enable', CORE, check=False)\n"
        "                ctl('start', CORE, check=False)\n"
        "        except Exception:\n"
        "            pass\n"
        "    except Exception:\n"
        "        for u in units:\n"
        "            ctl('stop', u, check=False)\n")
request = 'usr/local/sbin/2pny-display-apply-request'
baseline(request, '2pny-display-apply-request')
backup(request)
replace(request, 'stderr=subprocess.STDOUT,timeout=35)', 'stderr=subprocess.STDOUT,timeout=120)')

# SPEED-058: operator data first, photo afterwards --------------------------------------------------
worker = 'usr/local/sbin/2pny-station-worker'
baseline(worker, '2pny-station-worker')
backup(worker)
replace(worker, 'def lookup(key):\n',
        'def cached_photo(call):\n'
        '    """SPEED-058: photo path only when the file is already cached; the download runs as its own job."""\n'
        '    call=str(call or "").upper().strip()\n'
        '    if not re.fullmatch(r"[A-Z0-9/]{3,16}",call):return ""\n'
        '    dest=PHOTOS/(call.replace("/","_")+".img")\n'
        '    return "/operator-photo/"+dest.name if dest.exists() else ""\n\n'
        'def lookup(key):\n')
replace(worker, '    person["photo"]=qrz_photo(person["callsign"]) if person["callsign"] else ""\n',
        '    person["photo"]=cached_photo(person["callsign"]) if person["callsign"] else ""\n')
replace(worker, 'probe=None;lookup_job=None;last_lookup=0;', 'probe=None;lookup_job=None;photo_job=None;last_lookup=0;')
replace(worker, '            lookup_job=None;dirty=True\n',
        '            lookup_job=None;dirty=True\n'
        '            if person and person.get("callsign") and not person.get("photo") and not photo_job:\n'
        '                photo_job=(ident,pool.submit(qrz_photo,person["callsign"]))\n'
        '        if photo_job and photo_job[1].done():\n'
        '            pident,pfut=photo_job\n'
        '            try:ppath=pfut.result()\n'
        '            except Exception:ppath=""\n'
        '            prow=db.execute("SELECT data FROM contacts WHERE key=?",(pident,)).fetchone()\n'
        '            if prow and ppath:\n'
        '                try:pp=json.loads(prow[0])\n'
        '                except Exception:pp={}\n'
        '                pp["photo"]=ppath\n'
        '                db.execute("UPDATE contacts SET data=? WHERE key=?",(json.dumps(pp,ensure_ascii=False),pident));db.commit()\n'
        '            photo_job=None;dirty=True\n')
replace(worker, 'wall-last_lookup>=15:', 'wall-last_lookup>=4:')

# UI-058: Wi-Fi/Internet bars and brand ------------------------------------------------------------
common = 'usr/share/2pny/ui-common-0.3.0.js'
baseline(common, 'ui-common-0.3.0.js')
backup(common)
replace(common, "q('pnyWiFiBar').style.width='100%'}", "q('pnyWiFiBar').style.width='100%';q('pnyWiFiBar').style.background='var(--green)'}")
replace(common, "q('pnyWiFiBar').style.width=(c.wifi_signal||0)+'%'}",
        "q('pnyWiFiBar').style.width=(c.wifi_signal||0)+'%';q('pnyWiFiBar').style.background=pnyQ(c.wifi_quality)}")
replace(common, "q('pnyNetBar').style.width=c.internet?Math.max(12,100-Math.min(90,(c.internet_latency_ms||0)/3))+'%':'0%';",
        "q('pnyNetBar').style.width=c.internet?Math.max(12,100-Math.min(90,(c.internet_latency_ms||0)/3))+'%':'0%';q('pnyNetBar').style.background=pnyQ(c.internet?c.internet_quality:'Offline');")
replace(common, '  async function loadConnectivity(){',
        "  function pnyQ(t){t=String(t||'').toLowerCase();return /^(ótimo|otimo|excel|great)/.test(t)?'var(--green)':/^(bom|boa|good|aten)/.test(t)?'var(--yellow)':'var(--red)'}\n"
        '  async function loadConnectivity(){')
for name in ('logo.png', 'favicon.png', 'favicon-192.png', 'apple-touch-icon.png'):
    create('usr/share/2pny/brand/' + name, repo/'assets/brand/web'/name, 0o644)
language = 'usr/share/2pny/ui-language.js'
baseline(language, 'ui-language.js')
backup(language)
(root/language).write_text((root/language).read_text() + '\n' + (repo/'runtime/5.08/brand.js').read_text())

# SPEED-058 / BOOT-058: nothing a headless hotspot never uses ----------------------------------------
mask('userconfig.service', 'multi-user.target.wants')
for unit in ('apt-daily.timer', 'apt-daily-upgrade.timer', 'man-db.timer', 'e2scrub_all.timer', 'dpkg-db-backup.timer'):
    mask(unit, 'timers.target.wants')
mask('ModemManager.service', 'multi-user.target.wants')
mask('triggerhappy.service', 'multi-user.target.wants')
mask('udisks2.service', 'graphical.target.wants')

(root/'etc/2pny/version').write_text('5.08.000\n')
print('PATCH_508_OK', arch)
