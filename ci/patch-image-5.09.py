#!/usr/bin/env python3
"""Offline 5.09 overlay on the published 5.08 image.

WIZ-059: "Salvando e ativando" no longer aborts after 15 s; an aborted wait falls through to the real
state poll of /api/rf (the radio kept activating while the page showed "signal is aborted").
DISPLAY-059: 64-pixel OLED text is drawn at native size with DejaVu Sans Mono Bold 12 (no stretching to 9 px);
32-pixel panels keep the previous drawing. Never touches RF, MMDVMHost, DMRGateway, NextionDriver or the apply scripts.
"""
import shutil
import sys
from pathlib import Path

root, arch, binary = Path(sys.argv[1]).resolve(), sys.argv[2], Path(sys.argv[3]).resolve()
repo = Path(__file__).resolve().parents[1]
fix = repo/'ci/fixtures/5.03'
assert arch in ('arm32', 'arm64')
assert root != Path('/') and (root/'etc/2pny/version').read_text().strip() == '5.08.000'
assert binary.is_file() and binary.stat().st_size > 1000000
SUFFIX = '.pre-5.09'
backed = set()


def backup(path):
    if path in backed:
        return
    src, dst = root/path, root/(path + SUFFIX)
    assert src.is_file() and not dst.exists()
    shutil.copy2(src, dst)
    backed.add(path)


def replace(path, old, new, count=1):
    p = root/path
    text = p.read_text()
    assert text.count(old) == count, (path, old[:70], text.count(old))
    p.write_text(text.replace(old, new))


# daemon (only the version string changes)
backup('usr/local/bin/2pnyd')
shutil.copyfile(binary, root/'usr/local/bin/2pnyd')
(root/'usr/local/bin/2pnyd').chmod(0o755)

wizard = 'usr/share/2pny/wizard.html'
assert (root/wizard).read_bytes() == (fix/'wizard-5.07.html').read_bytes(), 'unexpected baseline: ' + wizard
backup(wizard)
replace(wizard, 'timer=setTimeout(()=>ctl.abort(),15000);', 'timer=setTimeout(()=>ctl.abort(),(opt&&opt.timeout)||15000);')
replace(wizard, "    await getj('/api/basic/apply',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});\n",
        "    try{await getj('/api/basic/apply',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data),timeout:150000})}\n"
        "    catch(e){if(!(e&&e.name==='AbortError'))throw e}  // WIZ-059: the radio keeps activating; the poll below reports the real state\n")

oled = 'usr/local/libexec/pu2pny/oled-502.py'
backup(oled)
replace(oled, "def render(self, live, cfg, tel):\n",
        "def _crisp_font(self):\n"
        "    # DISPLAY-059: native-size TrueType text on panels with at least 48 rows; None keeps the old drawing.\n"
        "    cached = getattr(self, '_509_font', 0)\n"
        "    if cached == 0:\n"
        "        cached = None\n"
        "        if self.h >= 48:\n"
        "            try:\n"
        "                from PIL import ImageFont\n"
        "                font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf', 12)\n"
        "                box = font.getbbox('Ag')\n"
        "                cached = (font, box[3] - box[1], box[1])\n"
        "            except Exception:\n"
        "                cached = None\n"
        "        self._509_font = cached\n"
        "    return cached\n\n"
        "def render(self, live, cfg, tel):\n")
replace(oled, "    content = fit_rows(rows(live, cfg, network_status()), self.font)\n    capacity = max(1, (self.h-12)//10)\n",
        "    crisp = _crisp_font(self)\n"
        "    content = fit_rows(rows(live, cfg, network_status()), crisp[0] if crisp else self.font)\n"
        "    capacity = max(1, (self.h-crisp[1]-3)//crisp[1]) if crisp else max(1, (self.h-12)//10)\n")
replace(oled, "    line(header, 1)\n    for index, text in enumerate(content[page*capacity:(page+1)*capacity]):\n        line(text, 12+index*10)\n",
        "    if crisp:\n"
        "        draw = self.ImageDraw.Draw(image)\n"
        "        draw.text((2, 1-crisp[2]), header, font=crisp[0], fill=255)\n"
        "        draw.line((0, crisp[1]+1, 127, crisp[1]+1), fill=255)\n"
        "        for index, text in enumerate(content[page*capacity:(page+1)*capacity]):\n"
        "            draw.text((2, crisp[1]+3+index*crisp[1]-crisp[2]), text, font=crisp[0], fill=255)\n"
        "        self.show_image(image)\n"
        "        return page, total\n"
        "    line(header, 1)\n    for index, text in enumerate(content[page*capacity:(page+1)*capacity]):\n        line(text, 12+index*10)\n")
compile((root/oled).read_bytes(), oled, 'exec')
(root/'etc/2pny/version').write_text('5.09.000\n')
print('PATCH_509_OFFLINE_OK', arch)
