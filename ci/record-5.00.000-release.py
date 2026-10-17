#!/usr/bin/env python3
"""Idempotently record the verified PU2PNY-OS 5.00.000 candidate in canonical docs."""
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
MARK='<!-- PU2PNY-OS-5.00.000-VERIFIED -->'
COMMIT='d435e0d0322b5dbc5e334399edd332a8f5b1ba0b'
RUN='39003305505'
ARM32='97ce1886567288cca361d21c63a14e78ae0ffe20cff2eafeb3529b84c2e59ef2'
ARM64='55402edeb87a748decc88f86092b15ebd0ed6bd45c59cdb40e9cf21c75117797'

def append(path:str, block:str)->None:
    p=ROOT/path; text=p.read_text(errors='replace')
    if MARK in text: return
    p.write_text(text.rstrip()+"\n\n"+MARK+"\n"+block.strip()+"\n")

append('PU2PNY-OS_MASTER_SPEC.md', '''
## Geração 5.x — PU2PNY-OS 5.00.000

### ARCH-500 — Appliance modular 5.x
A geração 5.x mantém o PU2PNY-OS como sistema próprio, não fork de Pi-Star/WPSD. A primeira candidata instala Event Bus local, Hardware Manager conservador, Network Manager event-driven, Wi-Fi transacional via NetworkManager e Protocol Manager de dono único sobre uma base 4.00.001 verificada. Componentes opcionais permanecem desacoplados e dados sem evidência não são promovidos.

### NET-500 — Wi-Fi transacional e mDNS
Aplicação de Wi-Fi deve preservar o perfil anterior até associação+IPv4 válidos e restaurar perfil/AP em falha. `pu2pny.local` é o nome mDNS canônico em AP/STA/Ethernet.

### RF-500 — Baseline RF protegida
A imagem 5.00.000 não altera os arquivos críticos MMDVMHost/DMR protegidos durante o overlay; hashes são comparados antes/depois no CI. Isso é evidência SW, não aprovação RF/HW.

### REL-500 — Primeira candidata 5.x
ARM32 e ARM64 devem passar source gates, build, verificação de arquitetura, montagem, systemd verify, fsck somente leitura, XZ e SHA-256 antes de publicação. A ausência de teste físico mantém a classificação ALPHA / CANDIDATA PARA TESTE FÍSICO.
''')

append('PU2PNY-OS_RELEASE_STATUS.md', f'''
## PU2PNY-OS 5.00.000 — 2026-10-17

**Estado:** ALPHA / CANDIDATA PARA TESTE FÍSICO — NÃO PROD.  
**Branch:** `pu2pny-os-5.00.000-appliance`  
**Commit do artefato:** `{COMMIT}`  
**CI:** run `{RUN}` — ARM32 PASS, ARM64 PASS, publish PASS.  
**Base da imagem:** 4.00.001 verificada; 4.00.002 não foi usada como base estrutural por regressões físicas reportadas.

- ARM32: `PU2PNY-OS-5.00.000-arm32.img.xz`, 682213664 bytes, SHA-256 `{ARM32}`.
- ARM64: `PU2PNY-OS-5.00.000-arm64.img.xz`, 601373964 bytes, SHA-256 `{ARM64}`.
- CI comprovou: sintaxe/build, arquitetura, montagem, preservação dos arquivos RF protegidos, systemd verify, fsck read-only, XZ e checksum.
- HW PENDENTE: Raspberry/MMDVM/UART, RF↔NET, DMR/D-Star/YSF/P25/NXDN/POCSAG, Wi-Fi/AP/mDNS reais, Nextion/OLED, BER/RSSI.
- VPS: NÃO VERIFICADO nesta execução; o SentinelX disponível apontava para host não dedicado ao teste PU2PNY, portanto não foi usado para evitar impacto fora do projeto.
''')

append('PU2PNY-OS_TEST_MATRIX.md', '''
## PU2PNY-OS 5.00.000 — matriz da candidata inicial

| ID | Caso | Estado | Nível |
|---|---|---|---|
| TEST-500-SRC | Python/Shell/source gates 5.x | PASS | SW |
| TEST-500-ARM32 | Build + arquitetura ARM32/GOARM6 | PASS | SW |
| TEST-500-ARM64 | Build + arquitetura ARM64 | PASS | SW |
| TEST-500-BASE | SHA/XZ da base 4.00.001 | PASS | SW |
| TEST-500-RF-GUARD | Hashes de arquivos RF protegidos antes/depois | PASS | SW |
| TEST-500-SYSTEMD | Units 5.x + MMDVMHost verificadas offline | PASS | SW |
| TEST-500-FS | fsck + remontagem read-only | PASS | SW |
| TEST-500-XZ | XZ final + SHA-256 + publicação | PASS | SW |
| TEST-500-VPS | VPS dedicada PU2PNY | NÃO VERIFICADO | VPS |
| TEST-500-NET-HW | AP/Wi-Fi/Ethernet/pu2pny.local reais | PENDENTE | HW |
| TEST-500-RF-HW | MMDVM/UART e RF↔NET | PENDENTE | HW |
| TEST-500-DISPLAY-HW | Nextion/OLED físicos | PENDENTE | HW |
''')

append('PU2PNY-OS_CHANGELOG.md', f'''
## 2026-10-17 — PU2PNY-OS 5.00.000 Appliance Alpha

- Criada arquitetura 5.x com contrato de UI preservado.
- Adicionados Event Bus local, Hardware Manager sem escrita RF, Network Manager event-driven, Wi-Fi NetworkManager transacional com rollback e Protocol Manager de dono único.
- `pu2pny.local` reafirmado por Avahi; compatibilidade `mmdvmhost.service` é somente alias do serviço canônico, nunca segundo motor.
- Backend web preservado a partir da cadeia 4.00.001 com versão 5.00.000; arquivos críticos RF são protegidos por hash no CI.
- Builds ARM32 e ARM64 passaram no run `{RUN}` e foram publicadas como prerelease `v5.00.000` no commit `{COMMIT}`.
- ARM32 SHA-256 `{ARM32}`; ARM64 SHA-256 `{ARM64}`.
- Classificação: ALPHA / CANDIDATA PARA TESTE FÍSICO. Nenhum caso HW foi promovido por CI.
''')

print('DOCS_500000_RECORDED')
