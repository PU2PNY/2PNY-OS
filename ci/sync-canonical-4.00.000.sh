#!/bin/bash
set -euo pipefail

append_file_once() {
  local file="$1" marker="$2" payload="$3"
  grep -Fq -- "$marker" "$file" || printf '\n%s\n' "$payload" >> "$file"
}

master="$(cat <<'EOF'
## 4.00.000 — Ecossistema global orientado por capacidades

### ARCH-007 — Inventário global de capacidades
- PU2PNY-OS deve detectar e expor capacidades reais do host, modem, gateways, displays, transcoder e acesso remoto sem presumir que presença de pacote significa validação física.
- Estados devem distinguir pelo menos available, unavailable, unknown, disabled, blocked e error.
- Nenhuma capacidade pode ser promovida para HW/PROD sem evidência correspondente.
- Implementação deve ser event-driven ou de baixa frequência, sem polling agressivo, escrita RF ou chamadas externas repetitivas.

### ARCH-008 — Integração local Helix
- Helix Voice Engine é backend opcional e local para PCM/DSP/transcoding orchestration.
- Modos: off, shadow e process; padrão off.
- Falha, ausência ou timeout do Helix não pode bloquear boot, rede, RF, MMDVMHost ou o caminho de áudio legado.
- HXP1/local IPC permanece sem cloud/API no hot path.
- HVC permanece bloqueado para produção enquanto qualidade/FTO/interoperabilidade não estiverem aprovadas.
- AMBE/AMBE+2 não é declarado nativo do Helix; requer backend externo/licenciado/verificado quando aplicável.

### PROTO-050 — Matriz global de protocolos
- Preservar DMR simplex/duplex e gateways já aprovados; ampliar somente por módulos isolados.
- D-Star, YSF/C4FM, P25, NXDN e POCSAG/DAPNET permanecem suportados conforme hardware/firmware/gateway real detectado.
- M17, FM/SVXLink, AX.25/KISS/IL2P e extensões semelhantes só podem aparecer como disponíveis quando existir hardware/firmware/backend compatível e validado.

### DISPLAY-031 — Displays globais por capacidade
- Suportar detecção modular de Nextion, OLED, HD44780/LCDproc e demais famílias implementadas sem amarrar o sistema a uma única tela.
- Nextion continua com writer único, sem gravação automática de HMI/TFT e com gate HW para standby/RX/TX reais.

### NET-050 — Acesso remoto opcional
- Cloudflare Tunnel, Tailscale e ZeroTier são opcionais e desabilitados por padrão.
- Nenhum deles pode expor segredo, substituir uplink RF/protocolo, ou liberar backend bruto sem autenticação e política explícita.

### REL-050 — Gate 4.00.000
- Imagens ARM64 e ARMHF/ARMv6 devem preservar a baseline correta de cada arquitetura, passar CI estrutural, fsck/xz, SHA-256 e regressões SW aplicáveis.
- RF real, BER/RSSI reais, duplex físico e displays físicos continuam HW PENDENTE até evidência real.
EOF
)"

tests="$(cat <<'EOF'
### SW-400000-CAPABILITY-20261014 — APROVADO SW/CI
- Branch: pu2pny-os-4.00.000-ecosystem.
- Safety CI run 38574305041: PASS.
- Baseline Guard run 38574304897: PASS.
- Verificado: sintaxe Python/shell, patch backend, endpoint /api/capabilities, fixture de hardware, instalação systemd, cross-build backend ARM64 e ARMv6 e igualdade byte a byte dos handlers protegidos RF/DMR/display/rede/Ao Vivo.
- HW: PENDENTE.

### VPS-400000-CAPABILITY-20261014 — APROVADO VPS
- Host de teste SentinelX: WartyWallaby x86_64, kernel 6.1.0-10-amd64.
- Commit testado: 684820f49896d9a478644e7418932ed40a3a8870.
- Scanner de capacidades: PASS.
- Políticas no_network_probe/no_rf_write e hardware=pending: PASS.
- Cadeia completa do patch backend 4.00.000: PASS.
- go test do backend: PASS.
- Este resultado não valida RF, MMDVM físico, BER/RSSI, duplex RF, áudio/transcoding real ou display físico.

### SW-400000-HELIX-20261014 — PARCIAL / BLOQUEADO PARA PROD
- Helix é backend opcional, padrão off, com estados explícitos e fallback obrigatório.
- HXP1/DSP/self-test possuem evidência SW/ENV no repositório Helix-Voice.
- HVC final e AMBE/AMBE+2 nativo não estão aprovados para produção; não declarar transcoder integral sem backend verificado.
- HW/RF/audio real: PENDENTE.
EOF
)"

release="$(cat <<'EOF'
### 4.00.000 — Ecossistema global
- Estado: EM TESTE / candidata para teste físico após build.
- Branch: pu2pny-os-4.00.000-ecosystem.
- Base protegida ARMHF/ARMv6: 0.3.31.124 / commit 6e7dc53d94a80d8860ce54f513b738313907e5b8.
- Base protegida ARM64: 0.3.31.122, última linha ARM64 protegida antes da trilha Pi Zero.
- Implementado: inventário global de capacidades, /api/capabilities, serviço event-driven/baixa frequência, modelo Helix opcional/default-off e gates de não regressão.
- Safety CI, Baseline Guard e validação VPS da camada 4.00.000: PASS.
- Build dual ARM64/ARMHF: EM TESTE até workflow 4.00.000 concluir.
- HW RF/display/audio: PENDENTE; não classificar como produção.
EOF
)"

changelog="$(cat <<'EOF'
### 4.00.000 (2026-10-14)
- Iniciado ecossistema global orientado por capacidades, sem amarrar o PU2PNY-OS a uma Raspberry Pi, um modem MMDVM ou um display específicos.
- Adicionado inventário conservador de hardware/protocolos/display/transcoder/acesso remoto e endpoint /api/capabilities.
- Adicionada atualização por PathChanged com fallback de 15 minutos, sem polling agressivo e sem escrita RF.
- Adicionado gate CI que prova handlers protegidos RF/DMR/display/rede/Ao Vivo byte-idênticos à cadeia baseline antes da camada 4.00.000.
- Helix passa a ser backend opcional local, pinado, padrão off; HVC e AMBE nativo continuam bloqueados enquanto faltarem gates próprios.
- A família 4.00.000 usa artefatos por arquitetura quando necessário; não forçar uma imagem única que invalide Pi Zero/ARMv6 ou ARM64.
- Validação VPS da camada de capacidades/backend concluída sem promover nenhum estado para HW.
EOF
)"

append_file_once PU2PNY-OS_MASTER_SPEC.md 'ARCH-007 — Inventário global de capacidades' "$master"
append_file_once PU2PNY-OS_TEST_MATRIX.md 'SW-400000-CAPABILITY-20261014' "$tests"
append_file_once PU2PNY-OS_RELEASE_STATUS.md '4.00.000 — Ecossistema global' "$release"
append_file_once PU2PNY-OS_CHANGELOG.md '4.00.000 (2026-10-14)' "$changelog"

grep -Fq 'ARCH-007 — Inventário global de capacidades' PU2PNY-OS_MASTER_SPEC.md
grep -Fq 'VPS-400000-CAPABILITY-20261014' PU2PNY-OS_TEST_MATRIX.md
grep -Fq '4.00.000 — Ecossistema global' PU2PNY-OS_RELEASE_STATUS.md
grep -Fq '4.00.000 (2026-10-14)' PU2PNY-OS_CHANGELOG.md

echo CANONICAL_400000_SYNC_OK
