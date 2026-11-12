#!/usr/bin/env python3
"""Overlay 5.11; backups e âncoras verificadas, sem alterar RF ou fluxo ON7LDS."""
import os
import shutil
import sys
from pathlib import Path

root, arch, binary = Path(sys.argv[1]).resolve(), sys.argv[2], Path(sys.argv[3]).resolve()
repo = Path(__file__).resolve().parents[1]
assert arch in ('arm32', 'arm64') and root != Path('/')
assert (root/'etc/2pny/version').read_text().strip() == '5.10.000'
assert binary.stat().st_size > 1000000
backed = set()

def backup(path):
    if path in backed:
        return
    src, dst = root/path, root/(path+'.pre-5.11')
    assert src.is_file() and not dst.exists(), path
    shutil.copy2(src, dst)
    backed.add(path)

def replace(path, old, new):
    p = root/path
    text = p.read_text()
    assert text.count(old) == 1, (path, old[:90], text.count(old))
    backup(path)
    p.write_text(text.replace(old, new, 1))

def install(path, source, mode=0o755):
    p = root/path
    if p.exists():
        backup(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(source, Path):
        shutil.copyfile(source, p)
    else:
        p.write_text(source)
    p.chmod(mode)

install('usr/local/bin/2pnyd', binary)
# PERF-511: EOF, seguidor único e telemetria espaçada, preservando ingestão/histórico.
worker = 'usr/local/sbin/2pny-station-worker'
install('usr/local/libexec/pu2pny/followers-511.py', repo/'runtime/5.11/followers.py')
start = (root/worker).read_text().index('    hostlog=start_follow(')
end = (root/worker).read_text().index('    pool=concurrent.futures.', start)
anchor = (root/worker).read_text()[start:end]
replace(worker, anchor,
        '    from importlib.machinery import SourceFileLoader\n'
        '    Followers=SourceFileLoader("followers511","/usr/local/libexec/pu2pny/followers-511.py").load_module().Followers\n'
        '    journal=["journalctl","-b","-f","-n","0","-o","json","-u","2pny-mmdvmhost.service"]\n'
        '    for unit in gateway_units:journal.extend(["-u",unit])\n'
        '    sel=Followers({"journal":journal,"mqtt":["mosquitto_sub","-h","127.0.0.1","-t","host/json","-t","dmr-gateway/json","-v"]})\n')
replace(worker, 'sel.select(timeout=0.10)', 'sel.select(timeout=1.0)')
replace(worker, '                msg,ts=decode_journal(raw);event=state.ingest(msg,ts,gateway=gateway)',
        '                try:unit=json.loads(raw).get("_SYSTEMD_UNIT", "")\n'
        '                except (ValueError,TypeError):unit=""\n'
        '                gateway=unit in gateway_units\n'
        '                msg,ts=decode_journal(raw);event=state.ingest(msg,ts,gateway=gateway)')
replace(worker, 'next_probe=now+(1.0 if any(state.active.values()) else 5.0)',
        'next_probe=now+(2.0 if any(state.active.values()) else 30.0)')
replace(worker, 'telem_interval=3 if any(state.active.values()) else 15',
        'telem_interval=5 if any(state.active.values()) else 30')
# NET-511: checagem pesada a cada 4 ciclos; carrier permanece em 3s.
net = 'usr/local/sbin/2pny-network-core'
replace(net, 'elif test "$NOW_CARRIER" = 1 && test "$ETH_MODE" = dhcp && ! has_global_v4', 'elif test "$NOW_CARRIER" = 1 && test "$ETH_MODE" = dhcp && test "$HEAVY_TICK" = 0 && ! has_global_v4')
replace(net, '      LAST_CARRIER="$NOW_CARRIER"\n', '      LAST_CARRIER="$NOW_CARRIER"\n      HEAVY_TICK=0\n')
replace(net, '    WIFI_MISS_COUNT=0\n    touch "$STATE/ap-disabled"', '    WIFI_MISS_COUNT=0\n    test -f "$STATE/ap-disabled" || touch "$STATE/ap-disabled"')
replace(net, 'connection.autoconnect-retries 3', 'connection.autoconnect-retries 0')
replace(net, 'WIFI_MISS_COUNT=0\nwifi_profile_link_ok()',
        'WIFI_MISS_COUNT=0\nHEAVY_TICK=0\nRECOVERY_DUE=120\nRECOVERY_DELAY=120\nwifi_profile_link_ok()')
replace(net, '  ACTIVE_CLIENT="$(active_wifi)"\n', '  if test "$HEAVY_TICK" = 0; then\n  ACTIVE_CLIENT="$(active_wifi)"\n')
replace(net, 'WIFI_MISS_COUNT" -ge 15', 'WIFI_MISS_COUNT" -ge 4')
replace(net, '  # Recover stale holds only after', '  fi\n  # Recover stale holds only after')
replace(net, '  maybe_maintenance\n  write_status\n  sleep 3',
        '  # NET-511: cliente do AP ou operação manual impedem a retentativa.\n'
        '  if test "$HEAVY_TICK" = 0; then\n'
        '    if alive "$HOSTAPD_PID" && test ! -f "$SCAN_HOLD" && test -f "$STATE/provisioned" && test "$SECONDS" -ge "$RECOVERY_DUE"; then\n'
        '      if nmcli -t -f NAME connection show 2>/dev/null | grep -Fxq PU2PNY-WIFI; then\n'
        '        if STATIONS="$(iw dev "$AP_WIFI" station dump 2>/dev/null)" && test -z "$STATIONS"; then\n'
        '          exec 9>"$RUN/wifi-operation.lock"\n'
        '          if flock -n 9; then\n'
        '            stop_ap\n'
        '            nmcli device set "$AP_WIFI" managed yes >/dev/null 2>&1 || true\n'
        '            if timeout -k 2 35 /usr/bin/nmcli --wait 30 connection up PU2PNY-WIFI >/dev/null 2>&1 && wifi_profile_link_ok "$AP_WIFI" "$SAVED_SSID"; then\n'
        '              touch "$STATE/ap-disabled"\n'
        '              rm -f "$STATE/ap-auto-disabled"\n'
        '              write_connect_state connected "Wi-Fi salvo reconectado." "$SAVED_SSID"\n'
        '              RECOVERY_DELAY=120\n'
        '            else\n'
        '              start_ap || log "falha ao restaurar AP de recuperação"\n'
        '              RECOVERY_DELAY=$((RECOVERY_DELAY*2))\n'
        '              test "$RECOVERY_DELAY" -le 300 || RECOVERY_DELAY=300\n'
        '            fi\n'
        '            flock -u 9\n'
        '          fi\n'
        '        fi\n'
        '      fi\n'
        '      RECOVERY_DUE=$((SECONDS+RECOVERY_DELAY))\n'
        '    fi\n'
        '    maybe_maintenance\n'
        '    write_status\n'
        '  fi\n'
        '  HEAVY_TICK=$(( (HEAVY_TICK+1)%4 ))\n'
        '  sleep 3')
# Hostname ARM64: mesmos pontos da HOST-057, substituição por ocorrência única.
if arch == 'arm64':
    for path in ('usr/share/2pny/wizard.html', 'usr/share/2pny/internet.html',
                 'usr/share/2pny/network/dnsmasq-ap.template', 'etc/NetworkManager/dnsmasq-shared.d/2pny-captive.conf',
                 'etc/NetworkManager/dispatcher.d/90-pu2pny-mdns', net, 'usr/local/sbin/2pny-mdns-guard',
                 'usr/local/libexec/pu2pny/lcd-504.py'):
        text=(root/path).read_text()
        assert 'pu2pny.local' in text, path
        backup(path)
        # Cada âncora é a linha completa e precisa ocorrer uma vez.
        for line in list(dict.fromkeys(l for l in text.splitlines(True) if 'pu2pny.local' in l)):
            replace(path, line, line.replace('pu2pny.local', 'pu2pny64.local'))
    replace('usr/local/sbin/2pny-mdns-alias', '-f 2pny.local "$ip"', '-f 2pny64.local "$ip"')
    install('etc/hostname', 'pu2pny64\n', 0o644)
    replace('etc/hosts', '127.0.1.1\tpu2pny\n', '127.0.1.1\tpu2pny64\n')
    replace('etc/avahi/avahi-daemon.conf', 'host-name=pu2pny\n', 'host-name=pu2pny64\n')
# BOOT-511: avahi atômico e idempotente.
guard = 'usr/local/sbin/2pny-mdns-guard'
host = 'pu2pny32' if arch == 'arm32' else 'pu2pny'
newhost = 'pu2pny32' if arch == 'arm32' else 'pu2pny64'
replace(guard, f'hostnamectl set-hostname {host} >/dev/null 2>&1 || true\nprintf \'{host}\\n\' >/etc/hostname',
        f'CHANGED=0\nif test "$(cat /proc/sys/kernel/hostname)" != {newhost}; then\n  hostnamectl set-hostname {newhost} >/dev/null 2>&1 || true\n  CHANGED=1\nfi\n'
        f'if test "$(cat /etc/hostname)" != {newhost}; then printf \'{newhost}\\n\' >/etc/hostname; CHANGED=1; fi\n'
        'BEFORE="$(sha256sum /etc/avahi/avahi-daemon.conf 2>/dev/null || true)"')
if arch == 'arm64':
    replace(guard, '("host-name","pu2pny")', '("host-name","pu2pny64")')
replace(guard, 'p.write_text("\\n".join(lines)+"\\n")',
        'new="\\n".join(lines)+"\\n"\nif p.read_text()!=new:\n    import os,tempfile\n    fd,tmp=tempfile.mkstemp(prefix=".avahi-",dir=p.parent)\n    with os.fdopen(fd,"w") as out:out.write(new)\n    os.chmod(tmp,0o644);os.replace(tmp,p)')
replace(guard, "cat >/etc/avahi/services/pu2pny-http.service <<'EOF'", 'TMP="$(mktemp /etc/avahi/services/.pu2pny-http.XXXXXX)"\ntrap \'rm -f "$TMP"\' EXIT\ncat >"$TMP" <<\'EOF\'')
replace(guard, 'systemctl restart avahi-daemon.service >/dev/null 2>&1 || true',
        'if ! cmp -s "$TMP" /etc/avahi/services/pu2pny-http.service; then\n'
        '  chmod 0644 "$TMP"; mv "$TMP" /etc/avahi/services/pu2pny-http.service; CHANGED=1\nfi\n'
        'AFTER="$(sha256sum /etc/avahi/avahi-daemon.conf 2>/dev/null || true)"\n'
        'if test "$CHANGED" = 1 || test "$BEFORE" != "$AFTER"; then systemctl restart avahi-daemon.service >/dev/null 2>&1 || true\n'
        'else systemctl start avahi-daemon.service >/dev/null 2>&1 || true; fi')
# DISPLAY-511: renderer OLED é substituição explicitamente autorizada; ON7LDS intacto.
install('usr/local/libexec/pu2pny/oled-502.py', repo/'runtime/5.11/oled.py')
core='usr/local/sbin/2pny-display-core'
s=(root/core).read_text(); start=s.index('        pix=img.load()\n'); end=s.index('    def label(',start)
replace(core,s[start:end],
        '        packed=img.convert("1").transpose(self.Image.Transpose.TRANSPOSE).tobytes()\n'
        '        reverse=bytes(int(f"{x:08b}"[::-1],2) for x in range(256))\n'
        '        old=getattr(self,"_511_pages",{})\n'
        '        for page in range(self.h//8):\n'
        '            data=bytes(reverse[b] for b in packed[page::self.h//8])\n'
        '            if old.get(page)==data:continue\n'
        '            self.cmd(0xB0+page,0x02 if self.sh1106 else 0x00,0x10)\n'
        '            for off in range(0,128,16):self.bus.write_i2c_block_data(self.addr,0x40,list(data[off:off+16]))\n'
        '            old[page]=data\n'
        '        self._511_pages=old\n')
replace(core, 'label(20,81,280,34,now,WHITE,1),',
        'label(20,81,280,25,now,WHITE,1),\n'
        '                         label(16,106,288,17,"CPU "+" / ".join((str(tel.get(k))+u) if isinstance(tel.get(k),(int,float)) and tel.get(k)>=0 else "—" for k,u in (("temperature"," C"),("load_1",""),("cpu_frequency_mhz"," MHz"))),GRAY,1),')
install('etc/tmpfiles.d/2pny-cpu-511.conf', 'z /sys/devices/system/cpu/cpu[0-9]*/cpufreq/cpuinfo_cur_freq 0444 root root -\n', 0o644)
# BOOT-511: listas fora do boot.
for unit in ('2pny-hostfiles-update','2pny-auto-maintenance'):
    install(f'etc/systemd/system/{unit}.service.d/511-priority.conf','[Service]\nNice=19\nIOSchedulingClass=idle\nCPUWeight=10\n',0o644)
install('usr/local/sbin/2pny-fast-resume',repo/'runtime/5.11/fast-resume.py')
install('usr/local/sbin/2pny-voice-apply',repo/'runtime/5.11/voice-apply.py')
(root/'usr/share/2pny/audio/dstar-off').mkdir(parents=True,exist_ok=True)
for proto in ('dmr','dstar','p25','nxdn'):
    unit='dmrgateway' if proto=='dmr' else proto+'gateway'
    install(f'etc/systemd/system/2pny-{unit}.service.d/511-voice.conf',
            f'[Service]\nExecStartPre=+-/usr/local/sbin/2pny-voice-apply --only {proto} --no-restart\n',0o644)
install('etc/systemd/system/2pny-voice-apply.service','[Unit]\nDescription=Aplicar voz PU2PNY-OS\n[Service]\nType=oneshot\nExecStart=/usr/local/sbin/2pny-voice-apply --request\nTimeoutStartSec=150\n',0o644)
# UI-511: neutra e relógio oculto por CSS, DOM preservado.
for path in sorted((root/'usr/share/2pny').glob('*')):
    if path.suffix not in ('.html','.js'):
        continue
    text=path.read_text()
    for line in list(dict.fromkeys(l for l in text.splitlines(True) if 'Pi-Star' in l or 'WPSD' in l)):
        replace(str(path.relative_to(root)),line,line.replace('Pi-Star / WPSD','MMDVMHost / ON7LDS').replace('Pi-Star e no WPSD','MMDVMHost e no ON7LDS').replace('Pi-Star','MMDVMHost').replace('WPSD','ON7LDS'))
system='usr/share/2pny/system.html'
replace(system,'<h2>Relógio</h2>','<h2>Relógio</h2><style>article:has(#localClock),#clockLocal,#clockUTC,#pnyClock,.top .clock{display:none!important}</style>')
replace(system,'Relógio, sincronização, operação do rádio e energia.','Operação do rádio, voz, energia e estado do sistema.')
# NET-511: nunca fazer nmcli no contexto síncrono de dispatcher.
replace('etc/NetworkManager/dispatcher.d/90-pu2pny-wifi-choice',
        '/usr/local/sbin/2pny-wifi-profiles auto-select >/dev/null 2>&1 || true',
        'systemctl start --no-block 2pny-wifi-autoselect.service >/dev/null 2>&1 || true')
install('etc/systemd/system/2pny-wifi-autoselect.service',
        '[Unit]\nDescription=Selecionar rede salva fora do dispatcher\n[Service]\nType=oneshot\nExecCondition=/usr/bin/test ! -f /run/2pny/ap-scan-hold\nExecStart=/usr/bin/flock -n /run/2pny/wifi-operation.lock /usr/local/sbin/2pny-wifi-profiles auto-select\nTimeoutStartSec=45\n',0o644)
# HOST-511: os escritores legados também precisam preservar o hostname após troca de rede.
for path in ('usr/local/sbin/2pny-network-switch','usr/local/sbin/2pny-firstboot','usr/local/sbin/2pny-wifi-profiles'):
    text=(root/path).read_text()
    for line in list(dict.fromkeys(l for l in text.splitlines(True) if 'hostnamectl set-hostname pu2pny ' in l or 'connection.autoconnect-retries 3' in l)):
        replace(path,line,line.replace('hostnamectl set-hostname pu2pny ',f'hostnamectl set-hostname {newhost} ').replace('connection.autoconnect-retries 3','connection.autoconnect-retries 0'))
# PROTO-511: código novo isolado; INI RF somente leitura.
install('usr/local/sbin/2pny-crossmode',repo/'runtime/5.11/mode.py')
install('usr/local/sbin/2pny-direct-group',repo/'runtime/5.11/direct-group.py')
install('usr/local/sbin/2pny-cm-run',repo/'runtime/5.11/cm-run.py')
for p in (repo/'runtime/5.11/cm-templates').iterdir():
    install('usr/local/libexec/pu2pny/cm-templates/'+p.name,p,0o644)
install('etc/systemd/system/2pny-mode-apply.service','[Unit]\nDescription=Aplicar modo exclusivo PU2PNY-OS\n[Service]\nType=oneshot\nExecStart=/usr/local/sbin/2pny-crossmode --request\nTimeoutStartSec=180\n',0o644)
for unit,command in (('2pny-cm@','/usr/local/sbin/2pny-cm-run %i converter'),('2pny-cm-gateway@','/usr/local/sbin/2pny-cm-run %i gateway'),('2pny-direct-group','/usr/local/sbin/2pny-direct-group')):
    install('etc/systemd/system/'+unit+'.service',f'[Unit]\nDescription=Modo experimental PU2PNY-OS\nAfter=2pny-mmdvmhost.service\n[Service]\nType=simple\nExecStart={command}\nRestart=no\nNoNewPrivileges=yes\nProtectHome=yes\nProtectSystem=strict\nReadWritePaths=/var/lib/2pny/crossmode /run/2pny\nPrivateTmp=yes\n',0o644)
install('etc/systemd/system/2pny-direct.service.d/511-enabled.conf','[Service]\nExecCondition=/usr/local/sbin/2pny-crossmode --legacy-gate\n',0o644)
for unit in ('2pny-profile-autostart','2pny-profile-autostart-retry'):
    install(f'etc/systemd/system/{unit}.service.d/511-mode.conf','[Service]\nExecCondition=/usr/local/sbin/2pny-crossmode --gate\n',0o644)
# Chamar off antes de mudança solicitada de perfil evita dois donos das mesmas portas.
replace('usr/local/sbin/2pny-protocol-profiles','def activate(proto):\n',
        'def activate(proto):\n    if readj(STATE/"special-mode.json").get("mode"):\n        subprocess.run(["/usr/local/sbin/2pny-crossmode","off"],check=True,timeout=90)\n')
install('etc/systemd/system/2pny-special-mode-reset.service','[Unit]\nDescription=Retorno seguro ao perfil de rádio no boot\nBefore=2pny-profile-autostart.service 2pny-profile-autostart-retry.service\n[Service]\nType=oneshot\nExecStart=/usr/local/sbin/2pny-crossmode --boot-reset\nRemainAfterExit=yes\n[Install]\nWantedBy=multi-user.target\n',0o644)
link=root/'etc/systemd/system/multi-user.target.wants/2pny-special-mode-reset.service'
assert not link.exists();link.parent.mkdir(parents=True,exist_ok=True);link.symlink_to('../2pny-special-mode-reset.service')
# Caminho gravável do daemon Direct existe sem ativar o recurso.
(root/'var/lib/2pny/crossmode').mkdir(parents=True,exist_ok=True)
install('usr/share/2pny/panel-511.js',repo/'runtime/5.11/panel.js',0o644)
for path,card in (('usr/share/2pny/protocols.html','mode-card.html'),('usr/share/2pny/direct.html','group-card.html')):
    replace(path,'</main>',(repo/'runtime/5.11'/card).read_text()+'\n</main>')
    replace(path,'</body>','<script src="/panel-511.js"></script></body>')
replace(system,'</body>','<script src="/panel-511.js"></script></body>')
replace(system,'<label><input id="voiceEnabled" type="checkbox" style="width:auto"> Ativar avisos por voz</label>',
        '<label hidden><input id="voiceEnabled" type="checkbox"> Voz geral</label>'+''.join(f'<label><input id="voice{key}511" type="checkbox" style="width:auto"> Avisos {label}</label>' for key,label in (('DMR','DMR'),('DStar','D-Star'),('P25','P25'),('NXDN','NXDN'))))
replace(system,'Avisos de link/status usam áudio AMBE do DMRGateway. O anúncio horário só fala quando o slot está livre.',
        'Avisos de link e estado por protocolo. Hora cheia disponível somente em D-Star; áudio horário em inglês. O DMRGateway não anuncia a hora.')
# Aviso de alimentação distingue eventos atuais de históricos; não implica falha presente.
replace(system, "PNY.q('throttle').textContent=t.throttled_active===true?'Ativo':t.throttled_active===false?'Não':'—';",
        "var uv=t.throttled_raw==null?0:Number(t.throttled_raw);PNY.q('throttle').textContent=(uv&1)?'Subtensão agora: verifique fonte e cabo':(uv&65536)?'Subtensão registrada desde o boot: verifique fonte e cabo':t.throttled_active===true?'Ativo':t.throttled_active===false?'Não':'—';")
# versionamento e SEC-511: corrigir somente dono de CI, nunca chmod global.
backup('etc/2pny/version'); (root/'etc/2pny/version').write_text('5.11.000\n')
for base, dirs, files in os.walk(root):
    for name in ['.']+dirs+files:
        path=Path(base)/name
        st=path.lstat()
        if st.st_uid==1001 or st.st_gid==1001:
            os.chown(path,0 if st.st_uid==1001 else -1,0 if st.st_gid==1001 else -1,follow_symlinks=False)
if os.geteuid()==0:os.chown(root/'var/lib/2pny',0,0)
(root/'var/lib/2pny').chmod(0o755)
print('PATCH_511_OK',arch)
