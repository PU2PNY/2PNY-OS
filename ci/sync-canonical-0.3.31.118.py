#!/usr/bin/env python3
from pathlib import Path
import argparse

p=argparse.ArgumentParser()
p.add_argument('--runtime-commit',required=True)
p.add_argument('--image-sha256',required=True)
p.add_argument('--run-url',required=True)
p.add_argument('--vps',default='BLOQUEADO')
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

append_once('PU2PNY-OS_MASTER_SPEC.md','REL-028',r'''
## 2026-10-07 — ciclo 0.3.31.118: hotfix Nextion ON7LDS

### DISPLAY-026 — Porta virtual ON7LDS não privilegiada
Quando o renderer `on7lds-compatible` for usado, o NextionDriver deve continuar executando como usuário não privilegiado e criar/publicar seu PTY exclusivamente em `/run/2pny-nextiondriver/ttyNextionDriver`, dentro do `RuntimeDirectory` gerenciado pelo systemd. Não é permitido resolver a compatibilidade elevando o driver a root ou concedendo escrita geral em `/dev`. O caminho consumido por MMDVMHost e o caminho compilado no driver devem ser idênticos.

### REL-028 — 0.3.31.118 corrige somente a integração do PTY ON7LDS
A 0.3.31.118 parte da imagem publicada 0.3.31.117 e substitui somente o binário endurecido `NextionDriver-pu2pny`, a identidade de versão/backend e documentação/gates. MMDVMHost, DMR/D-Star/YSF, helpers RF/protocolo, rede, wizard, `2pny-display-apply`, unit systemd e UIs permanecem byte-idênticos à 0.3.31.117. Nextion física permanece HW PENDENTE após o build.
''')

append_once('PU2PNY-OS_RELEASE_STATUS.md','REL-028',f'''
## PU2PNY-OS 0.3.31.118 — HOTFIX NEXTION / CANDIDATA PARA TESTE FÍSICO

- **Feedback HW da 0.3.31.117:** DISPLAY-025 FALHOU. Nextion `NX3224T024_011R` 320x240 foi confirmada por COMOK, porém HMI `USE NextionDriver - ON7LDS` permaneceu no splash. A tentativa do renderer ON7LDS falhou e o rollback para `mmdvmhost-native` preservou MMDVMHost/DMRGateway ativos.
- **Causa raiz:** upstream fixa `/dev/ttyNextionDriver`; a 0.3.31.117 roda como `mmdvm` e espera `/run/2pny-nextiondriver/ttyNextionDriver`.
- **DISPLAY-026:** binário recompilado com PTY em RuntimeDirectory não privilegiado; nenhum root extra e nenhuma escrita geral em `/dev`.
- **REL-028 / base:** `v0.3.31.117`, SHA-256 base `c323d796135d8e69eca9240d50e40a8f529d79b1992d94a7753946f88a4f403b`.
- **Commit de runtime/build:** `{a.runtime_commit}`.
- **SW/CI:** APROVADO em {a.run_url}.
- **VPS:** {a.vps}.
- **Imagem SHA-256:** `{a.image_sha256}`.
- **HW:** PENDENTE para comprovar saída do splash ON7LDS e standby/RX/TX reais. Não PROD.
''')

append_once('PU2PNY-OS_TEST_MATRIX.md','REL-028',f'''
## 0.3.31.117 feedback HW / 0.3.31.118 — REL-028

| ID | Caso | Nível | Estado | Evidência/limite |
|---|---|---|---|---|
| DISPLAY-025-HW-117 | HMI ON7LDS físico sai do splash com renderer avançado | HW | FALHOU | HMI ficou em `USE NextionDriver - ON7LDS`; apply falhou e rollback restaurou `mmdvmhost-native` |
| DISPLAY-025-ROLLBACK-117 | Falha de renderer preserva rádio/config anterior | HW | APROVADO | MMDVMHost e DMRGateway permaneceram ativos após rollback |
| DISPLAY-026-A | Driver compilado usa `/run/2pny-nextiondriver/ttyNextionDriver` e não `/dev/ttyNextionDriver` | SW/CI | APROVADO | {a.run_url} |
| DISPLAY-026-B | unit continua não-root + RuntimeDirectory; display-apply usa o mesmo PTY | SW/CI | APROVADO | {a.run_url} |
| REL-028 | Imagem 0.3.31.118 preserva hashes do runtime 0.3.31.117 exceto NextionDriver/backend/version | SW/CI | APROVADO | SHA-256 `{a.image_sha256}` |
| REL-028-VPS | reprodução/validação não-RF | VPS | {a.vps} | VPS não substitui Nextion física |
| REL-028-HW | Nextion ON7LDS sai do splash e acompanha standby/RX/TX | HW | PENDENTE | novo teste físico obrigatório |
''')

append_once('PU2PNY-OS_CHANGELOG.md','REL-028',f'''
## 0.3.31.118 — 2026-10-07 — REL-028 / DISPLAY-026

- Registrado HW FAIL da compatibilidade ON7LDS na 0.3.31.117: Nextion `NX3224T024_011R` foi confirmada por COMOK, mas permaneceu no splash do HMI `USE NextionDriver - ON7LDS`; a aplicação do renderer avançado falhou e executou rollback seguro.
- Causa raiz confirmada em código/upstream: NextionDriver usa `/dev/ttyNextionDriver`, enquanto a integração 0.3.31.117 roda como `mmdvm` e espera `/run/2pny-nextiondriver/ttyNextionDriver`.
- DISPLAY-026 recompila o mesmo upstream pinado e o mesmo hardening da 0.3.31.117, alterando somente `NEXTIONDRIVERLINK` para o RuntimeDirectory não privilegiado.
- Ponto de retorno: `backup/0.3.31.117-nextion-hw-fail-20261007` @ `088ba5901bfc918503430df658f1a7b5728ef64e`.
- Build/runtime commit: `{a.runtime_commit}`; imagem SHA-256 `{a.image_sha256}`; SW/CI: {a.run_url}; VPS: {a.vps}; HW: PENDENTE.
''')
