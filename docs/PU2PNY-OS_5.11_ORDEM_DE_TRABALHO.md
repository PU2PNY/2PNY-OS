# ORDEM DE TRABALHO — PU2PNY-OS 5.11 COMPLETA (Raspberry 32/64, Orange Pi Zero, NanoPi NEO)

Você vai implementar, testar e publicar a versão **5.11** do PU2PNY-OS, completa: todos os itens abaixo, sem deixar nada "planejado para a próxima". Trabalhe até o fim, sem pedir confirmação para cada passo. Só pare para perguntar se uma decisão for irreversível e puder ir para os dois lados.

## 0. Regras obrigatórias (não negociáveis)

1. Repositório: `PU2PNY/2PNY-OS`. Base de trabalho: branch `release/pu2pny-5.10` (tag `pu2pny-v5.10.000`, commit `1a280662d4ab48bb1ea9726874a11c1e5a126c55`). Crie a branch `release/pu2pny-5.11` a partir dela. Leia a seção 5.10 do CHANGELOG: ela já corrigiu CLOCK-060, DIRECT-060, BOOT-060, UI-060 e EXPERT-060 — preserve esses itens. A `main` é histórica, não use.
2. Antes de mexer em qualquer coisa, leia na raiz da branch: `PU2PNY-OS_START_HERE.md`, `PU2PNY-OS_MASTER_SPEC.md`, `PU2PNY-OS_RELEASE_STATUS.md`, `PU2PNY-OS_TEST_MATRIX.md`, `PU2PNY-OS_CHANGELOG.md`, `PU2PNY-OS_PROJECT_INSTRUCTIONS.md` e `docs/PU2PNY-OS_DISPLAY_BASELINE.md`.
3. **Funcionando + aprovado = preservar.** DMR simplex, D-Star simplex, YSF simplex, Nextion ON7LDS (5.00.002, baseline DISPLAY-041), AP de primeiro acesso, wizard e voz DMR são baseline protegido. Não refatore nem reescreva nada fora do escopo abaixo.
4. Siga o modelo de build que já existe: **overlay sobre a imagem publicada anterior**. Copie o padrão dos arquivos `ci/*-5.10.py` e do workflow da 5.10, criando os equivalentes `5.11`. A base é `pu2pny-32-5.10.img.xz` / `pu2pny-64-5.10.img.xz` da release `pu2pny-v5.10.000`; confira o SHA-256 delas antes de usar.
5. Toda edição de arquivo na imagem: faça backup `.pre-5.11`, use substituição por âncora que precisa casar **exatamente uma vez** (como `replace()` no patch da 5.09) e mantenha a lista `PROTECTED` byte-idêntica. Se algum arquivo protegido precisar mudar (ex.: `2pny-protocol-network-apply`), retire-o da lista só para aquele caso e justifique no CHANGELOG.
6. Não invente dado (BER, RSSI, temperatura, conexão). Sem fonte = `—` / `não verificado`.
7. Não chame nada de "testado" ou "funcionando" sem prova. Níveis: DOC, SW, VPS, HW, PROD. Tudo desta versão sai como **SW/CI PASS, HW PENDENTE** até o usuário testar no hotspot real.
8. Shell com `set -euo pipefail`, aspas em variáveis, sem `eval`, sem `curl | bash`. Nunca exponha senhas/tokens.
9. Toda decisão nova recebe ID (`PERF-511`, `NET-511`, `DISPLAY-511`, etc.) e entra no MASTER_SPEC, CHANGELOG, RELEASE_STATUS e TEST_MATRIX com critério de aceite.
10. Todos os ajustes valem para **todas** as imagens: Raspberry 32 bits (Pi Zero/ARMv6), Raspberry 64 bits, Orange Pi Zero (H2+) e NanoPi NEO (H3).
11. Responda e documente em português.

## 1. Causas já encontradas nos diagnósticos do usuário — corrija

