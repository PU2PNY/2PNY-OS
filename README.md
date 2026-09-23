# PU2PNY-OS

**PU2PNY-OS — Digital Radio Operating System**

Sistema operacional/appliance próprio para Raspberry Pi e hotspots MMDVM, desenvolvido com foco em baixo consumo, configuração sem terminal, operação multiprotocolo, diagnóstico, rollback e preservação rigorosa do que já foi aprovado.

> **Estado atual:** `0.3.21-alpha` — **ALPHA / PARA TESTE FÍSICO**. Não é PROD.

## Release atual

- **Versão:** `0.3.21-alpha`
- **Branch:** `pu2pny-os-0.3.21-alpha`
- **Base preservada:** `0.3.20-alpha`
- **GitHub Actions:** workflow de release com publicação validada; consulte Actions para o run mais recente.
- **Source:** PASS
- **Staged source:** PASS
- **Build ARM64:** PASS
- **XZ + SHA-256:** PASS
- **Preflight REL-015:** PASS
- **Validador final:** PASS
- **Publicação da prerelease:** PASS
- **Imagem:** `PU2PNY-OS-0.3.21-alpha-arm64.img.xz`
- **Tamanho:** `610089972` bytes
- **SHA-256:** `c2ec6b729b3f60153274909c8280fc2f73a07d5e426fdd129a7982d4f9d420ab`
- **Integridade:** conferir também o arquivo `.sha256` publicado junto da imagem.

### Download

