# PU2PNY-OS

**PU2PNY-OS — Digital Radio Operating System**

Sistema operacional/appliance próprio para Raspberry Pi e hotspots MMDVM, desenvolvido com foco em baixo consumo, configuração sem terminal, operação multiprotocolo, diagnóstico, rollback e preservação rigorosa do que já foi aprovado.

> **Estado atual:** `0.3.20-alpha` — **ALPHA / PARA TESTE FÍSICO**. Não é PROD.

## Release atual

- **Versão:** `0.3.20-alpha`
- **Branch:** `pu2pny-os-0.3.20-alpha`
- **Base preservada:** `0.3.19-alpha`
- **GitHub Actions:** run `35798691612` — PASS
- **Source:** PASS
- **Staged source:** PASS
- **Build ARM64:** PASS
- **XZ + SHA-256:** PASS
- **Preflight REL-015:** PASS
- **Validador final:** PASS
- **Publicação da prerelease:** PASS
- **Imagem:** `PU2PNY-OS-0.3.20-alpha-arm64.img.xz`
- **Tamanho:** 614874612 bytes
- **SHA-256 da imagem:** `f42756bfcce537a7890b6296db3da3258fd8e909a45c7856f1530c8b363bed56`

### Download

- [Release PU2PNY-OS 0.3.20 Alpha](https://github.com/PU2PNY/2PNY-OS/releases/tag/v0.3.20-alpha)
- [Imagem ARM64](https://github.com/PU2PNY/2PNY-OS/releases/download/v0.3.20-alpha/PU2PNY-OS-0.3.20-alpha-arm64.img.xz)
- [SHA-256](https://github.com/PU2PNY/2PNY-OS/releases/download/v0.3.20-alpha/PU2PNY-OS-0.3.20-alpha-arm64.img.xz.sha256)

A publicação e os gates acima são validação **SW/CI**. Eles não substituem teste físico em Raspberry Pi + MMDVM + display.

## Baseline protegido

A regra permanente do projeto é:

> **funcionando + aprovado = preservar**

DMR simplex TX/RX comprovadamente funcional é baseline obrigatório. Problemas de duplex devem ser corrigidos sem reescrever ou regredir simplex.

O mesmo princípio vale para rede, wizard, RF, displays, protocolos, painel, atualização e demais módulos.

## Principais mudanças da 0.3.20

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

Continuam **HW PENDENTE** na 0.3.20:

- D-Star RF real e troca de refletor por comando do rádio;
- DMR duplex TX/RX e áudio em ambos os sentidos;
- regressão física completa do DMR simplex nesta imagem;
- Nextion física e confirmação COMOK;
- PU2PNY Moderno V2 em display real;
- BER/RSSI/S-meter reais;
- Direct entre dois hotspots reais;
- demais comportamentos explicitamente marcados como HW PENDENTE na TEST_MATRIX.

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