Os diagnósticos foram coletados com a **5.08** em campo. Para cada item abaixo, confira primeiro se a 5.10 já resolveu (monte a imagem 5.10 e compare); se já resolveu, preserve e registre; se não, corrija.

Diagnósticos: Pi Zero W 32 bits (carga 6,0 em 1 núcleo, boot 2min17s, 46,5 °C) e Pi 4 64 bits (boot 1min25s, `throttled=0x50000`).

### 1.1 Arquivos da imagem com dono errado (uid/gid 1001) — CRÍTICO
Nas imagens 5.09 e 5.10 (32 e 64), ~180 arquivos e pastas estão com dono `1001:1001` (usuário do runner de CI): `/etc/NetworkManager/**`, `/etc/systemd/system/2pny-*`, `/usr/local/**`, `/var/lib/2pny/**`, `/etc/avahi/**`, `/etc/mosquitto/**`, `/etc/udev/rules.d/**`.
Consequência comprovada no log do Pi 4: o NetworkManager **recusa** os scripts de dispatcher (`not owned by root`: `90-pu2pny-wifi-choice`, `91-pu2pny-online-actions`, `90-pu2pny-mdns`, `90-2pny-connectivity`) e os keyfiles (`File owner (1001) is insecure`). Ou seja, failover de Wi-Fi, ações ao ficar online e re-anúncio do mDNS nunca rodaram.
A 5.10 só registrou isso como achado ("exige decisão"); **o usuário decidiu: corrigir agora.** **Correção:** no build, `chown root:root` de tudo que tiver uid ou gid 1001 (exceto o que tiver dono intencional diferente). `/var/lib/2pny` fica `root:root 0755`. Adicione ao gate do build uma verificação que falha se sobrar qualquer arquivo com uid/gid 1001. Antes, revise os 4 scripts de dispatcher, porque eles vão começar a rodar de verdade (`90-pu2pny-wifi-choice` chama `2pny-wifi-profiles auto-select`; confirme que é seguro).

### 1.2 `2pny-direct.service` em loop de reinício — JÁ CORRIGIDO NA 5.10 (DIRECT-060), só conferir
O log de avisos do Pi Zero mostra `2pny-direct.service: Failed with result 'exit-code'` a cada ~8 s, por horas. Cada reinício abre 2 processos Python + o binário. Isso também explica `dbus-daemon` 7% e `systemd` 4% de CPU.
A 5.10 achou a causa (binário AArch64 na imagem de 32 bits), trocou por build ARMv6 e limitou a 4 falhas em 15 min. Confira que o binário certo está em cada imagem (incluindo Orange Pi e NanoPi) e só rode o serviço se o Direct estiver habilitado. O grupo P2P novo (seção 3.5) convive com ele.

### 1.3 `2pny-station-worker` com 25% de CPU constante (`/usr/local/sbin/2pny-station-worker`)
- Laço principal acorda a cada 100 ms (`sel.select(timeout=0.10)`).
- **Bug de laço ocupado:** quando um processo seguidor (`journalctl -f` ou `mosquitto_sub`) termina, o stdout fica em EOF, o `select` retorna sempre e o código faz `if not raw: continue` sem desregistrar. Desregistre o fd no EOF e recrie o seguidor com recuo (5 s → 60 s).
- Abre 7 `journalctl -f` separados (1 por unidade). Troque por **um único** `journalctl -f -o json -u A -u B ...` e despache pelo campo `_SYSTEMD_UNIT`.
- `ping` via subprocesso a cada 5 s ocioso → 30 s ocioso, 2 s com chamada ativa.
- Telemetria chama `vcgencmd`, `iw`, `ip` e `mosquitto_pub` por subprocesso; mantenha só o necessário e espaçe quando ocioso.
- Timeout do select para 1 s. A semântica do Ao Vivo (`live-state.json`, histórico, contatos) não pode mudar.