- [Release PU2PNY-OS 0.3.21 Alpha](https://github.com/PU2PNY/2PNY-OS/releases/tag/v0.3.21-alpha)
- [Imagem ARM64](https://github.com/PU2PNY/2PNY-OS/releases/download/v0.3.21-alpha/PU2PNY-OS-0.3.21-alpha-arm64.img.xz)
- [SHA-256](https://github.com/PU2PNY/2PNY-OS/releases/download/v0.3.21-alpha/PU2PNY-OS-0.3.21-alpha-arm64.img.xz.sha256)

A publicação e os gates acima são validação **SW/CI**. Eles não substituem teste físico em Raspberry Pi + MMDVM + display.

## Baseline protegido

A regra permanente do projeto é:

> **funcionando + aprovado = preservar**

**D-Star simplex** e **DMR simplex** foram aprovados fisicamente na rodada de 22/09/2026 e são baseline protegida. Problemas de duplex devem ser corrigidos sem reescrever ou regredir simplex.

O mesmo princípio vale para rede, wizard, RF, displays, protocolos, painel, atualização e demais módulos.

## Principais mudanças da 0.3.21

- correções DMR duplex isoladas do simplex aprovado, com TS1/TS2 locais no modo repetidora;
- arbitragem de voz DMR ajustada para não silenciar áudio NETWORK→RF enquanto o anúncio apenas aguarda;
- estado DMR passa a separar TG solicitado de TG confirmado e evita mostrar “Módulo C” quando o conceito real é TG;
- RX/TX duplex separados no Ao Vivo e na configuração de protocolo;
- DNS com confirmação real e recuperação visual automática;
- Wi-Fi 1 + Wi-Fi 2/backup, failover automático e seleção por sinal com histerese;
- aviso global quando a Internet cai;
- idioma persistente perguntado uma vez; com Internet já configurada, wizard retoma em Hardware;
- PU2PNY Direct acionado pelo rádio, com payload QSO direct-only e sem relay de servidor;
- APRS com diagnóstico ACK/REJ por origem + ID, coordenadas manuais em HTTP e documentação M-SMS/H-SMS sem fingir entrega DMR;
- Nextion continua sem falso positivo: sem COMOK real, comunicação física permanece não confirmada;
- relógio por NTP/timezone automático, com horário de verão manual apenas na apresentação;
- journald limitado a 64 MiB / 7 dias;
- assistente BER/RXOffset com medição real, melhor valor da sessão, salvar e restaurar;
- release notes em PT/EN/ES e gates completos de CI/imagem.

## Base herdada da 0.3.20

### D-Star

- módulo local/RPT1 separado do módulo remoto do refletor;
- novas configurações usam **B** como padrão local;
- seletor manual **A–D**;
- upgrades preservam o módulo local já configurado;
- RPT2 continua usando o gateway `G`;
- comandos de link/unlink/status via rádio não podem alterar apenas o painel: o estado efetivo só muda depois de confirmação real do gateway;
- catálogo XLX incorporado para resolução dos comandos via rádio;
- REF/XRF/DCS continuam usando o catálogo compatível do DStarGateway.

### DMR

- XLX aparece como primeira opção;
- troca BrandMeister/TGIF/outro → XLX remove ESSID incompatível;
- DMR simplex permanece protegido;
- modo duplex mantém TS1/TS2 localmente quando aplicável;
- TG4000, TG4001–TG4026 e TG4099 podem ser tratados em TS1 ou TS2;
- estado visual só deve refletir mudança efetivamente confirmada.

### Ao Vivo

- aviso TOT preserva corte aos 180 s;
- 2:30–2:49: alerta amarelo;
- 2:50–2:59: alerta vermelho;
- S-meter aparece somente em evento RF com RSSI real;
- tráfego Internet→RF não inventa RSSI/BER;
- modo duplex exibe RX e TX separadamente.

### Rede e Protocolos

- Internet local e link remoto são estados separados;
- UI não deve dizer “aguardando rede” quando a Internet já está disponível;
- confirmação de DNS respeita a janela real do backend;
- ativação de perfil não deve prender a interface esperando confirmação remota.

### Nextion e displays

- Nextion física via MMDVM só é confirmada após resposta real `comok`;
- MMDVMHost continua proprietário da UART;
- PU2PNY Moderno V2 é o layout padrão após confirmação física;
- nenhum HMI/TFT é gravado automaticamente.

### APRS

- página passa a chamar-se **APRS**;
- preserva APRS-IS, ACK/REJ, retry limitado e deduplicação;
- comandos PING, STATUS, LAST, MYLAST, ONLINE, MODULE, INFO e HELP usam apenas estado real disponível.

### Sistema e atualização

- lista completa de timezones instalados;
- ajuste manual de data/hora com confirmação efetiva;
- download de logs sanitizados;
- OTA com SHA-256, “Instalar agora” / “Instalar depois” e rollback automático em falha após início da mutação.

### Direct / P2P

- atividade RF real pode iniciar Direct automaticamente quando existir peer pareado e online no mesmo protocolo;
- D-Star usa URCALL/indicativo;
- DMR usa Private Call/Radio ID;
- TG DMR não é chamada Direct.

## O que ainda precisa de teste físico

Continuam **HW PENDENTE** na 0.3.21:

- regressão de D-Star simplex e DMR simplex **na nova imagem 0.3.21**, preservando a baseline aprovada;
- DMR duplex: RF→rede, rede→RF com áudio, timeout, TS/CC e atualização do Ao Vivo;
- troca real de TG/módulo pelo rádio e confirmação correta no painel;
- Wi-Fi 1↔Wi-Fi 2 e reconhecimento rápido de Ethernet em Raspberry real;
- Nextion física, COMOK e renderer/HMI real;
- PU2PNY Direct entre dois hotspots reais, inclusive comportamento sob NAT/CGNAT;
- BER/RSSI reais e recomendação RXOffset em MMDVM;
- ACK real das mensagens APRS; os IDs históricos 89018, 70182 e 42231 permanecem não confirmados sem evidência de ACK correspondente;
- demais comportamentos marcados como HW PENDENTE na TEST_MATRIX.

Não promover esses itens para HW PASS apenas porque CI/VPS passou.

## Primeiro acesso

Conforme `NET-001`:

- SSID de setup: `pu2pny`
- endereço local do setup: `10.43.0.1`
- acesso normal: `http://pu2pny.local/`
- o AP deve permanecer recuperável se o provisionamento falhar.

## Validação

O projeto usa estes níveis:

- **DOC** — documentação/código
- **SW** — software/CI
- **VPS** — Linux/VPS
- **HW** — Raspberry Pi + MMDVM/display/hardware real
- **PROD** — produção

`VPS aprovado ≠ HW aprovado`.

Quando aplicável sem RF real, testes devem usar a VPS/SentinelX e validação cruzada com GitHub/CI, plugins/conectores e fontes oficiais.

## Gate de release

Fluxo obrigatório:

`requisito → implementação → teste → resultado → regressão → pendências`

Para imagens:

`source → staged source → ARM64 → XZ/SHA-256 → REL-015 preflight → validador final → artefato → publicação`

Uma nova funcionalidade não compensa regressão de algo previamente aprovado.

## Documentação canônica

Antes de modificar o projeto, leia:

1. [PU2PNY-OS_START_HERE.md](PU2PNY-OS_START_HERE.md)
2. [PU2PNY-OS_MASTER_SPEC.md](PU2PNY-OS_MASTER_SPEC.md)
3. [PU2PNY-OS_RELEASE_STATUS.md](PU2PNY-OS_RELEASE_STATUS.md)
4. [PU2PNY-OS_TEST_MATRIX.md](PU2PNY-OS_TEST_MATRIX.md)
5. [PU2PNY-OS_CHANGELOG.md](PU2PNY-OS_CHANGELOG.md)
6. [PU2PNY-OS_PROJECT_INSTRUCTIONS.md](PU2PNY-OS_PROJECT_INSTRUCTIONS.md)
7. [docs/README.md](docs/README.md)

## Identidade do projeto

- Nome: **PU2PNY-OS**
- Título da aba do painel: exatamente **PU2PNY-OS**
- Repositório observado atualmente: `PU2PNY/2PNY-OS`
- Nome canônico aprovado para futura renomeação: `PU2PNY/PU2PNY-OS`

A renomeação só deve ser considerada concluída quando a metadata do GitHub confirmar o novo nome.
