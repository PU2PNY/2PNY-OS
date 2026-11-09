#!/usr/bin/env python3
"""VOICE-056: spoken hour on D-Star, built from the gateway's own TIME_*.ambe voice data.

Runs at every full hour (systemd timer). It only transmits when the saved voice settings and the
hourly marker are on, the active protocol is D-Star, MMDVMHost and the D-Star gateway are active.
Words are cut from TIME_en_GB (the only time vocabulary shipped with the gateway) and handed to
dgwvoicetransmit, the gateway's own voice transmit tool. Never touches RF configuration.
"""
import datetime, json, os, subprocess, sys, tempfile
from pathlib import Path

STATE = Path(os.environ.get('PNY_STATE', '/var/lib/2pny'))
DATA = Path(os.environ.get('PNY_VOICE_DATA', '/usr/local/share/dstargateway.d'))
TOOL = os.environ.get('PNY_VOICETX', '/usr/local/bin/dgwvoicetransmit')
FRAME = 9          # bytes per AMBE voice frame; index offsets/lengths are counted in frames
MAGIC = b'AMBE'

def readj(path):
    try:
        return json.loads(Path(path).read_text())
    except Exception:
        return {}

def read_index(path):
    words = {}
    for line in Path(path).read_text().splitlines():
        parts = line.split()
        if len(parts) == 3:
            try:
                words[parts[0]] = (int(parts[1]), int(parts[2]))
            except ValueError:
                pass
    return words

def sentence(hour):
    """English phrase of the TIME_en_GB vocabulary for a 24 h clock hour."""
    if hour == 0:
        return ['It_is', 'midnight']
    if hour == 12:
        return ['It_is', 'midday']
    names = ['zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten', 'eleven', 'twelve']
    return ['It_is', names[hour % 12], 'O_Clock', 'AM' if hour < 12 else 'PM']

def cut_words(ambe_bytes, index, words, folder):
    """Write one .ambe file per word (AMBE magic + the word's frames); returns the paths in order."""
    assert ambe_bytes[:4] == MAGIC
    body = ambe_bytes[4:]
    paths = []
    for position, word in enumerate(words):
        offset, length = index[word]
        chunk = body[offset * FRAME:(offset + length) * FRAME]
        if len(chunk) != length * FRAME:
            raise ValueError('voice data shorter than index: ' + word)
        path = folder / f'{position:02d}-{word}.ambe'
        path.write_bytes(MAGIC + chunk)
        paths.append(str(path))
    return paths

def gateway_repeater(path):
    """8-character gateway repeater name (callsign padded to 7 + module) from [Repeater 1]."""
    import configparser
    cp = configparser.ConfigParser(interpolation=None, strict=False)
    try:
        cp.read(path)
        call = cp.get('Repeater 1', 'Callsign').strip().upper()
        band = cp.get('Repeater 1', 'Band').strip().upper()
    except Exception:
        return ''
    if not call or len(call) > 7 or len(band) != 1 or not (call.replace('/', '').isalnum() and band.isalpha()):
        return ''
    return call.ljust(7) + band

def active(unit):
    return subprocess.run(['systemctl', 'is-active', '--quiet', unit], check=False,
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10).returncode == 0

def log(message):
    subprocess.run(['logger', '-t', 'pu2pny-hourly-voice', '--', message], check=False,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def main(now=None):
    settings = readj(STATE / 'voice-settings.json')
    if settings.get('enabled') is False or not (STATE / 'voice-hourly.enabled').exists():
        return 0
    cfg = readj(STATE / 'config.json')
    if str(cfg.get('protocol') or '').upper().replace('-', '') != 'DSTAR':
        return 0
    if not (active('2pny-mmdvmhost.service') and active('2pny-dstargateway.service')):
        log('hora cheia ignorada: MMDVMHost ou gateway D-Star inativo')
        return 0
    repeater = gateway_repeater(STATE / 'dstar' / 'DStarGateway.ini')
    if not repeater:
        log('hora cheia ignorada: repetidor local não encontrado em DStarGateway.ini')
        return 0
    now = now or datetime.datetime.now()
    try:
        index = read_index(DATA / 'TIME_en_GB.indx')
        ambe = (DATA / 'TIME_en_GB.ambe').read_bytes()
        words = sentence(now.hour)
        with tempfile.TemporaryDirectory(prefix='pny-hour-') as tmp:
            files = cut_words(ambe, index, words, Path(tmp))
            result = subprocess.run([TOOL, repeater] + files, check=False, timeout=40,
                                    stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
    except Exception as exc:
        log('hora cheia falhou: ' + str(exc)[:200])
        return 0
    log('hora cheia ' + ' '.join(words) + ' rc=' + str(result.returncode) + ' ' + (result.stderr or '')[-120:].strip())
    return 0

if __name__ == '__main__':
    sys.exit(main())
