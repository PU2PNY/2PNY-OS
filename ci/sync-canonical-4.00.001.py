#!/usr/bin/env python3
"""Append the canonical 4.00.001 corrective decision once.

History is intentionally preserved: older display requirements remain in the
record and are explicitly superseded instead of being silently deleted.
"""
from pathlib import Path

repo=Path(__file__).resolve().parents[1]
marker='<!-- PU2PNY-OS-4.00.001-CANONICAL -->'
sections={
'PU2PNY-OS_MASTER_SPEC.md': r'''

<!-- PU2PNY-OS-4.00.001-CANONICAL -->
## PU2PNY-OS 4.00.001 — correção cirúrgica Display / timezone / ARM32

### DISPLAY-032 — Nextion padrão Pi-Star/WPSD/MMDVM
**Decisão:** supersede, por ordem explícita do usuário em 2026-10-14, qualquer requisito anterior que imponha renderer Nextion próprio do PU2PNY-OS, auto-provisionamento de HMI/TFT ou confirmação COMOK como pré-condição de ativação de tela ligada ao modem. O histórico anterior permanece apenas para auditoria.

**Requisito:** telas Nextion ligadas à porta do modem devem usar exclusivamente semântica compatível com G4KLX/MMDVMHost e ON7LDS NextionDriver: `ScreenLayout=0` (G4KLX), `2` (ON7LDS L2), `3` (ON7LDS L3) ou `4` (ON7LDS L3 HS); L3/L3 HS usam PTY + Transparent Data com `SendFrameType=1`; HMI/TFT existente nunca é sobrescrito automaticamente; o layout é escolhido conforme o HMI já instalado. Para display ligado ao modem, ausência de COMOK não pode reprovar a aplicação, pois o upstream não garante leitura/identificação física nesse caminho.

**Aceite mínimo:** SW deve provar configuração, exclusividade de writer, rollback e lifecycle systemd; HW deve provar imagem real aparecendo numa Nextion física. **Validação mínima final: HW.**

### BOOT-051 — fuso IANA persistente
Quando um fuso IANA válido for detectado/selecionado e salvo em `/var/lib/2pny/settings/clock.json`, o sistema deve reaplicá-lo localmente no boot, sem nova geolocalização ou polling externo. `timedatectl` é o caminho preferencial, com `/etc/localtime` + `/etc/timezone` como fallback local. **Validação mínima: VPS; persistência final também deve ser observada em HW.**

### PERF-051 — redução de wakeups do watcher Ao Vivo em ARM32
O watcher do snapshot Ao Vivo passa de 80 ms para 160 ms entre verificações, reduzindo pela metade os `stat`/wakeups ociosos desse loop sem mudar payload/API/SSE/RF. O aumento máximo teórico da observação do arquivo é de aproximadamente 80 ms. **Validação mínima: SW/VPS; desempenho percebido no Pi Zero permanece HW.**

### ARCH-010 — transcodificação/processamento por software
A estratégia aprovada é software/local, sem tornar hardware AMBE obrigatório. O Helix permanece isolado e fail-open. O estado técnico atual do Helix não autoriza declarar transcodificação AMBE/AMBE+2 ou HVC pronta para produção; interoperabilidade de codec legado continua **BLOQUEADA** até existir adaptador autorizado/licenciado e validação correspondente. A 4.00.001 não pode ativar silenciosamente um transcoder experimental, especialmente em ARMv6/Pi Zero.

### Baseline protegida 4.00.001
Por confirmação explícita do usuário, todo o restante que já está funcionando fica congelado e fora do escopo desta correção. A imagem 4.00.001 deve ser derivada dos artefatos imutáveis da 4.00.000 e comprovar por hashes que RF, DMR, gateways, Wi-Fi e demais helpers protegidos não sofreram alteração não autorizada.
''',
'PU2PNY-OS_RELEASE_STATUS.md': r'''

<!-- PU2PNY-OS-4.00.001-CANONICAL -->
## 4.00.001 — corretiva Display / timezone / ARM32 — EM TESTE

- Base de rollback: `v4.00.000`, preservada e não sobrescrita.
- Branch: `pu2pny-os-4.00.001-display-perf-timezone`.
- Evidência HW recebida: aplicação de Nextion falhou e a tela permaneceu sem imagem nos testes relatados em 32 e 64 bits; portanto Display da 4.00.000 não está aprovado em HW.
- DISPLAY-032: correção autorizada; validação física da nova imagem ainda **PENDENTE HW** até novo teste do usuário.
- BOOT-051: implementação e teste não-RF exigidos antes da candidata.
- PERF-051: redução de polling pode ser validada em SW/VPS; ganho real no Pi Zero permanece **PENDENTE HW**.
- ARCH-010: software/local é a direção aprovada, mas transcoding legado por Helix continua **BLOQUEADO PARA PROD** conforme a evidência do próprio projeto Helix.
- Todo o restante foi declarado funcionando pelo usuário e é baseline protegida; nenhuma mudança funcional fora deste escopo é autorizada.
- Classificação máxima antes do reteste físico: **CANDIDATA PARA TESTE FÍSICO**, nunca PROD.
''',
'PU2PNY-OS_TEST_MATRIX.md': r'''

<!-- PU2PNY-OS-4.00.001-CANONICAL -->
## Matriz 4.00.001

### HW-400000-DISPLAY-20261014 — FALHOU / HW
Evidência do usuário: em instalação física, nenhuma das configurações de display ativou a Nextion em 32 ou 64 bits; a UI informou rollback da configuração anterior. Esta evidência reprova somente o caminho Display/Nextion testado e não autoriza inferir BER, RSSI ou demais métricas RF.

### SW-400001-DISPLAY — EM TESTE
Critério: NextionDriver executado em foreground sob `Type=simple`; PTY `/run/2pny-nextiondriver/ttyNextionDriver`; MMDVMHost/Transparent Data nos parâmetros upstream; ausência de COMOK não bloqueia tela ligada ao modem; rollback mantém MMDVMHost operacional. HW físico continua obrigatório para APROVADO final.

### VPS-400001-TIMEZONE — EM TESTE
Critério: timezone IANA salvo em `clock.json`, reinício/execução do restore sem rede, timezone efetivo preservado; entrada inválida não altera `/etc/localtime`.

### SW-400001-PERF — EM TESTE
Critério: watcher Ao Vivo usa 160 ms em vez de 80 ms e nenhum contrato API/SSE é alterado. Ganho efetivo em Pi Zero não pode ser marcado APROVADO sem HW.

### SW-400001-BASELINE — EM TESTE
Critério: hashes dos arquivos protegidos de RF/protocolos/gateways/rede permanecem idênticos aos artefatos 4.00.000, exceto backend, display e timezone explicitamente autorizados.

### HW-400001-NEXTION — PENDENTE
Critério final: após gravar a 4.00.001 em Raspberry Pi real, selecionar o layout que corresponde ao HMI já gravado e observar a imagem/estado real da Nextion, sem regressão do MMDVMHost/RF.
''',
'PU2PNY-OS_CHANGELOG.md': r'''

<!-- PU2PNY-OS-4.00.001-CANONICAL -->
## 2026-10-14 — 4.00.001: display upstream, timezone persistente e ARM32 leve

- **DISPLAY-032:** por solicitação explícita do usuário, a política anterior de telas foi supersedida. A implementação passa a seguir o modelo Pi-Star/WPSD: G4KLX/ON7LDS via MMDVMHost e ON7LDS NextionDriver; nenhum HMI/TFT é auto-gravado e COMOK não é gate para display atrás do modem.
- Causa técnica confirmada no código upstream ON7LDS: a opção `-d` chama `go_daemon()`/fork. A unidade PU2PNY usava `Type=simple` junto com `-d`; 4.00.001 remove `-d` e deixa o systemd supervisionar o processo em foreground.
- O upstream também declara que `checkDisplay()` não consegue checar/atualizar displays conectados via `Port=modem`; portanto auto-identificação física não pode ser usada como condição para aplicar esse modo.
- **BOOT-051:** o fuso IANA salvo pelo painel é reafirmado no boot localmente, sem depender de nova detecção de região.
- **PERF-051:** o watcher de estado Ao Vivo reduz wakeups de 80 ms para 160 ms. Nenhuma alteração RF/gateway acompanha essa otimização.
- **ARCH-010:** software/local permanece a estratégia de transcodificação, mas o Helix atual continua experimental para HVC/codec legado e não é promovido silenciosamente a produção.
- A 4.00.000 permanece ponto de rollback; a 4.00.001 é derivada diretamente de seus artefatos para preservar todo o restante confirmado como funcionando.
''',
}

for name,body in sections.items():
    p=repo/name
    text=p.read_text()
    if marker in text:
        continue
    p.write_text(text.rstrip()+body.rstrip()+"\n")
    print('UPDATED',name)
