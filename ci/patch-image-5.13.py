#!/usr/bin/env python3
"""Scoped overlays on the four published 5.12.002 P2 filesystems."""
import shutil
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
BACKUP = '.pre-5.13'


def apply(root, board, backend):
    root = Path(root).resolve()
    assert root != Path('/') and board in ('32','64','opizero','nanopineo')
    assert (root/'etc/2pny/version').read_text().strip() == '5.12.002'
    changed = set()

    def put(relative, data, mode=None):
        path = root/relative
        assert not path.is_symlink(), relative
        if path.is_file():
            backup = path.with_name(path.name + BACKUP)
            assert not backup.exists() and not backup.is_symlink(), backup
            shutil.copy2(path,backup)
            changed.add(relative + BACKUP)
        assert not path.exists() or path.is_file(), relative
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_bytes(data.encode() if isinstance(data,str) else data)
        if mode is not None:
            path.chmod(mode)
        changed.add(relative)

    def edit(relative, replacements):
        source = (root/relative).read_text()
        for old,new in replacements:
            assert source.count(old) == 1, (relative,old,source.count(old))
            source = source.replace(old,new,1)
        if relative.endswith(('.py','/2pny-display-apply','/2pny-rf-access','/2pny-rf-access-request')):
            compile(source,relative,'exec')
        put(relative,source)

    put('etc/2pny/version','5.13.002\n',0o644)
    put('usr/local/bin/2pnyd',Path(backend).read_bytes(),0o755)
    previous = root/'usr/local/sbin/2pny-timezone-apply'
    assert previous.read_bytes() == (REPO/'runtime/5.08/tz-apply.py').read_bytes()
    put(str(previous.relative_to(root)),(REPO/'runtime/5.13/tz-apply.py').read_bytes(),0o755)
    units = 'etc/systemd/system/'
    put(units+'2pny-timezone-restore.service.d/65-consumers.conf',
        '[Unit]\nBefore=2pnyd.service 2pny-display.service 2pny-display-reconcile.service\n',0o644)
    put('etc/systemd/timesyncd.conf.d/65-pu2pny-clock.conf',
        '[Time]\nNTP=time.google.com time1.google.com time2.google.com time3.google.com\nFallbackNTP=pool.ntp.org\n',0o644)

    # The first-access AP never uses upstream DNS. Use the same predicate in
    # the steady-state loop so DHCP/DNS doesn't restart on every pass with an uplink.
    edit('usr/local/sbin/2pny-network-core',[
        ('test -n "$outif" && test "$outif" != "$AP_WIFI" && now=1',
         'test -f "$STATE/provisioned" && test -n "$outif" && test "$outif" != "$AP_WIFI" && now=1'),
        ("\nif nmcli -t -f NAME connection show 2>/dev/null | grep -Fxq 'PU2PNY-WIFI'; then",
         """
try_secondary_wifi(){
  local iface="$1" ssid
  ssid="$(nmcli --escape no -g 802-11-wireless.ssid connection show PU2PNY-WIFI-SECONDARY 2>/dev/null | head -1 || true)"
  test -n "$ssid" && test -n "$iface" || return 1
  timeout -k 2 26 /usr/bin/nmcli --wait 22 connection up PU2PNY-WIFI-SECONDARY ifname "$iface" >/dev/null 2>&1 &&
    wifi_profile_link_ok "$iface" "$ssid" || return 1
  SECONDARY_SSID="$ssid"
}
if nmcli -t -f NAME connection show 2>/dev/null | grep -Fxq 'PU2PNY-WIFI'; then"""),
        ('  if test "$WIFI_BOOT_OK" != 1; then\n',
         """  if test "$WIFI_BOOT_OK" != 1 && try_secondary_wifi "$SAVED_IF"; then
    WIFI_BOOT_OK=1
    touch "$STATE/ap-disabled"
    rm -f "$STATE/ap-auto-disabled" "$STATE/wifi-pending"
    write_connect_state connected "Rede Wi-Fi 2 conectada." "$SECONDARY_SSID"
    /usr/local/sbin/2pny-mdns-guard >/dev/null 2>&1 || true
  fi
  if test "$WIFI_BOOT_OK" != 1; then
"""),
        ('            if timeout -k 2 35 /usr/bin/nmcli --wait 30 connection up PU2PNY-WIFI >/dev/null 2>&1 && wifi_profile_link_ok "$AP_WIFI" "$SAVED_SSID"; then',
         """            RECOVERED_SSID="$SAVED_SSID"
            recover_wifi(){
              if timeout -k 2 35 /usr/bin/nmcli --wait 30 connection up PU2PNY-WIFI >/dev/null 2>&1 && wifi_profile_link_ok "$AP_WIFI" "$SAVED_SSID"; then
                return 0
              fi
              if try_secondary_wifi "$AP_WIFI"; then RECOVERED_SSID="$SECONDARY_SSID"; return 0; fi
              return 1
            }
            if recover_wifi; then"""),
        ('write_connect_state connected "Wi-Fi salvo reconectado." "$SAVED_SSID"',
         'write_connect_state connected "Wi-Fi salvo reconectado." "$RECOVERED_SSID"'),
    ])
    profiles = 'usr/local/sbin/2pny-wifi-profiles'
    source = (root/profiles).read_text()
    start = source.index('save_secondary(){')
    end = source.index('scan_signal(){',start)
    edit(profiles,[
        (source[start:end], (REPO/'runtime/5.13/wifi-secondary.sh').read_text()),
        ('nm -g 802-11-wireless.ssid connection show', 'nm --escape no -g 802-11-wireless.ssid connection show'),
        ('exec 9>"$LOCK"; flock -w 35 9',
         'lock_wait=35\nif test "${1:-}" = save-secondary; then lock_wait=8; fi\nexec 9>"$LOCK"; flock -w "$lock_wait" 9'),
        ('nm -m multiline --escape no -f SSID,SIGNAL', 'nm -t -m multiline --escape no -f SSID,SIGNAL'),
        ('  if test "$current" != "$chosen"; then nm --wait 18 connection up "$chosen" ifname "$iface" >/dev/null; fi',
         """  if test "$current" != "$chosen" && test "$best_sig" -ge 0; then
    if ! nm --wait 18 connection up "$chosen" ifname "$iface" >/dev/null 2>&1 ||
        test -z "$(active_ip)" || test "$(active_ssid)" != "$(profile_ssid "$chosen")"; then
      if test -n "$current"; then nm --wait 18 connection up "$current" ifname "$iface" >/dev/null 2>&1 || true; fi
      echo "A segunda rede não confirmou associação e IPv4." >&2
      return 5
    fi
  fi"""),
    ])
    if board in ('opizero','nanopineo'):
        # Keep the HTTP service eligible to recover from transient Armbian startup failures.
        edit(units+'2pnyd.service.d/62-board-portal.conf',[
            ('StartLimitIntervalSec=300\nStartLimitBurst=8','StartLimitIntervalSec=0'),
            ('RestartSec=4','RestartSec=15'),
        ])

    edit('usr/local/libexec/pu2pny/2pny-rf-access-request',[
        ('import importlib.util','import importlib.machinery\nimport importlib.util'),
        ('        spec = importlib.util.spec_from_file_location("rfaccess", SRC)',
         """        # The installed helper is executable Python without a .py suffix.
        loader = importlib.machinery.SourceFileLoader("rfaccess", str(SRC))
        spec = importlib.util.spec_from_loader(loader.name, loader)"""),
    ])
    edit('usr/local/libexec/pu2pny/2pny-rf-access',[
        ('def atomic_write(target: Path, data: bytes, mode: int) -> None:',
         'def atomic_write(target: Path, data: bytes, mode: int, owner=None) -> None:'),
        ('        os.chmod(path, mode)\n        os.replace(path, target)',
         """        if owner is not None:
            os.chown(path, *owner)
        os.chmod(path, mode)
        os.replace(path, target)"""),
        ('        snapshot = state.with_suffix(".rollback.ini")','        owner = (stat.st_uid, stat.st_gid)\n        snapshot = state.with_suffix(".rollback.ini")'),
        ('atomic_write(ini, updated.encode("utf-8"), stat.st_mode & 0o777)',
         'atomic_write(ini, updated.encode("utf-8"), stat.st_mode & 0o777, owner)'),
        ('atomic_write(ini, original, stat.st_mode & 0o777)',
         'atomic_write(ini, original, stat.st_mode & 0o777, owner)'),
    ])
    put(units+'2pny-display-reconcile.service.d/65-persisted.conf',
        '[Unit]\nConditionPathExists=\n'
        'ConditionPathExists=|/var/lib/2pny/display-settings.json\n'
        'ConditionPathExists=|/var/lib/2pny/display-override.json\n',0o644)
    edit('usr/local/sbin/2pny-display-apply',[
        ("    driver['Nextion'] = {'ScreenLayout': str(layout)}",
         """    driver['Nextion'] = {'ScreenLayout': str(layout)}
    # ON7LDS reads frequencies from [Info], while MMDVM-Host MQTT stores them in [Modem].
    driver['Info'] = {}
    for key in ('RXFrequency', 'TXFrequency'):
        value = host.get('Modem', key, fallback='')
        if value.isascii() and value.isdecimal() and 0 < int(value) < 2**32:
            driver['Info'][key] = value
    # Only mode flags are carried into the display-only configuration.
    for section in ('D-Star', 'DMR', 'System Fusion', 'P25', 'NXDN', 'POCSAG', 'M17',
                    'D-Star Network', 'DMR Network', 'System Fusion Network',
                    'P25 Network', 'NXDN Network', 'M17 Network'):
        enabled = host.get(section, 'Enable', fallback='')
        if enabled in ('0', '1'):
            driver[section] = {'Enable': enabled}"""),
        ("    if (saved.get('enabled') is True and saved.get('type') == 'nextion_mmdvm'\n"
         "            and saved.get('requested_layout') in (3, 4)):",
         """    profile = override if override.get('enabled') is True else saved
    layout = profile.get('layout', profile.get('requested_layout'))
    if (profile.get('enabled') is True and profile.get('type') == 'nextion_mmdvm'
            and layout in (0, 2, 3, 4)):"""),
        ("            ov = {**ov, 'layout': saved['requested_layout'], 'enabled': saved.get('enabled', True)}",
         """            ov = {**ov, 'layout': saved['requested_layout'], 'enabled': saved.get('enabled', True),
                  'model_profile': saved.get('model_profile', 'auto'),
                  'resolution': saved.get('resolution', '')}"""),
        ("                    'physical_confirmed': d.get('physical_confirmed') is True}",
         """                    'physical_confirmed': d.get('physical_confirmed') is True,
                    'model_profile': ov.get('model_profile', 'auto'), 'resolution': ov.get('resolution', '')}"""),
    ])
    edit('usr/local/libexec/pu2pny/oled-502.py',[
        ('import shutil', 'import json\nimport shutil'),
        ("TEMP = Path('/sys/class/thermal/thermal_zone0/temp')",
         """TEMP = Path('/sys/class/thermal/thermal_zone0/temp')
OLED_CONFIG = Path('/var/lib/2pny/oled.json')


def rotate_oled(image, path=OLED_CONFIG):
    try:
        settings = json.loads(path.read_text())
    except (OSError, ValueError):
        return image
    if isinstance(settings, dict) and settings.get('rotation') == 180:
        return image.rotate(180)
    return image"""),
        ('    self.show_image(image)','    self.show_image(rotate_oled(image))'),
    ])

    ui = 'usr/share/2pny/'
    common = root/(ui+'ui-common-0.3.0.js')
    source = common.read_text()
    start = source.index('      if(!clockAutoTZTried)')
    end = source.index('    renderClock()',start)
    edit(ui+'ui-common-0.3.0.js',[
        (source[start:end],"""      if(!clockAutoTZTried && !(s.clock_settings||{}).timezone){
        var zone=Intl.DateTimeFormat().resolvedOptions().timeZone;
        if(zone){
          clockAutoTZTried=true;
          getj('/api/clock/browser',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({timezone:zone,epoch_ms:Date.now()}),pnySilent:true},21000)
            .then(function(){setTimeout(syncClock,300)}).catch(function(){clockAutoTZTried=false});
        }
      }
    }catch(e){}
"""),
        ('if(clockDSTManual)ms+=3600000;var d=new Date(ms);','var d=new Date(ms+(clockDSTManual?3600000:0));'),
        ("if(u)u.textContent=d.toISOString()", "if(u)u.textContent=new Date(ms).toISOString()"),
    ])
    system = (root/(ui+'system.html')).read_text()
    start = system.index('<script>// CLOCK-056:')
    end = system.index('</script>',start)+len('</script>')
    edit(ui+'system.html',[
        (system[start:end],''),
        ("PNY.q('dstManual').onchange=applyAutomaticClock;",
         """PNY.q('dstManual').onchange=async function(){
  try{await action('dst-display',{dst_manual:this.checked},21000);await load()}
  catch(e){PNY.q('timeResult').textContent=e.message;await load()}
};"""),
        ('var d=new Date(Date.now()+serverDelta+dstDisplay);',
         'var utc=Date.now()+serverDelta,d=new Date(utc+dstDisplay);'),
        ("PNY.q('utcClock').textContent=d.toISOString()", "PNY.q('utcClock').textContent=new Date(utc).toISOString()"),
    ])
    wizard = (root/(ui+'wizard.html')).read_text()
    assert wizard.count('</body>') == 1
    edit(ui+'wizard.html',[
        ('</body>',"""<script>
try{
  var zone=Intl.DateTimeFormat().resolvedOptions().timeZone;
  if(zone)fetch('/api/clock/browser',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({timezone:zone,epoch_ms:Date.now()})}).catch(function(){});
}catch(_){}
</script></body>"""),
    ])
    internet = (root/(ui+'internet.html')).read_text()
    start = internet.index('async function followSecondaryToLive(')
    end = internet.index("PNY.q('wifiSavePrimary')",start)
    secondary = next(line for line in internet.splitlines() if line.startswith("PNY.q('wifiSaveSecond').onclick="))
    edit(ui+'internet.html',[
        (internet[start:end], ''),
        (secondary, """PNY.q('wifiSaveSecond').onclick=async function(){
  var button=this,select=PNY.q('wifiSecondSelect'),option=select.options[select.selectedIndex];
  var manual=PNY.q('wifiSecondManual').value,ssid=manual||select.value,bssid=manual?'':(option?option.dataset.bssid||'':'');
  var result=PNY.q('wifiProfileResult');
  if(!ssid.trim()){result.textContent=PNYT('Busque uma rede ou informe o SSID manualmente.');return}
  button.disabled=true;
  var op=PNY.operation('Salvando Rede Wi‑Fi 2','Validando o perfil sem alterar a Rede Wi‑Fi 1...');
  try{
    await PNY.getj('/api/network/wifi/profiles',{method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({action:'save-secondary',ssid:ssid,password:PNY.q('wifiSecondPass').value,bssid:bssid})},90000);
    PNY.q('wifiSecondPass').value='';
    PNY.q('wifiSecondManual').value='';
    result.textContent=PNYT('Rede de backup salva.');
    op.done(result.textContent);
    await loadProfiles();
  }catch(e){result.textContent=e.message;op.error(e.message)}
  finally{button.disabled=false}
};""".replace("PNYT(", "(window.PNYT||String)(")),
    ])
    edit(ui+'expert.html',[
        ('<button class="btn primary" id="oledSave"',
         '''<label for="oledRotation"><span id="oledRotationLabel"></span><select id="oledRotation">
<option value="0">0°</option><option value="180">180°</option></select></label>
<button class="btn primary" id="oledSave"'''),
        (" if(!$('oledSave'))return;",
         """ if(!$('oledSave'))return;
 $('oledRotationLabel').textContent=({pt:'Rotação OLED',en:'OLED rotation',es:'Rotación OLED'})[document.documentElement.lang.slice(0,2)]||'Rotação OLED';"""),
        ("  if(c&&c.type){$('oledType').value=c.type}",
         """  if(c&&c.type){$('oledType').value=c.type}
  $('oledRotation').value=c&&c.rotation===180?'180':'0';"""),
        ('body={type:type};','body={type:type,rotation:Number($(\'oledRotation\').value)};'),
    ])
    return changed