### 1.4 `2pny-network-core` (bash) faz ~20 forks a cada 3 s, incluindo 2× `nmcli`
Faça as checagens pesadas (`nmcli`, `write_status`) a cada 4 voltas ou quando o carrier mudar; mantenha a leitura de carrier da Ethernet a cada 3 s; ajuste `WIFI_MISS_COUNT` para manter o mesmo tempo real (~45 s).

### 1.5 Wi-Fi salvo não volta depois de desligar o hotspot
Em `2pny-network-core`:
- O script reafirma `connection.autoconnect-retries 3` no boot, desfazendo a NET-045 (que pôs 0 = infinito). Troque para 0.
- Se as 3 tentativas do boot falham (ex.: roteador volta depois da queda de energia), o AP de recuperação sobe no **único rádio** (Pi Zero W) e **nunca mais tenta o Wi-Fi salvo**. Adicione: em modo AP de recuperação, com perfil `PU2PNY-WIFI` salvo e **nenhum cliente associado ao AP** (`iw dev <if> station dump` vazio), a cada 2 min (recuo até 5 min) pare o AP, tente `nmcli --wait 30 connection up PU2PNY-WIFI`; deu certo → `ap-disabled` e segue; falhou → volta o AP.

### 1.6 MMDVMHost falha no boot e o último protocolo demora a voltar
No Pi 4, `2pny-mmdvmhost.service` falhou 4× entre +20 s e +42 s do boot, a retomada rápida cancelou (`MMDVMHost não iniciou`) e o perfil só voltou com o retry em ~3 min. Causa exata não comprovada.
**Correção:** em `runtime/5.07/fast-resume.py` (instalado como `/usr/local/sbin/2pny-fast-resume`), antes de desistir, tente até ~45 s: `systemctl reset-failed 2pny-mmdvmhost.service`, start, espera 3 s, de novo. Registre no log o motivo (saída de `systemctl status` resumida) para a próxima análise. Meta: voltar conectado ao último protocolo em < 60 s após a rede subir.

### 1.7 Boot mais rápido e mais leve
`systemd-analyze blame` do Pi 4: `profile-autostart-retry` 71 s, `display-reconcile` 70 s, `operational-restore` 58 s, `display-online-detect` 37 s, `hostfiles-update` 34,8 s, `network-online` 11 s, `mdns-guard` 10,7 s.
- A 5.10 (BOOT-060) já faz manutenção e listas esperarem 5 min após o boot. Complete com `Nice=19`, `IOSchedulingClass=idle`, `CPUWeight=10` nesses serviços.
- `2pny-mdns-guard`: escreve `/etc/avahi/services/pu2pny-http.service` com `cat >` (o avahi lê no meio da escrita: `XML_ParseBuffer() failed`). Grave atômico (tmp + mv), só se mudou, e só reinicie o avahi se algo mudou; não chame `hostnamectl` se o hostname já está certo.
- `sysfs` `cpuinfo_cur_freq` é 0400; faça legível (tmpfiles `z /sys/devices/system/cpu/cpu[0-9]*/cpufreq/cpuinfo_cur_freq 0444`).
- Meça antes/depois em VPS/chroot o que der e deixe o ganho real como HW PENDENTE.
- Objetivo do usuário: sistema leve como um ESP32, boot rápido, conectar à internet rápido e reiniciar no último protocolo. Corte tudo que roda sem necessidade; nada de polling agressivo.

## 2. Telas

### 2.1 OLED/LED: hoje liga mostrando várias linhas em páginas rotativas
Arquivo: `/usr/local/libexec/pu2pny/oled-502.py`, função `render()`, chamada por `/usr/local/sbin/2pny-display-core`.
Troque por uma tela fixa no estilo MMDVMHost/OLED (sem paginação), compatível com 128×64 e 128×32:
- **Parado:** modo/protocolo no topo (ex. `DMR  XLX026 C`), indicativo grande, IP, `Listening`.
- **Em chamada:** `DMR TS2 RX`/`TX`, indicativo de quem fala grande, nome (se houver), destino (`TG 4003`), duração e BER quando existir.
- Fonte DejaVu Sans Mono Bold nativa (já usada na 5.09). No 128×32 só 2 linhas.
- No `2pny-display-core` (classe `OLED.show_image`): envie só as páginas I2C que mudaram e evite `pix[x,y]` pixel a pixel (custa CPU no Pi Zero). Em repouso, redesenhe só quando o conteúdo mudar.

