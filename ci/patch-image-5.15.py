#!/usr/bin/env python3
"""PU2PNY-OS 5.15 scoped overlays on the four published 5.12.002 P2 filesystems.

5.15 = every 5.14 change + OTA notifier fix (backend) + YSF auto-reconnect
resilience (YSF-515, a systemd drop-in, not an RF-script change) + profile-apply
timing (backend). It does not rewrite RF scripts, the protected hardware probe,
MMDVMHost, gateways or the Nextion baseline.
"""
import shutil
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
BACKUP = '.pre-5.15'


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

    put('etc/2pny/version','5.15.000\n',0o644)
    # YSF-515: keep YSF/C4FM reconnecting to the reflector on its own after a
    # drop, without rewriting the protected RF scripts or the YSFGateway binary.
    # A manual protocol switch uses `systemctl stop`, which Restart=always does
    # not override, so switching away from YSF is unaffected.
    put('etc/systemd/system/2pny-ysfgateway.service.d/515-resilience.conf',
        '[Unit]\nStartLimitIntervalSec=0\n[Service]\nRestart=always\nRestartSec=5\n',0o644)
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
        ('  sed "s/@IFACE@/$ETH/g" /usr/share/2pny/network/dnsmasq-eth.template >"$RUN/dnsmasq-eth.conf"\n',
         '  sed "s/@IFACE@/$ETH/g" /usr/share/2pny/network/dnsmasq-eth.template >"$RUN/dnsmasq-eth.conf"\n  grep -q \'^dhcp-leasefile=\' "$RUN/dnsmasq-eth.conf" || printf \'dhcp-leasefile=%s/dnsmasq-eth.leases\\n\' "$RUN" >>"$RUN/dnsmasq-eth.conf"\n'),
        ('  sed "s/@IFACE@/$AP_WIFI/g" /usr/share/2pny/network/dnsmasq-ap.template >"$RUN/dnsmasq-ap.conf"\n',
         '  sed "s/@IFACE@/$AP_WIFI/g" /usr/share/2pny/network/dnsmasq-ap.template >"$RUN/dnsmasq-ap.conf"\n  grep -q \'^dhcp-leasefile=\' "$RUN/dnsmasq-ap.conf" || printf \'dhcp-leasefile=%s/dnsmasq-ap.leases\\n\' "$RUN" >>"$RUN/dnsmasq-ap.conf"\n'),
        ('AP_ONLINE="-1"\n',
         'AP_ONLINE="-1"\nBOARD_ID="$(cat /etc/2pny/board-id 2>/dev/null || true)"\nAP_HEALTH_LAST=0\nAP_DNS_FAILS=0\nAP_HTTP_FAILS=0\nAP_DNS_RESTART_LAST=0\nAP_HTTP_RESTART_LAST=0\nAP_IP_STATE="unknown"\nAP_DHCP_STATE="unknown"\nAP_DNS_STATE="unknown"\nAP_HTTP_STATE="unknown"\n'),
        ('enable_ap_forwarding(){',
         """ap_udp_bound(){
  local port="$1"
  ss -H -lun "sport = :$port" 2>/dev/null | awk '{print $4}' |
    grep -Eq "^(10\\\\.43\\\\.0\\\\.1|0\\\\.0\\\\.0\\\\.0|\\\\*|\\\\[::\\\\]):$port$"
}
check_ap_health(){
  case "$BOARD_ID" in opizero|nanopineo) ;; *) return 0 ;; esac
  test -n "$AP_WIFI" && alive "$HOSTAPD_PID" || return 0
  local now
  now="$(date +%s)"
  test "$((now - AP_HEALTH_LAST))" -ge 15 || return 0
  AP_HEALTH_LAST="$now"
  if ip -4 -o addr show dev "$AP_WIFI" scope global 2>/dev/null | awk '{print $4}' | grep -Fxq "$SETUP_CIDR"; then
    AP_IP_STATE=active
  else
    ip addr replace "$SETUP_CIDR" dev "$AP_WIFI" >/dev/null 2>&1 || true
    AP_IP_STATE=repairing
    log "AP IPv4 missing on $AP_WIFI; reapplying $SETUP_CIDR"
  fi
  if ap_udp_bound 67; then AP_DHCP_STATE=active; else AP_DHCP_STATE=inactive; fi
  if ap_udp_bound 53; then AP_DNS_STATE=active; else AP_DNS_STATE=inactive; fi
  if test "$AP_DHCP_STATE" = active && test "$AP_DNS_STATE" = active; then
    AP_DNS_FAILS=0
  else
    AP_DNS_FAILS=$((AP_DNS_FAILS+1))
    if test "$AP_DNS_FAILS" -ge 2 && test "$((now - AP_DNS_RESTART_LAST))" -ge 30; then
      AP_DNS_RESTART_LAST="$now"
      log "AP DHCP/DNS socket missing; restarting dnsmasq"
      start_ap_dns || log "AP dnsmasq recovery failed"
      AP_DNS_FAILS=0
    fi
  fi
  if systemctl is-active --quiet 2pnyd.service; then
    if curl --noproxy '*' -fsS --connect-timeout 1 --max-time 2 "http://$SETUP_IP/healthz" 2>/dev/null | grep -q 'PU2PNY OK'; then
      AP_HTTP_STATE=active
      AP_HTTP_FAILS=0
    else
      AP_HTTP_STATE=degraded
      AP_HTTP_FAILS=$((AP_HTTP_FAILS+1))
      if test "$AP_HTTP_FAILS" -ge 3 && test "$((now - AP_HTTP_RESTART_LAST))" -ge 60; then
        AP_HTTP_RESTART_LAST="$now"
        AP_HTTP_FAILS=0
        log "AP HTTP health check failed; restarting 2pnyd.service"
        systemctl --no-block restart 2pnyd.service >/dev/null 2>&1 || true
      fi
    fi
  else
    AP_HTTP_STATE=starting
    systemctl --no-block start 2pnyd.service >/dev/null 2>&1 || true
  fi
}
enable_ap_forwarding(){"""),
        ('    if alive "$DNS_ETH_PID"; then echo \'dnsmasq_eth=active\'; else echo \'dnsmasq_eth=inactive\'; fi\n',
         """    if alive "$DNS_ETH_PID"; then echo 'dnsmasq_eth=active'; else echo 'dnsmasq_eth=inactive'; fi
    echo "board_id=$BOARD_ID"
    case "$BOARD_ID" in
      opizero|nanopineo)
        echo "ap_ipv4=$AP_IP_STATE"
        echo "ap_dhcp=$AP_DHCP_STATE"
        echo "ap_dns=$AP_DNS_STATE"
        echo "ap_http=$AP_HTTP_STATE"
        ;;
      *) echo 'ap_ipv4=not_applicable'; echo 'ap_dhcp=not_applicable'; echo 'ap_dns=not_applicable'; echo 'ap_http=not_applicable' ;;
    esac
"""),
        ('    enable_ap_forwarding\n  fi\n',
         '    enable_ap_forwarding\n    check_ap_health\n  fi\n')

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
</script>
<style id="pny514-css">
/* UI-514: banner/cabecalho responsivo, sem quebrar o painel */
.brand img,.sidebar img,.top img,.brand svg,.sidebar svg{max-width:100%;height:auto;display:block}
.brand{overflow:hidden}
.top{flex-wrap:wrap}
.top h1{overflow-wrap:anywhere}
.badges{flex-wrap:wrap}
@media(max-width:480px){.top h1{font-size:22px}.main{padding-left:13px;padding-right:13px}.brand strong{font-size:18px}}
</style>
<script>
/* WIZ-514: o assistente nunca congela. Se a deteccao automatica falhar ou demorar,
   libera "Ir para configuracao basica" e explica, sem nunca inventar MMDVM nem
   avancar sozinho (o avanco automatico so ocorre quando a MMDVM e confirmada). */
