#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-.}"
cd "$ROOT"

python3 - <<'PY'
from pathlib import Path
root=Path('.')

# Version bump for the next physical test image.
p=root/'builder/build-image.sh'
s=p.read_text().replace('VERSION="${VERSION:-0.1.3-alpha}"','VERSION="${VERSION:-0.1.4-alpha}"')
p.write_text(s)
(root/'rootfs-overlay/etc/2pny/version').write_text('0.1.4-alpha\n')

p=root/'rootfs-overlay/usr/local/sbin/2pny-firstboot'
s=p.read_text().replace('0.1.3-alpha','0.1.4-alpha')
p.write_text(s)

p=root/'src/2pnyd/main.go'
s=p.read_text()
s=s.replace('appVersion      = "0.1.3-alpha"','appVersion      = "0.1.4-alpha"')
s=s.replace('Alpha 0.1.3','Alpha 0.1.4')

marker='2pny-theme-bootstrap'
if marker not in s:
    head=r'''<meta name="color-scheme" content="dark light">
<script id="2pny-theme-bootstrap">(function(){var t=localStorage.getItem('2pny-theme')||'dark';document.documentElement.setAttribute('data-theme',t);})();</script>
<style id="2pny-modern-ui">
:root{color-scheme:dark;--pny-bg:#0b0f14;--pny-surface:#111821;--pny-surface2:#17212d;--pny-line:#263446;--pny-text:#eef4fb;--pny-muted:#9aabc0;--pny-accent:#4db2ff;--pny-ok:#42d392;--pny-warn:#f5c451;--pny-danger:#ff6b7a;--pny-shadow:0 18px 48px rgba(0,0,0,.28)}
html[data-theme="light"]{color-scheme:light;--pny-bg:#f3f6fa;--pny-surface:#ffffff;--pny-surface2:#edf2f7;--pny-line:#d5dee9;--pny-text:#101722;--pny-muted:#5f6f82;--pny-accent:#0877c9;--pny-ok:#087f5b;--pny-warn:#9a6700;--pny-danger:#c92a2a;--pny-shadow:0 14px 36px rgba(34,52,73,.10)}
*{box-sizing:border-box}html{background:var(--pny-bg)!important}body{background:var(--pny-bg)!important;color:var(--pny-text)!important;min-height:100vh;transition:background .18s ease,color .18s ease}body,button,input,select,textarea{font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif!important}a{color:var(--pny-accent)!important}.card,.panel,section,.box,main>div{border-color:var(--pny-line)!important}.card,.panel,section{background:var(--pny-surface)!important;box-shadow:var(--pny-shadow)!important}h1,h2,h3,strong,b,label{color:var(--pny-text)!important}p,small,.muted{color:var(--pny-muted)!important}input,select,textarea{background:var(--pny-surface2)!important;color:var(--pny-text)!important;border:1px solid var(--pny-line)!important;border-radius:10px!important;outline:none}input:focus,select:focus,textarea:focus,button:focus-visible{border-color:var(--pny-accent)!important;box-shadow:0 0 0 3px color-mix(in srgb,var(--pny-accent) 25%,transparent)!important}button{border-radius:10px!important;transition:transform .12s ease,opacity .12s ease,background .12s ease}button:hover{transform:translateY(-1px)}
#pny-ui-bar{position:fixed;z-index:9999;right:16px;top:14px;display:flex;gap:8px;align-items:center;background:color-mix(in srgb,var(--pny-surface) 94%,transparent);border:1px solid var(--pny-line);border-radius:14px;padding:7px 8px;box-shadow:var(--pny-shadow);backdrop-filter:blur(12px)}#pny-ui-bar .pny-dot{width:8px;height:8px;border-radius:50%;background:var(--pny-ok);box-shadow:0 0 0 4px color-mix(in srgb,var(--pny-ok) 14%,transparent)}#pny-ui-bar span{font-size:12px;color:var(--pny-muted)}#pny-theme-toggle{border:1px solid var(--pny-line)!important;background:var(--pny-surface2)!important;color:var(--pny-text)!important;padding:7px 10px!important;font-weight:700!important;cursor:pointer}
.pny-status-chip{display:inline-flex;align-items:center;gap:7px;padding:7px 10px;border:1px solid var(--pny-line);border-radius:999px;background:var(--pny-surface2);font-size:12px;color:var(--pny-muted)}.pny-status-chip:before{content:"";width:7px;height:7px;border-radius:50%;background:var(--pny-ok)}
@media(max-width:760px){#pny-ui-bar{top:8px;right:8px}.container,main{padding-left:14px!important;padding-right:14px!important}.card,.panel,section{border-radius:14px!important}}
@media(prefers-reduced-motion:reduce){*,*:before,*:after{scroll-behavior:auto!important;transition:none!important;animation:none!important}}
</style>'''
    s=s.replace('</head>',head+'\n</head>')

    body=r'''<script id="2pny-theme-runtime">(function(){function label(){var b=document.getElementById('pny-theme-toggle');if(!b)return;var t=document.documentElement.getAttribute('data-theme')||'dark';b.textContent=t==='dark'?'☀ Claro':'☾ Escuro';b.setAttribute('aria-label',t==='dark'?'Ativar tema claro':'Ativar tema escuro')}function boot(){if(document.getElementById('pny-ui-bar'))return;var bar=document.createElement('div');bar.id='pny-ui-bar';bar.innerHTML='<i class="pny-dot" aria-hidden="true"></i><span>2PNY local</span><button id="pny-theme-toggle" type="button"></button>';document.body.appendChild(bar);document.getElementById('pny-theme-toggle').onclick=function(){var cur=document.documentElement.getAttribute('data-theme')||'dark';var next=cur==='dark'?'light':'dark';document.documentElement.setAttribute('data-theme',next);localStorage.setItem('2pny-theme',next);label()};label();document.querySelectorAll('[class*="chip"],[class*="badge"]').forEach(function(el){if(!el.classList.contains('pny-status-chip'))el.classList.add('pny-status-chip')})}if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot);else boot()})();</script>'''
    s=s.replace('</body>',body+'\n</body>')

p.write_text(s)

v=root/'builder/validate-source.sh'
vs=v.read_text()
checks='''\ngrep -q '2pny-theme-bootstrap' src/2pnyd/main.go\ngrep -q 'pny-theme-toggle' src/2pnyd/main.go\ngrep -q 'localStorage.getItem' src/2pnyd/main.go\ngrep -q '0.1.4-alpha' src/2pnyd/main.go\n'''
if "grep -q '2pny-theme-bootstrap'" not in vs:
    vs += checks
v.write_text(vs)
PY

gofmt -w src/2pnyd/main.go
chmod +x builder/build-image.sh builder/validate-source.sh rootfs-overlay/usr/local/sbin/2pny-firstboot

echo "2PNY 0.1.4 dark-first professional UI module applied"