### 2.2 Nextion não mostra dados da CPU (TEMP/CYCLES/LOAD/DISK/IP — a 5.10 deixou como não confirmado)
Fatos levantados no código upstream:
- No caminho ON7LDS (MMDVM-Display commit `96a0705` → PTY → NextionDriver), quem preenche `t20` (temperatura), `t21` (MHz) e `t22` (carga) é o próprio NextionDriver (`basicFunctions.c`), lendo `/sys/class/thermal/thermal_zone0/temp`, `/sys/devices/system/cpu/cpu0/cpufreq/cpuinfo_cur_freq` e `/proc/loadavg`, quando está na página 0 e recebe `t2.txt` (relógio) ou `status.val=17`. Ele roda como `mmdvm`, e `cpuinfo_cur_freq` é legível só pelo root → `"?"`. O item 1.7 resolve isso.
- O `display/adapter.py` publica CPU em `pu2pny-display-info/json` a cada 60 s; confira se chega ao MMDVM-Display.
- No renderizador próprio (`2pny-display-core`, classe `Nextion`, tela de standby 320×240) não existe linha de CPU. Adicione temperatura, carga e MHz lidos de `/run/2pny/telemetry.json` (já gerado pelo station-worker).
- Não altere o HMI/TFT, nem o fluxo ON7LDS aprovado.

### 2.3 Tirar os nomes Pi-Star e WPSD da interface
Ocorrências visíveis: `usr/share/2pny/display.html` (eyebrow "Compatibilidade Pi-Star / WPSD"), `usr/share/2pny/wizard.html` (opção "ON7LDS / Pi-Star"), `usr/share/2pny/expert.html` ("como no Pi-Star e no WPSD"). Troque por texto neutro (ex. "Compatível com MMDVMHost/ON7LDS"). Não mexa nas URLs de dados `pistar.uk` em `2pny-hostfiles-update` (é fonte de listas, não aparece na tela). Faça uma varredura final em `usr/share/2pny/*.html`, `*.js` e no binário `2pnyd` para garantir que nenhum texto visível sobrou.

### 2.4 Tirar o relógio do menu Sistema
`usr/share/2pny/system.html`: esconda o card "Relógio" e o relógio do topo **com CSS** (`display:none`), sem remover os elementos, porque o JavaScript usa `localClock`, `utcClock` etc. e quebraria o resto da página. O ajuste automático de fuso (CLOCK-056/058) continua rodando em segundo plano. Atualize o subtítulo da página.

## 3. Funções

### 3.1 Nomes de rede (evitar conflito)
- 64 bits: `pu2pny64.local` (hoje é `pu2pny.local`). Repita exatamente o que a HOST-057 fez para o 32 bits em `ci/patch-image-5.07.py` e `ci/prepare-5.07-backend.py`: `wizard.html`, `internet.html`, `network/dnsmasq-ap.template`, `dnsmasq-shared.d/2pny-captive.conf`, `dispatcher.d/90-pu2pny-mdns`, `2pny-network-core`, `2pny-mdns-guard` (hostname, `/etc/hostname`, avahi host-name), `2pny-mdns-alias` (`2pny64.local`), `/etc/hostname`, `/etc/hosts`, `avahi-daemon.conf`, `oled-502.py`, `lcd-504.py` e as 7 ocorrências no `main.go` do backend.
- 32 bits continua `pu2pny32.local`. Orange Pi e NanoPi usam `pu2pny32.local`.