(function(){
  if(window.__pny514)return; window.__pny514=1;
  var seenAt=0, noted=false;
  function addNote(){
    var r=document.getElementById('hardwareResult'); if(!r||noted)return; noted=true;
    var e=document.createElement('div'); e.style.marginTop='8px';
    e.textContent='Voce pode continuar mesmo sem a deteccao automatica. A MMDVM e o display podem ser detectados ou configurados depois.';
    r.appendChild(e);
  }
  setInterval(function(){
    var b=document.getElementById('toBasic'); if(!b)return;
    if(!b.offsetParent){ seenAt=0; return; }
    if(!seenAt) seenAt=Date.now();
    var r=document.getElementById('hardwareResult');
    var cls=r?(r.className||''):'';
    var errored=/error/.test(cls)&&!/hidden/.test(cls);
    if(b.disabled&&(errored||Date.now()-seenAt>35000)){ b.disabled=false; addNote(); }
  },1000);
})();
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
    put('etc/2pny/board-id',(board+'\n').encode(),0o644)
    if board in ('opizero','nanopineo'):
        put('usr/local/sbin/2pny-display-core',(REPO/'src/2pny-display-core-0.3.31.py').read_bytes(),0o755)
        for unit_name in ('2pnyd.service','2pny-network-core.service'):
            unit_path=root/'etc/systemd/system'/unit_name
            if not unit_path.is_file():
                raise RuntimeError(f"missing required board unit: {unit_path}")
            link=root/'etc/systemd/system/multi-user.target.wants'/unit_name
            link.parent.mkdir(parents=True,exist_ok=True)
            expected='../'+unit_name
            valid=False
            if link.is_symlink():
                try: valid=(link.parent/link.readlink()).resolve(strict=True)==unit_path.resolve(strict=True)
                except OSError: valid=False
            elif link.exists():
                raise RuntimeError(f"refusing to replace non-symlink unit enablement: {link}")
            if not valid:
                if link.is_symlink():
                    backup=link.with_name(link.name+BACKUP)
                    if backup.exists(): raise RuntimeError(f"backup already exists: {backup}")
                    link.rename(backup)
                    changed.add(str(backup.relative_to(root)))
                link.symlink_to(expected)
                changed.add(str(link.relative_to(root)))
    return changed
