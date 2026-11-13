# PU2PNY-OS 5.12 — feedback físico e decisão de correção

Data: 2026-11-13. Branch: `release/pu2pny-5.12`. Baseline de código: `release/pu2pny-5.11` / release `pu2pny-v5.11.000`. Issue de rastreio: [#23](https://github.com/PU2PNY/2PNY-OS/issues/23).

## 1. Evidências por equipamento

| Equipamento | Versão efetivamente informada | Evidência | Classificação |
| --- | --- | --- | --- |
| Raspberry Pi 3B Rev 1.2 ARM64 | 5.10.000 | Boot 7min55; serviços de manutenção e listas atrasam o alvo; subtensão `0x50005` | HW FALHOU na 5.10 |
| Raspberry Pi 3B Rev 1.2 ARM64 | 5.11.000 | Boot ainda não concluído aos 202 s; MMDVMHost reiniciando; retomada cancelada após 45s; display-detect e operational-apply falharam; Wi-Fi conectado | HW FALHOU/parcial na 5.11 |
| Raspberry Pi 4B Rev 1.2 ARM64 | 5.11.000 | Boot 8min30; DMRGateway não permaneceu ativo (duas tentativas com rollback); D-Star mostra `connected:false`; display SIGSEGV; Avahi falhou; subtensão `0x50005` | HW FALHOU/parcial na 5.11 |
| Orange Pi Zero H2+ | 5.11 (relato) | Estação associou ao AP, mas painel HTTP não abriu | HW FALHOU (sem log específico) |
| Raspberry Pi Zero W ARM32 | 5.11 (relato no prompt) | AP/painel não abriu; sem diagnóstico técnico anexado nesta rodada | Relato HW; causa NÃO VERIFICADA |
| NanoPi NEO H3 | 5.11 | Sem teste físico anexado | HW PENDENTE |

**Atenção:** os dois logs 5.11 não são ambos Pi 3: um é Pi 3 e outro é Pi 4. Não misturar versões ou dados de placas.

## 2. Causas encontradas no código e correções P0 isoladas

### BOOT-512 — Manutenção bloqueando inicialização
- **Causa confirmada no fonte:** `ci/patch-image-5.10.py` incluiu `ExecStartPre=/bin/sleep 300` em `2pny-auto-maintenance.service` e `2pny-hostfiles-update.service`. A 5.11 adicionou apenas `Nice=19`, prioridade de I/O e `CPUWeight=10`; isso não remove o bloqueio de dependências.
- **Correção 5.12 P0 em código:** `ci/patch-image-5.12.py` faz preflight da versão e das unidades; preserva backups; remove o drop-in que adicionava `sleep 300`; retira ligações diretas de manutenção/listas do `multi-user.target` quando presentes; preserva o timer já existente de hostfiles e adiciona timer específico para manutenção depois de oito minutos.
- **Evidência SW:** `ci/test-boot-5.12.py` reproduz e verifica a transição, a preservação de timer e a rejeição segura de base divergente.
- **Gate HW:** repetir boot e medir painel, RF e `systemd-analyze`. Não declarar meta de 45 s alcançada antes da medição real.

### NET-512 — AP Orange Pi conectado, painel indisponível
- **Causa de empacotamento confirmada no fonte:** o transplante `ci/build-board-5.11.py` copiava unidades e vínculos somente com glob `2pny-*`; o servidor HTTP é `2pnyd.service` e ficava excluído dessa seleção.
- **Correção 5.12 P0 em código:** `ci/build-board-5.12.py` copia e exige a unidade `2pnyd.service`, seu link de inicialização `multi-user.target.wants/2pnyd.service`, verifica o binário e preserva as outras unidades. Também transplanta unidades `pu2pny-capabilities.*` quando presentes.
- **Evidência SW:** `ci/test-board-5.12.py` reproduz a exclusão anterior e passa no transplante; falha deliberadamente quando falta unidade ou vínculo.
- **Gate HW:** ligar a Orange Pi com AP e provar `http://10.43.0.1/` acessível; se não, inspecionar servidor :80, lease DHCP, gateway, DNS e estado do serviço. AP associado não comprova HTTP funcional.

## 3. Falhas ainda sem correção comprovada

| ID | Evidência | Próxima investigação | Estado |
| --- | --- | --- | --- |
| PROTO-512 | DMRGateway encerra durante aplicar configuração, rollback ocorreu | `journalctl -u 2pny-dmrgateway`, INI sanitizado, conflitos de porta, preflight da rede, sem mexer no RF aprovado | HW FALHA / raiz não verificada |
| DSTAR-512 | `gateway_active` coexistindo com `connected:false`, embora o testador relate link real | distinguir processo, confirmação do protocolo e tráfego real; verificar DStarGateway e módulo XLX | EM INVESTIGAÇÃO |
| RF-512 | MMDVMHost reinicia repetidamente; retorno rápido aborta após 45 s | ordem de systemd, serial `/dev/serial0`, logs completos do MMDVM, sem hardcode de ttyUSB/ttyACM | HW FALHA / raiz não verificada |
| DISPLAY-512 | SIGSEGV do serviço MMDVM-Display; campos Nextion ausentes | crash/coredump sanitizado e rota de telemetria; manter ON7LDS DISPLAY-041 intacto | HW FALHA / raiz não verificada |
| NET-513 | Avahi/mDNS falhou e houve conflito de hostname em equipamentos distintos | distinguir colisão de nomes de falha no serviço; não supor dois hotspots como única causa | HW FALHA / raiz não verificada |
| HW-512 | `get_throttled=0x50005` em Pi 3/Pi 4 | testar fonte/cabo adequados e repetir medições; não alegar correção por software | HW FALHA elétrica |

## 4. Regras de preservação e solicitações adicionais

- Baselines: DMR simplex, D-Star simplex, YSF simplex, NextionDriver ON7LDS aprovado (DISPLAY-041), setup/AP e rollback. Nunca executar flash HMI/TFT automático.
- A especificação propõe endereços por placa e IP novo `192.168.4.1`, enquanto a baseline da especificação atual exige `10.43.0.1`. **Não alterar IP base em patch P0**: registrar NET-514 como solicitação futura, testar transição/compatibilidade e rollback antes.
- UI-512: redesign conforme princípios Apple Human Interface Guidelines, recursos offline, CSS leve, contraste, acessibilidade, modo claro/escuro, PT/EN/ES, navegação mobile/desktop, baixo CPU. **PENDENTE**, exige separar contrato UI, inventário e testes de regressão antes de substituir painel.
- HOST-512: nomes únicos por placa e para dois hotspots iguais; **PENDENTE**, pois colisão de mDNS não comprova o mecanismo de identificação pretendido. Estudar identificador estável sem revelar segredos e sem mudar nome após provisionamento.
- PROTO-513 / P2P-512 / APRS-512 / UPDATE-512: backlog funcional adicional do prompt de v5.12 continua explícito e auditável; nem a presença de código da 5.11 nem o CI comprovam RF, NAT, entrega de SMS, OTA ou displays físicos.

## 5. Critério para classificar qualquer build

O patch BOOT-512 e o empacotamento NET-512 só são SW PASS quando os testes respectivos executarem com sucesso; a imagem é apenas candidata ao teste físico depois de CI completo, verificação de integridade XZ, SHA-256, commit/tag/asset e manifesto do filesystem. Nenhuma imagem nesta etapa prova correção de DMR/D-Star/YSF, AP da Orange Pi ou Nextion físico.

Referências:
- [Repositório PU2PNY-OS](https://github.com/PU2PNY/2PNY-OS)
- [Código 5.10 que introduziu sleep](https://github.com/PU2PNY/2PNY-OS/blob/release/pu2pny-5.11/ci/patch-image-5.10.py)
- [Transplante de unidades 5.11](https://github.com/PU2PNY/2PNY-OS/blob/release/pu2pny-5.11/ci/build-board-5.11.py)
- [Baseline Nextion](https://github.com/PU2PNY/2PNY-OS/blob/release/pu2pny-5.11/docs/PU2PNY-OS_DISPLAY_BASELINE.md)
- [systemd service](https://www.freedesktop.org/software/systemd/man/latest/systemd.service.html)
- [systemd timer](https://www.freedesktop.org/software/systemd/man/latest/systemd.timer.html)