### 3.2 Ao conectar no AP abre duas abas (e o wizard mostra "welcome" em equipamento já configurado — a 5.10 deixou sem causa)
Handler `captivePortalHandler` no `main.go` do backend: toda sonda de captive portal (generate_204, hotspot-detect, connecttest...) recebe redirect. Causa exata **não comprovada**. Use um único URL canônico de destino (`http://pu2pny64.local/wizard?captive=1` / `pu2pny32`) em todos os ramos (inclusive o `default`, que hoje usa `/wizard` relativo) e marque como HW PENDENTE. Se for implementar deduplicação por cliente, não responda 204 para o Android enquanto a página de configuração estiver aberta, porque isso fecha a janela.

### 3.3 Voz enviada ao rádio: liga/desliga para todas as opções
Hoje o card "Voz enviada ao rádio" (system.html) salva `voice-settings.json` e só reinicia o DMRGateway, **sem regravar o .ini** (o `[Voice] Enabled` só é gerado ao ativar perfil) → o botão não tem efeito imediato. Faça:
- Opções separadas: DMR, D-Star, P25, NXDN, hora cheia e idioma.
- Novo helper `/usr/local/sbin/2pny-voice-apply` que edita os .ini já gerados: `dmr/DMRGateway.ini` `[Voice] Enabled/Language`; `p25/P25Gateway.ini` e `nxdn/NXDNGateway.ini` `[Voice] Enabled` (hoje fixo em 0 no `2pny-protocol-network-apply`); D-Star: o `dstargateway` da imagem (upstream `612f388`) **não tem** a opção `[General] Voice` (ela só existe a partir do commit `3e26100`), então para desligar aponte `[Paths] Data=` para uma pasta vazia (`/usr/share/2pny/audio/dstar-off/`) e para ligar volte para `/usr/local/share/dstargateway.d/`.
- Reinicie só o gateway ativo. Para valer após troca de perfil, adicione drop-in em cada gateway com `ExecStartPre=+-/usr/local/sbin/2pny-voice-apply --only <proto> --no-restart`.
- Rota nova no backend (arquivo `runtime/5.11/web.go`, registrada em `init()` como as anteriores, com checagem `sameOrigin`).
- A hora cheia (VOICE-056) só existe para D-Star (`dgwvoicetransmit`); o DMRGateway não tem anúncio de hora. Diga isso na tela, não invente.

### 3.4 Transcodificação (crossmode)
Regra do usuário: **um modo ou um crossmode por vez**. D-Star não transcodifica. Use MMDVM_CM (`github.com/juribeparada/MMDVM_CM`, commit `7328c9e`): DMR2YSF, YSF2DMR, DMR2NXDN, YSF2NXDN, YSF2P25.
- **Compilação:** no CI, nunca no runner direto para o 32 bits (o toolchain armhf do Debian é ARMv7 e não roda no Pi Zero). Compile dentro de um chroot do rootfs da própria imagem 32 bits (Raspbian ARMv6) com `qemu-user-static`, numa **cópia descartável** do rootfs, instalando `build-essential` lá; para 64 bits, chroot do rootfs 64. Instale só os binários em `/usr/local/bin/`.
- **Encaixe sem mexer no MMDVMHost.ini:**
  - DMR2YSF/DMR2NXDN: com o perfil DMR ativo, pare o DMRGateway e suba o conversor nas mesmas portas (`RptPort=62032`, `LocalPort=62031`); do lado YSF/NXDN suba uma instância própria de YSFGateway/NXDNGateway (`/var/lib/2pny/crossmode/`) com o refletor escolhido, usando os templates de `.ini` que já existem em `2pny-protocol-network-apply`.
  - YSF2DMR/YSF2NXDN/YSF2P25: com o perfil YSF ativo, pare o YSFGateway e suba o conversor nas portas que o MMDVMHost usa (`LocalPort=4200`, `DstPort=3200`; leia do `MMDVM-Host.ini` em tempo de execução). YSF2DMR fala direto com o master DMR (BM/XLX/TGIF) usando ID e senha do perfil salvo.
