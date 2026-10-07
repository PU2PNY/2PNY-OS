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

append_once('PU2PNY-OS_MASTER_SPEC.md','REL-029',r'''
## 2026-10-07 — ciclo 0.3.31.119: renderer padrão MMDVM/Nextion

### DISPLAY-027 — Nextion somente por caminhos padrão MMDVM/ON7LDS
O renderer Nextion específico `pu2pny-modern-v2` deixa de ser uma opção ativa do sistema. Para Nextion conectada ao modem, o painel deve oferecer no próprio campo **Renderer** somente perfis compatíveis com o ecossistema MMDVM: `Modem · G4KLX` (`ScreenLayout=0`), `Nextion · ON7LDS L2` (`ScreenLayout=2`) pelo renderer nativo do MMDVMHost, e `Nextion · ON7LDS L3/L3 HS` (`ScreenLayout=3/4`) pelo NextionDriver endurecido quando esse intermediário for necessário. O valor `ScreenLayout=0` deve permanecer zero durante persistência/aplicação; é proibido tratá-lo como valor ausente/falso. O hardware físico pode ser identificado por `connect/comok`, mas modelo/resolução não autorizam inferir qual HMI/layout foi gravado. Quando o HMI não puder ser provado, a seleção manual é obrigatória. Nenhum HMI/TFT é gravado automaticamente e permanece a regra de exatamente um writer.

Referências técnicas: MMDVM-Host oficial (`https://github.com/g4klx/MMDVM-Host`) fornece Transparent Data (`setTransparentDataParams`, leitura/escrita transparente); NextionDriver ON7LDS (`https://github.com/on7lds/NextionDriver`) documenta operação `Port=modem` por Transparent Data com `SendFrameType=1`.

### REL-029 — 0.3.31.119 é overlay estritamente de display sobre 0.3.31.118
A 0.3.31.119 parte da imagem publicada 0.3.31.118. O delta de runtime é limitado a UI de Display, política `2pny-display-apply`, identidade do backend/versão e documentação/gates. MMDVMHost, NextionDriver endurecido, DMRGateway, DMR/D-Star/YSF, RF, frequências, offsets, rede, wizard e demais serviços permanecem protegidos por gate de hash. A aprovação de saída real do splash, standby/RX/TX e interação com a Nextion exige HW real.
''')

append_once('PU2PNY-OS_RELEASE_STATUS.md','REL-029',f'''
## PU2PNY-OS 0.3.31.119 — CANDIDATA PARA TESTE FÍSICO

- **Escopo:** somente Display/Nextion — DISPLAY-027 + REL-029.
- **Mudança ativa:** removida a opção Nextion `PU2PNY Moderno V2`; Renderer passa a oferecer somente Modem/G4KLX, ON7LDS L2, ON7LDS L3 e ON7LDS L3 HS.
- **Correção adicional:** `ScreenLayout=0` deixa de cair no antigo fallback por avaliação booleana de zero.
- **Detecção:** modelo/resolução continuam automáticos por evidência real; HMI/layout desconhecido exige escolha manual.
- **Base:** `v0.3.31.118`, SHA-256 `111db204ab8f407aa0b25f503db0c612f3fc59575c437340314f173bd12d6dfc`.
- **Commit de runtime/build:** `{a.runtime_commit}`.
- **SW/CI:** APROVADO em {a.run_url}.
- **VPS:** {a.vps}.
- **Imagem SHA-256:** `{a.image_sha256}`.
- **HW:** PENDENTE — Nextion física deve comprovar saída do splash e atualização de standby/RX/TX. Não PROD.
''')

append_once('PU2PNY-OS_TEST_MATRIX.md','REL-029',f'''
## 0.3.31.119 — DISPLAY-027 / REL-029

| ID | Caso | Nível | Estado | Evidência/limite |
|---|---|---|---|---|
| DISPLAY-027-A | UI Nextion não expõe `pu2pny-modern-v2` e oferece G4KLX 0 / ON7LDS 2 / ON7LDS 3 / ON7LDS 4 | SW/CI | APROVADO | {a.run_url} |
| DISPLAY-027-B | `ScreenLayout=0` persiste/aplica como zero, sem fallback para layout 9 | SW/CI | APROVADO | {a.run_url} |
| DISPLAY-027-C | G4KLX/L2 usam MMDVMHost nativo; L3/L3 HS usam NextionDriver endurecido + Transparent Data; um writer por vez | SW/CI | APROVADO | {a.run_url} |
| DISPLAY-027-D | modelo/resolução por COMOK não é convertido em HMI/layout inventado | SW/CI | APROVADO | política e UI validadas em {a.run_url}; prova física depende do modem |
| REL-029 | imagem 0.3.31.119 preserva por hash MMDVMHost, NextionDriver, RF/protocolos/rede/wizard | SW/CI | APROVADO | SHA-256 `{a.image_sha256}` |
| REL-029-VPS | subset não-RF | VPS | {a.vps} | VPS não substitui Nextion física |
| REL-029-HW | Nextion real sai do splash e acompanha standby/RX/TX no perfil correto | HW | PENDENTE | teste físico obrigatório |
''')

append_once('PU2PNY-OS_CHANGELOG.md','REL-029',f'''
## 0.3.31.119 — 2026-10-07 — REL-029 / DISPLAY-027

- Removido do fluxo ativo de Nextion o renderer `PU2PNY Moderno V2`.
- O seletor Renderer agora apresenta diretamente os quatro perfis padrão suportados: Modem/G4KLX (`0`), ON7LDS L2 (`2`), ON7LDS L3 (`3`) e ON7LDS L3 HS (`4`).
- Corrigido o parse de layout que convertia `ScreenLayout=0` em fallback porque zero era tratado como falso.
- Mantida detecção não destrutiva de hardware; modelo físico não é usado para inventar HMI/layout. Quando não houver evidência, o operador escolhe o Renderer manualmente.
- Mantidos NextionDriver endurecido, PTY em `/run/2pny-nextiondriver/ttyNextionDriver`, Transparent Data com `SendFrameType=1`, single-writer e proibição de flash automático.
- Referência oficial adicionada: `g4klx/MMDVM-Host` para Transparent Data; ON7LDS NextionDriver para o caminho `Port=modem`.
- Base/rollback: `v0.3.31.118` / branch `pu2pny-os-0.3.31.118-nextion-hotfix`.
- Build/runtime commit: `{a.runtime_commit}`; imagem SHA-256 `{a.image_sha256}`; SW/CI: {a.run_url}; VPS: {a.vps}; HW: PENDENTE.
''')
