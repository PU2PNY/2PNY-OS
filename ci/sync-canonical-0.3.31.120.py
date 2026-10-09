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

append_once('PU2PNY-OS_MASTER_SPEC.md','REL-030',r'''
## 2026-10-08 — ciclo 0.3.31.120: reaplicação Nextion + recuperação mDNS

### DISPLAY-028 — configuração Nextion deve reiniciar o writer selecionado
Ao aplicar ON7LDS L3/L3 HS, após a gravação atômica de `MMDVM-Host.ini`, o `NextionDriver` deve ser explicitamente reiniciado antes da validação do PTY. Apenas `systemctl enable --now` não é suficiente quando o serviço já está ativo. A falha de enable/restart deve preservar o rollback existente. Continuam obrigatórios: exatamente um writer, nenhuma gravação automática de HMI/TFT e nenhuma apropriação direta de `/dev/serial0` quando a UART pertence ao MMDVM.

### NET-038 — `pu2pny.local` deve ser reanunciado após mudança de uplink
Avahi deve anunciar explicitamente o hostname `pu2pny` por IPv4 e ser reanunciado de forma event-driven quando o NetworkManager sinalizar `up`, mudança DHCP ou conectividade. Esta correção não altera perfis Wi-Fi/Ethernet, DHCP, DNS externo, RF ou protocolos.

### REL-030 — 0.3.31.120 é overlay cirúrgico sobre 0.3.31.119
A 0.3.31.120 parte da imagem publicada 0.3.31.119. O delta é limitado a `2pny-display-apply`, Avahi/dispatcher mDNS, identidade do backend/versão e documentação/gates. MMDVMHost, NextionDriver binário, DMR/D-Star/YSF, RF, frequências, gateways, Wi-Fi profiles, wizard e demais caminhos permanecem protegidos por hash. Nextion real e resolução mDNS no equipamento do usuário exigem validação HW.
''')

append_once('PU2PNY-OS_RELEASE_STATUS.md','REL-030',f'''
## PU2PNY-OS 0.3.31.120 — CANDIDATA PARA TESTE FÍSICO

- **Escopo:** DISPLAY-028 + NET-038 + REL-030.
- **Nextion:** força restart controlado do NextionDriver após reaplicação da configuração, preservando rollback/single-writer.
- **mDNS:** Avahi anuncia `pu2pny.local` explicitamente e recebe reanúncio event-driven após mudança de uplink.
- **Base:** `v0.3.31.119`, SHA-256 `ab787f47c27566c9f057b3517320674c010904ea98b82e478993fb75a6fa3978`.
- **Commit de runtime/build:** `{a.runtime_commit}`.
- **SW/CI:** APROVADO em {a.run_url}.
- **VPS:** {a.vps}.
- **Imagem SHA-256:** `{a.image_sha256}`.
- **HW:** PENDENTE — validar Nextion física e `http://pu2pny.local/` no Raspberry Pi real. Não PROD.
''')

append_once('PU2PNY-OS_TEST_MATRIX.md','REL-030',f'''
## 0.3.31.120 — DISPLAY-028 / NET-038 / REL-030

| ID | Caso | Nível | Estado | Evidência/limite |
|---|---|---|---|---|
| DISPLAY-028-A | reaplicar ON7LDS executa enable + restart explícito do NextionDriver | SW/CI | APROVADO | {a.run_url} |
| DISPLAY-028-B | rollback e regra single-writer permanecem no helper existente | SW/CI | APROVADO | overlay cirúrgico validado em {a.run_url} |
| DISPLAY-028-HW | Nextion NX3224T024_011R exibe standby e acompanha RX/TX no perfil HMI correto | HW | PENDENTE | teste físico obrigatório |
| NET-038-A | Avahi configura `host-name=pu2pny` e IPv4 | SW/CI | APROVADO | {a.run_url} |
| NET-038-B | mudança NetworkManager dispara reanúncio Avahi sem polling | SW/CI | APROVADO | {a.run_url} |
| NET-038-HW | `http://pu2pny.local/` resolve após Wi-Fi/Ethernet e troca de uplink | HW | PENDENTE | teste físico obrigatório |
| REL-030 | imagem 0.3.31.120 preserva por hash MMDVMHost, NextionDriver binário, RF/protocolos, Wi-Fi profiles e wizard | SW/CI | APROVADO | SHA-256 `{a.image_sha256}` |
| REL-030-VPS | subset não-RF | VPS | {a.vps} | VPS não substitui hardware físico |
''')

append_once('PU2PNY-OS_CHANGELOG.md','REL-030',f'''
## 0.3.31.120 — 2026-10-08 — REL-030 / DISPLAY-028 / NET-038

- Corrigida reaplicação ON7LDS: após escrever a configuração, `NextionDriver` é habilitado e reiniciado explicitamente antes de validar o PTY; rollback existente é preservado.
- Mantidos sem alteração o binário NextionDriver, MMDVMHost e a regra de um único writer; nenhum HMI/TFT é gravado automaticamente.
- Corrigido `pu2pny.local`: Avahi recebe hostname explícito `pu2pny` e reanúncio event-driven nas mudanças relevantes do NetworkManager, sem polling.
- Nenhum perfil Wi-Fi/Ethernet, RF, DMR, D-Star, YSF, frequência, gateway ou wizard é alterado.
- Base/rollback: `v0.3.31.119` / branch `pu2pny-os-0.3.31.119-display-autodetect`.
- Build/runtime commit: `{a.runtime_commit}`; imagem SHA-256 `{a.image_sha256}`; SW/CI: {a.run_url}; VPS: {a.vps}; HW: PENDENTE.
''')