- Unidades `2pny-cm@.service`; helper `2pny-crossmode {off|ysf2dmr|dmr2ysf|dmr2nxdn|ysf2nxdn|ysf2p25} <destino>` com backup e rollback: se o conversor não subir em X s, volta o gateway original.
- Card na página Protocolos (ou transforme o card de Expert da 5.06 em ativo), com lista de destinos lida de `/var/lib/2pny/hosts/*`.
- Risco a registrar: MMDVM_CM foi escrito para o protocolo antigo MMDVMHost↔DMRGateway; compatibilidade com o MMDVMHost/DMRGateway atuais **não verificada** → HW PENDENTE.

### 3.5 Direct: criar grupo entre dois ou mais PU2PNY-OS, sem servidor e sem IP fixo
Decisão do usuário: **descoberta pela DHT pública (Mainline/BitTorrent) usando um código secreto do grupo**; áudio sempre direto entre os hotspots.
- `infohash = SHA1("pu2pny-direct-v1:" + código_do_grupo)`; cada hotspot faz `announce_peer` e `get_peers` (BEP 5) a cada ~5 min.
- Furo de NAT por UDP (hole punching) entre os pares encontrados; keepalive a cada 25 s.
- Autenticação e cifra com chave derivada do código do grupo (ex. HMAC-SHA256 + ChaCha20-Poly1305 se `python3-cryptography` estiver na imagem; senão HMAC + descarte do que não autenticar). Nunca mande o código em claro.
- Primeira entrega: **DMR**. O daemon `2pny-direct-group` ocupa o lugar do DMRGateway (portas 62031/62032) quando o modo "Direct grupo" está ativo, repassa os quadros `DMRD` do MMDVMHost para os pares e injeta os dos pares no MMDVMHost. Confira no código do MMDVMHost atual o protocolo do modo Gateway (pings, login) antes de escrever.
- Tela Direct: criar grupo (gera código), entrar no grupo (cola código), lista de pares com estado (`procurando`, `conectado P2P`, `bloqueado por NAT`) e como conectou. Se a operadora usar CGNAT simétrico nos dois lados, mostre "não foi possível conectar direto" — não invente relay.
- Pouca CPU: sem polling agressivo.

## 4. Imagens Orange Pi Zero (H2+) e NanoPi NEO (H3) — regra obrigatória

Modelos confirmados pelo usuário: **Orange Pi Zero (H2+, 32 bits)** e **NanoPi NEO (H3, 32 bits)**.
- Base: Armbian Bookworm minimal oficial de cada placa (`dl.armbian.com/orangepizero/...` e `dl.armbian.com/nanopineo/...`). Fixe URL e SHA-256 no workflow.
- Transplante do userland PU2PNY-OS a partir da imagem 32 bits 5.11: `/usr/local/**`, `/usr/share/2pny/**`, `/etc/2pny/**`, `/var/lib/2pny/**` (estado de fábrica), `/etc/systemd/system/2pny-*` e drop-ins, `/etc/NetworkManager/{conf.d,dispatcher.d,dnsmasq-shared.d,system-connections}`, `/etc/mosquitto/conf.d`, `/etc/avahi`, udev, journald, usuário/grupo `mmdvm` (no grupo `dialout`). Tudo com dono root.
- No chroot ARM (`qemu-arm-static`), `apt-get install` das dependências: rode `ldd` em todos os binários de `/usr/local/bin` da imagem 32 e instale as libs; mais `python3`, `python3-pil`, `python3-smbus`, `i2c-tools`, `fonts-dejavu-core`, `mosquitto`, `mosquitto-clients`, `network-manager`, `avahi-daemon`, `dnsmasq-base`, `hostapd`, `iw`, `rfkill`, `iptables`. Os binários Raspbian ARMv6 rodam em ARMv7 (mesmo ABI armhf); confirme rodando cada um com `--version`/`-v` no chroot.
- UART do modem: na barra de 26 pinos (pinos 8/10) é a UART1 → `/dev/ttyS1`. Em `/boot/armbianEnv.txt` ative `overlays=uart1 i2c0`. Crie regra udev para o link `/dev/serial0 → ttyS1`, porque todos os scripts usam `/dev/serial0`. Confira o pinout de cada placa na documentação oficial antes de fechar.
- Sem `vcgencmd`: o código tem que tolerar a ausência (telemetria, `throttled`), sem quebrar.
- O probe de hardware lê `/proc/device-tree/model` e já teve erro "não reconhece a placa" no Pi Zero: garanta que Orange Pi e NanoPi sejam aceitos como placa válida sem inventar modelo.
- Desative serviços do Armbian que pesam (`armbian-*` desnecessários, `unattended-upgrades` etc.), primeira configuração do Armbian (usuário/senha no primeiro boot) desligada, AP de primeiro acesso do PU2PNY funcionando.
- Hostname `pu2pny32`. Nomes dos arquivos: `pu2pny-opizero-5.11.img.xz` e `pu2pny-nanopineo-5.11.img.xz`.
- Gate: boot do rootfs no chroot, serviços `systemctl list-unit-files` presentes, fsck, montagem somente leitura, XZ e SHA-256. **HW PENDENTE.**

