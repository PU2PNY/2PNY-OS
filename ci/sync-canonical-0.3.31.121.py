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

def append_once(name,marker,block):
    path=repo/name; text=path.read_text()
    if marker in text:
        print(f'{name}: already contains {marker}'); return
    path.write_text(text.rstrip()+"\n\n"+block.strip()+"\n")

append_once('PU2PNY-OS_MASTER_SPEC.md','REL-031',r'''
## 2026-10-09 — ciclo 0.3.31.121: handoff real ON7LDS/NextionDriver

### DISPLAY-029 — NextionDriver precisa assumir a topologia antes do MMDVMHost
Quando uma Nextion ligada ao modem usar ON7LDS L3/L3 HS, a troca de renderer deve recriar de forma limpa o PTY do NextionDriver, usar o modo upstream `-i` para não abortar por detecção de processo concorrente/stale, iniciar o NextionDriver com a configuração já gravada, validar a existência da porta virtual e somente então estabilizar o MMDVMHost. A transição continua single-writer, com rollback automático e sem flash de HMI/TFT. Um estado `active` do renderer nativo não pode ser tratado como prova de saída visível na HMI.

### REL-031 — 0.3.31.121 é overlay estritamente de runtime Nextion sobre 0.3.31.120
A 0.3.31.121 parte da imagem publicada 0.3.31.120. O delta é limitado ao helper `2pny-display-apply`, unit `2pny-nextiondriver.service`, identidade de versão e documentação/gates. MMDVMHost, binário NextionDriver, DMR/D-Star/YSF, RF, rede/mDNS, Wi-Fi, wizard e UI permanecem protegidos por gate de hash. Aprovação visual exige HW real.
''')
append_once('PU2PNY-OS_RELEASE_STATUS.md','REL-031',f'''
## PU2PNY-OS 0.3.31.121 — CANDIDATA PARA TESTE FÍSICO
- **Escopo:** DISPLAY-029 + REL-031.
- **Causa tratada:** handoff ON7LDS/NextionDriver podia falhar antes de assumir a porta virtual; G4KLX/L2 `active` não comprova HMI compatível.
- **Mudança:** clean stop/start do NextionDriver, limpeza do PTY, flag upstream `-i`, validação conjunta NextionDriver + MMDVMHost + PTY e rollback.
- **Base:** `v0.3.31.120`, SHA-256 `43fa01b610519c3c8e63a474a6494a6cd6247b7750c8eb0815a9328b9ffe1a03`.
- **Commit de runtime/build:** `{a.runtime_commit}`.
- **SW/CI:** APROVADO em {a.run_url}.
- **VPS:** {a.vps}.
- **Imagem SHA-256:** `{a.image_sha256}`.
- **HW:** PENDENTE — saída visual standby/RX/TX e compatibilidade da HMI real precisam do Raspberry/MMDVM/Nextion do operador.
''')
append_once('PU2PNY-OS_TEST_MATRIX.md','REL-031',f'''
## 0.3.31.121 — DISPLAY-029 / REL-031
| ID | Caso | Nível | Estado | Evidência/limite |
|---|---|---|---|---|
| DISPLAY-029-A | unit NextionDriver usa PTY em RuntimeDirectory, clean start e `-i` upstream | SW/CI | APROVADO | {a.run_url} |
| DISPLAY-029-B | apply valida NextionDriver + MMDVMHost + PTY e mantém rollback/single-writer | SW/CI | APROVADO | {a.run_url} |
| DISPLAY-029-C | smoke ARM64 cria PTY com config `Port=modem` + Transparent Data sem hardware RF | SW/CI | APROVADO | {a.run_url} |
| REL-031 | imagem preserva por hash MMDVMHost, binário NextionDriver, RF/protocolos/rede/wizard/UI | SW/CI | APROVADO | SHA-256 `{a.image_sha256}` |
| REL-031-HW | HMI real mostra standby e acompanha RX/TX | HW | PENDENTE | teste físico obrigatório |
''')
append_once('PU2PNY-OS_CHANGELOG.md','REL-031',f'''
## 0.3.31.121 — 2026-10-09 — REL-031 / DISPLAY-029
- Corrigido handoff ON7LDS: NextionDriver passa por clean stop/start após a configuração ser gravada.
- PTY stale é removido antes do start; `-i` upstream evita abortar por instância detectada durante transição.
- Aplicação só confirma o modo após NextionDriver, `2pny-mmdvmhost.service` e PTY estarem simultaneamente estáveis; falha restaura a configuração anterior.
- MMDVMHost e binário NextionDriver permanecem byte-idênticos à 0.3.31.120.
- Build/runtime commit: `{a.runtime_commit}`; imagem SHA-256 `{a.image_sha256}`; SW/CI: {a.run_url}; HW: PENDENTE.
''')
