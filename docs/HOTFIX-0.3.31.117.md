# PU2PNY-OS 0.3.31.117 — Wi-Fi handoff + uplink real + Nextion compatibility

## Base e escopo

- Base imutável: `v0.3.31.116`, commit `be75b68aa5549c15d538b1814ffd2df5987cb759`.
- Esta candidata é um overlay cirúrgico. Não altera o binário MMDVMHost, DMR/D-Star/YSF, DMRGateway/helpers de protocolo, RF, frequências, offsets, `2pny-network-switch`, `2pny-network-online` ou wizard.
- Requisitos: NET-037, LIVE-023, DISPLAY-025, REL-027.

## Correções

### NET-037 — retomada do painel

O backend da 0.3.31.116 já valida associação Wi-Fi, IPv4, persistência do perfil e publica `resume_urls`; também já usa `pu2pny.local`. A correção atua na página que inicia a troca: após `state=connected`, ela tenta de forma limitada reencontrar `pu2pny.local`/IPs reais e navega para `/internet` quando o hotspot estiver alcançável na LAN.

Em Ethernet, Avahi/mDNS continua event-driven. Um hotspot pode anunciar `pu2pny.local`, mas não existe mecanismo web geral e confiável para obrigar um navegador externo a abrir uma nova página apenas porque um cabo foi conectado. O aceite é não exigir pesquisa manual do IP: `http://pu2pny.local/` deve ser o endereço normal, com IP como fallback.

### LIVE-023 — Wi-Fi / Uplink

O backend já coleta RSSI real por `iw` e sinal percentual por `nmcli`. A barra do Ao Vivo passa a usar esse valor somente quando o uplink padrão for Wi-Fi. Ethernet não recebe porcentagem fictícia: mostra `Ethernet` e RSSI `—`.

### DISPLAY-025 — Pi-Star/WPSD/ON7LDS

Adiciona terceiro renderer explícito `on7lds-compatible`, sem substituir os modos existentes. O build usa a revisão fixa do ON7LDS NextionDriver:

`03b904270c9cb54f720d71753fc209afb1d9598f`

Hardening obrigatório antes da compilação:

- bloqueio de comandos da HMI que chegavam a `popen()`/`system()`;
- bloqueio de atualização TFT/HMI iniciada pela própria tela;
- bloqueio de downloads autônomos do banco de grupos/usuários;
- banco de grupos/usuários vem da revisão upstream fixada no build;
- serviço sem privilégios de root, `NoNewPrivileges`, filesystem protegido e rede restrita a localhost;
- Nextion no modem usa `Transparent Data` (`SendFrameType=1`) e porta virtual PTY;
- exatamente um writer ativo por vez;
- nenhum `.tft`/`.hmi` é gravado automaticamente.

O modelo físico obtido por `connect/comok` não identifica o HMI gravado. Nextion física permanece `PENDENTE HW` até teste em Raspberry Pi + MMDVM + tela real.

## Rollback

1. A imagem base publicada `v0.3.31.116` continua imutável.
2. O overlay salva backup do `MMDVM-Host.ini` antes de alterar o renderer.
3. Se NextionDriver, PTY ou MMDVMHost não iniciarem/permanecerem ativos, a configuração anterior é restaurada e o driver de compatibilidade é desligado.
4. Trocar de `on7lds-compatible` para renderer nativo/PU2PNY desativa o NextionDriver antes de devolver o writer ao outro renderer.
5. Em regressão geral, regravar `v0.3.31.116` é o ponto de retorno integral.

## Critério de release

Antes de publicar link:

- hardening do NextionDriver aplicado e compilado ARM64;
- testes SW/CI PASS;
- imagem base 0.3.31.116 verificada pelo SHA-256 conhecido;
- overlay montado e validado em leitura;
- hashes dos runtimes protegidos iguais antes/depois;
- `xz -t` PASS;
- SHA-256 novo gerado;
- documentação canônica sincronizada somente após os gates;
- classificação: **PARA TESTE FÍSICO**, nunca “produção” antes de HW real.