## 5. Testes, CI e publicação
1. Testes de software novos em `ci/test-5.11.py` cobrindo: dono root em tudo; station-worker sem laço ocupado (simule EOF de seguidor e meça CPU); network-core (retentativa do Wi-Fi em AP de recuperação com `nmcli`/`iw` simulados); OLED renderizando 128×64 e 128×32 em imagem PIL (salve PNG como artefato para conferência visual); Nextion standby com linha de CPU; voice-apply editando os 4 tipos de .ini; crossmode gerando .ini e fazendo rollback; Direct grupo com dois pares em loopback (descoberta simulada + troca de quadros DMRD); varredura sem "Pi-Star"/"WPSD" em texto visível; nomes `pu2pny64`/`pu2pny32`.
2. Rode todos os testes anteriores do workflow 5.10 também (regressão).
3. Valide em VPS via SentinelX o que não depende de RF: instalação dos serviços em chroot/container, backend, rotas novas, rollback.
4. Workflow `.github/workflows/5.11-release.yml` com matriz `arm32, arm64, opizero, nanopineo`; gate de escopo (manifesto completo antes/depois), arquivos protegidos byte-idênticos, fsck, montagem RO, XZ, SHA-256, `BUILD-INFO-*.json` com `HW: NOT_VERIFIED`.
5. Publique como prerelease `pu2pny-v5.11.000` com as 4 imagens, os `.sha256` e os BUILD-INFO. Notas da release em português, dizendo com honestidade o que foi corrigido em SW e o que continua sem prova em hardware.
6. Atualize os 5 documentos canônicos e o README da raiz apontando para a 5.11.

## 5.1 Pendências herdadas da 5.10 que também entram na 5.11
Lentidão ao ativar perfil, YSF sem conectar ao refletor, D-Star `connected:false` logo após ativar, assistente preso em "Conectando…" depois que o AP cai, subtensão no Pi 4 (`throttled=0x50000`: mostre aviso claro no painel de que é fonte/cabo). Investigue com o código e os logs; corrija o que tiver causa comprovada e registre o resto como não comprovado.

## 6. Entrega final ao usuário
Mensagem curta em português com: link da release, os 4 arquivos com SHA-256, lista do que mudou (com IDs), o que ele precisa testar no hotspot real (checklist: boot e tempo até conectar no último protocolo, temperatura/carga no Pi Zero, Wi-Fi depois de desligar da tomada com o roteador desligando junto, `pu2pny64.local`/`pu2pny32.local`, uma aba só no AP, OLED, Nextion com CPU, voz liga/desliga por protocolo, cada crossmode, Direct em grupo com 2 hotspots em redes diferentes, Orange Pi Zero e NanoPi NEO do zero) e o que ficou pendente ou sem prova.