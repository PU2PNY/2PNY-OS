#!/usr/bin/env python3
"""WIZ-059 / DISPLAY-059 software tests and the 5.04 -> 5.09 overlay chain."""
import importlib.util, os, subprocess, sys, tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'ci'))
spec = importlib.util.spec_from_file_location('t508', ROOT/'ci/test-5.08.py')
src = (ROOT/'ci/test-5.08.py').read_text().split('# ---------- overlay chain 5.04 -> 5.08')[0]
make_root_src = (ROOT/'ci/test-5.08.py').read_text().split('# ---------- overlay chain 5.04 -> 5.08')[1].split('with tempfile.TemporaryDirectory() as td:\n    binary')[0]
ns = {'os': os, 'Path': Path, 'ROOT': ROOT, 'FIX': ROOT/'ci/fixtures/5.03', 'subprocess': subprocess, 'sys': sys, 'tempfile': tempfile}
exec(make_root_src, ns)
make_root, chain = ns['make_root'], ns['chain']
FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf'


def chain509(root, arch, binary):
    chain(root, arch, binary)
    # the published 5.08 image carries the real 5.07 wizard (extracted from the image), not the test chain's
    (root/'usr/share/2pny/wizard.html').write_bytes((ROOT/'ci/fixtures/5.03/wizard-5.07.html').read_bytes())
    cp = subprocess.run([sys.executable, '-I', str(ROOT/'ci/patch-image-5.09.py'), str(root), arch, str(binary)], capture_output=True, text=True)
    assert cp.returncode == 0, (arch, cp.stderr[-800:])


# the chain helper stops at 5.08; 5.09 is applied after it
for arch in ('arm64', 'arm32'):
    with tempfile.TemporaryDirectory() as td:
        binary = Path(td)/'d'; binary.write_bytes(b'\0'*1_200_000)
        root = make_root(td + '/r'); chain509(root, arch, binary)
        assert (root/'etc/2pny/version').read_text() == '5.09.000\n'
        wiz = (root/'usr/share/2pny/wizard.html').read_text()
        assert '(opt&&opt.timeout)||15000' in wiz and 'timeout:150000' in wiz and "e.name==='AbortError'" in wiz
        assert (root/'usr/share/2pny/wizard.html.pre-5.09').read_bytes() == (ROOT/'ci/fixtures/5.03/wizard-5.07.html').read_bytes()
        node = subprocess.run(['which', 'node'], capture_output=True, text=True).stdout.strip()
        if node:
            import re
            scripts = re.findall(r'<script>(.*?)</script>', wiz, re.S)
            for i, s in enumerate(scripts):
                f = Path(td)/f's{i}.js'; f.write_text(s)
                assert subprocess.run([node, '--check', str(f)], capture_output=True).returncode == 0, ('wizard script', i)
        oled = root/'usr/local/libexec/pu2pny/oled-502.py'
        text = oled.read_text()
        assert text.count('_crisp_font') == 2 and ('pu2pny32.local' in text) == (arch == 'arm32')
        # render on a fake 64-row and 32-row panel
        mod = importlib.util.module_from_spec(importlib.util.spec_from_loader('o509', loader=None))
        exec(compile(text, 'oled', 'exec'), mod.__dict__)
        from PIL import Image, ImageDraw, ImageFont
        shown = []
        DEFAULT_FONT = ImageFont.load_default()
        class Fake:
            pass
        def make(h):
            f = Fake(); f.Image, f.ImageDraw, f.h = Image, ImageDraw, h
            f.font = DEFAULT_FONT; f.show_image = shown.append
            return f
        os.path.exists(FONT) or sys.exit('font missing for the test')
        real_truetype = ImageFont.truetype
        live = {'active': {'source': 'PU2PNY', 'target': 'TG 724', 'protocol': 'DMR', 'mode': 'rx'}}
        cfg = {'callsign': 'PU2PNY', 'dmr_id': '7241465', 'protocol': 'DMR'}
        f64 = make(64)
        mod._crisp_font.__globals__  # exists
        page, total = mod.render(f64, live, cfg, {})
        assert shown[-1].size == (128, 64) and shown[-1].getbbox() is not None and total >= 2
        assert f64._509_font is not None and f64._509_font[1] >= 12 and len(f64._509_font) == 3
        assert all(v in (0, 255) for v in set(shown[-1].convert('L').tobytes())), 'no grey levels: crisp 1-bit'
        font, pitch, top = f64._509_font
        assert (64 - pitch - 2)//pitch >= 4, 'at least 4 content rows per page'
        assert shown[-1].crop((0, 0, 128, pitch)).getbbox() is not None, 'header drawn'
        f32 = make(32)
        mod.render(f32, live, cfg, {})
        assert f32._509_font is None and shown[-1].size == (128, 32), 'small panels keep the previous drawing'
        # fallback when the font cannot be opened
        ImageFont.truetype = lambda *a, **k: (_ for _ in ()).throw(OSError('no font'))
        try:
            fb = make(64); mod.render(fb, live, cfg, {})
            assert fb._509_font is None and shown[-1].size == (128, 64)
        finally:
            ImageFont.truetype = real_truetype
        # baseline mismatch is refused
        bad = make_root(td + '/bad'); chain(bad, arch, binary)
        (bad/'usr/share/2pny/wizard.html').write_bytes((ROOT/'ci/fixtures/5.03/wizard-5.07.html').read_bytes())
        (bad/'usr/share/2pny/wizard.html').write_text((bad/'usr/share/2pny/wizard.html').read_text() + '\n')
        cp = subprocess.run([sys.executable, '-I', str(ROOT/'ci/patch-image-5.09.py'), str(bad), arch, str(binary)], capture_output=True, text=True)
        assert cp.returncode != 0 and 'unexpected baseline' in cp.stderr

for arch in ('arm64', 'arm32'):
    with tempfile.TemporaryDirectory() as td:
        cp = subprocess.run([sys.executable, str(ROOT/'ci/prepare-5.09-backend.py'), td, arch], capture_output=True, text=True)
        assert cp.returncode == 0, cp.stderr[-500:]
        assert 'appVersion            = "5.09.000"' in (Path(td)/'main.go').read_text()
print('TEST_509_OK')
