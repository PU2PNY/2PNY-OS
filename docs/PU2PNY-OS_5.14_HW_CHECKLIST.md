# PU2PNY-OS 5.14 — ALPHA para teste físico

**Base:** overlay sobre a 5.12.002 P2 publicada (mantém todas as correções da 5.13.003).
**Escopo 5.14 (bloco A + H):** destravar o primeiro acesso na Orange Pi Zero / NanoPi e deixar o cabeçalho/banner do wizard responsivo. **Não altera RF, MMDVMHost, gateways, o probe de hardware protegido nem a baseline Nextion.**
**Estado:** `ALPHA_HW_TEST_CANDIDATE` · CI SW/VPS · **HW NÃO VERIFICADO · PROD NÃO APROVADO.** Preserve o cartão anterior para rollback.

## O que mudou (requisitos)

- **WIZ-514 — wizard não congela.** A etapa "Preparando hardware" não fica mais presa em 12%. A espera do probe caiu de 60 s para 30 s e, se a detecção automática falhar ou demorar, o botão **"Ir para configuração básica"** é liberado com um aviso claro. O avanço automático continua acontecendo **somente** quando a MMDVM é confirmada de verdade — nenhum dado de MMDVM é inventado.
- **WIZ-514 — diagnóstico.** Quando o probe não conclui, o sistema grava o **modelo real da placa** e o **motivo** da falha em `/var/lib/2pny/hardware-probe.json` (campo `probe_error`), para que o próximo teste aponte a causa exata.
- **UI-514 — banner responsivo.** Cabeçalho, marca e logo do wizard não quebram em telas pequenas; imagens escalam sem estourar o layout.
- O **probe de hardware protegido não foi alterado**. A correção de fundo da detecção na Orange (se a MMDVM realmente não for reconhecida) depende da evidência do `probe_error` deste teste.

## Checklist físico (Orange Pi Zero H2+ e, se possível, NanoPi NEO / Raspberry 32/64)

1. Gravar `pu2pny-opizero-5.14.000.img.xz` (conferir SHA-256) em cartão separado.
2. Ligar, conectar na rede AP e abrir `http://10.43.0.1/`.
3. **Wizard — etapa Hardware:** confirmar que **não trava em 12%**. Em no máximo ~35 s deve aparecer o resultado (MMDVM detectada **ou** aviso de que pode continuar).
   - [ ] Não congela em 12%
   - [ ] Mostra o modelo da placa (não fica "Detectando..." para sempre)
   - [ ] Se não detectou, o botão "Ir para configuração básica" fica clicável
4. **Banner/responsivo:** abrir o wizard no celular e no PC; o cabeçalho/logo não quebra em nenhum tamanho.
   - [ ] Celular (tela estreita) OK
   - [ ] PC OK
5. **Se a MMDVM não foi detectada:** anotar/baixar `probe_error` (página Expert / dados técnicos) e enviar — é o que aponta a causa exata na próxima versão.
6. **Raspberry (regressão):** confirmar que o wizard e a detecção na Raspberry continuam como antes (sem mudança intencional).
   - [ ] Raspberry sem regressão

## Limites honestos

- A **lista automática de Wi-Fi** pode continuar vazia na Orange: o rádio é único e está ocupado como AP. Use o **campo manual de SSID/senha**.
- **Cabo** só conta como "internet" se o roteador entregar endereço (DHCP). Sem endereço, use "Continuar sem internet".
- Se a MMDVM realmente não for reconhecida, a configuração de RF ainda não vai completar nessa placa — mas o wizard **não trava mais**, e o `probe_error` dirá o porquê.
- VPS/CI não comprovam RF, UART/GPIO, BER/RSSI, Nextion físico nem associação Wi-Fi real.
