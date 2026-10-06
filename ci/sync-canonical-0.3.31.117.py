#!/usr/bin/env python3
from pathlib import Path
import argparse

p=argparse.ArgumentParser()
p.add_argument('--runtime-commit',required=True)
p.add_argument('--image-sha256',required=True)
p.add_argument('--run-url',required=True)
p.add_argument('--vps',default='NÃO VERIFICADO')
a=p.parse_args()
repo=Path(__file__).resolve().parents[1]

def append_once(name, marker, block):
    path=repo/name
    text=path.read_text()
    if marker in text:
        print(f'{name}: already contains {marker}')
        return
    path.write_text(text.rstrip()+"\n\n"+block.strip()+"\n")
    print(f'{name}: appended {marker}')

append_once('PU2PNY-OS_MASTER_SPEC.md','REL-027',r'''
## 2026-10-06 — ciclo 0.3.31.117: retomada de rede e compatibilidade Nextion

### NET-037 — Retomada automática do painel após handoff Wi-Fi
Depois de `NET-002` confirmar associação, IPv4 e persistência do perfil, a página que iniciou a troca deve procurar de forma limitada e sob demanda os destinos de retomada fornecidos pelo backend, priorizando `http://pu2pny.local/`, e navegar para o painel na LAN quando ele estiver alcançável. O mecanismo não autoriza polling contínuo nem transforma falha de navegador/cliente em falso sucesso de rede. Em Ethernet, o sistema deve garantir `pu2pny.local`/mDNS; um navegador externo não pode ser forçado a abrir sem uma requisição do próprio cliente.

### LIVE-023 — Barra Wi-Fi/Uplink usa apenas sinal real
No box Ao Vivo, quando o uplink padrão for Wi-Fi, a barra deve usar exclusivamente `wifi_signal`/RSSI medidos pelo backend (`nmcli`/`iw`). Quando o uplink for Ethernet, exibir Ethernet e RSSI `—`, sem converter presença de cabo em porcentagem fictícia. Ausência de telemetria Wi-Fi também resulta em `—`/barra vazia.

### DISPLAY-025 — Compatibilidade Pi-Star/WPSD/ON7LDS endurecida
Além do renderer nativo MMDVMHost e do PU2PNY Moderno já existentes, o sistema pode oferecer um renderer explícito `on7lds-compatible` para HMI Pi-Star/WPSD/ON7LDS. O driver deve ser compilado de uma revisão upstream fixa, operar com exatamente um writer, usar Transparent Data quando a Nextion estiver ligada ao modem e manter TFT/HMI existente sem gravação automática. Toda execução de shell originada da HMI e download autônomo de dados pelo driver são proibidos. Layout/HMI instalado continua distinto do modelo físico; COMOK comprova hardware, não o HMI. Nextion física permanece HW PENDENTE até teste real.

### REL-027 — 0.3.31.117 é overlay cirúrgico sobre 0.3.31.116
A 0.3.31.117 parte da imagem publicada 0.3.31.116 e altera somente UI de retomada/indicador de uplink, integração de display/Nextion, identidade de versão, build/gates e documentação. MMDVMHost binário, DMRGateway/helpers de protocolo, DMR/D-Star/YSF, RF, frequências, offsets, `2pny-network-switch`, `2pny-network-online` e wizard permanecem protegidos/byte-idênticos. Build exige ARM64, SHA-256, preflight montado, gate de hashes e classificação PARA TESTE FÍSICO. **Validação mínima:** SW/CI; VPS quando aplicável; HW obrigatório para Nextion física, RF e handoff real do dispositivo.
''')

append_once('PU2PNY-OS_RELEASE_STATUS.md','REL-027',f'''
## PU2PNY-OS 0.3.31.117 — CANDIDATA PARA TESTE FÍSICO

- **REL-027 / estado:** PARA TESTE FÍSICO; não promover a produção sem HW real.
- **Base imutável:** `v0.3.31.116` / commit `be75b68aa5549c15d538b1814ffd2df5987cb759`.
- **Commit de runtime/build:** `{a.runtime_commit}`.
- **SW/CI:** APROVADO na execução {a.run_url}.
- **VPS:** {a.vps}.
- **HW:** PENDENTE — Wi-Fi handoff real, Ethernet/mDNS no cliente, Nextion física, RF/DMR/D-Star/YSF e BER/RSSI RF não são aprovados por CI.
- **Imagem SHA-256:** `{a.image_sha256}`.
- **Escopo:** NET-037, LIVE-023, DISPLAY-025 e REL-027. Runtime RF/protocolos/rede transacional protegido.
''')

append_once('PU2PNY-OS_TEST_MATRIX.md','REL-027',f'''
## 0.3.31.117 — REL-027

| ID | Caso | Nível | Estado | Evidência/limite |
|---|---|---|---|---|
| NET-037 | Handoff pós-conexão usa `pu2pny.local`/resume URLs com tentativa limitada | SW/CI | APROVADO | {a.run_url}; HW real PENDENTE |
| LIVE-023 | Barra usa `wifi_signal`/RSSI real; Ethernet e ausência de telemetria não geram porcentagem | SW/CI | APROVADO | {a.run_url}; RSSI físico PENDENTE |
| DISPLAY-025-A | NextionDriver pinado compila ARM64 após hardening; `system()`/`popen()` removidos do source set | SW/CI | APROVADO | {a.run_url} |
| DISPLAY-025-B | Single-writer, Transparent Data, rollback e unit sandbox presentes na imagem | SW/CI | APROVADO | {a.run_url}; Nextion física PENDENTE |
| REL-027 | Imagem ARM64 monta, overlay aplica, protegidos mantêm hash, `xz -t` e SHA-256 passam | SW/CI | APROVADO | SHA-256 `{a.image_sha256}` |
| REL-027-VPS | Validação não-RF da candidata | VPS | {a.vps} | VPS não substitui HW |
| REL-027-HW | Wi-Fi/Ethernet/Nextion/RF em Raspberry Pi real | HW | PENDENTE | teste do operador obrigatório |
''')

append_once('PU2PNY-OS_CHANGELOG.md','REL-027',f'''
## 0.3.31.117 — 2026-10-06 — REL-027

- NET-037: após conexão Wi-Fi confirmada, a UI passa a reencontrar o painel por `pu2pny.local` e pelos endereços reais fornecidos pelo backend; nenhum navegador é falsamente considerado “autoaberto” em Ethernet.
- LIVE-023: `Wi-Fi / Uplink` passa a representar sinal Wi-Fi real; Ethernet mostra cabo sem RSSI/porcentagem inventada.
- DISPLAY-025: adicionada compatibilidade explícita Pi-Star/WPSD/ON7LDS com NextionDriver pinado em `03b904270c9cb54f720d71753fc209afb1d9598f`, hardening contra HMI→shell/download autônomo, Transparent Data para display no modem, single-writer e sem flash automático de HMI/TFT.
- Protegidos: MMDVMHost, DMR/D-Star/YSF, DMRGateway/helpers, RF, frequências, offsets, `2pny-network-switch`, `2pny-network-online` e wizard permanecem sem alteração pelo overlay.
- Build/runtime commit: `{a.runtime_commit}`; imagem SHA-256 `{a.image_sha256}`; SW/CI: {a.run_url}; VPS: {a.vps}; HW: PENDENTE.
''')
