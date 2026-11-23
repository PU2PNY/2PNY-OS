# PU2PNY-OS 5.15 — ALPHA para teste físico

**Base:** overlay sobre a 5.12.002 P2 (mantém 5.13.003 + 5.14).
**Escopo 5.15:** aviso de atualização (OTA) consertado, YSF reconecta sozinho, medição do tempo de "ativar perfil", e guia de gravação. **Não reescreve RF, o probe protegido, MMDVMHost nem os gateways.**
**Estado:** `ALPHA_HW_TEST_CANDIDATE` · CI SW · **HW NÃO VERIFICADO · PROD NÃO APROVADO.** Use cartão separado (rollback).

## Como gravar no cartão (importante — resolve o problema do Rufus)

A imagem é `.img.xz` (compactada). **O Rufus não abre `.xz` direto.** Opções, da mais fácil para a mais trabalhosa:

1. **Balena Etcher** (recomendado): abre o `.img.xz` direto, escolhe o cartão e grava. 1 clique. https://etcher.balena.io
2. **Raspberry Pi Imager**: "Usar imagem personalizada" → selecione o `.img.xz` → grave. https://www.raspberrypi.com/software
3. **Rufus** (se insistir): primeiro **extraia** o `.xz` com o 7-Zip (https://www.7-zip.org) para obter o `.img`; depois abra o Rufus, selecione o `.img`, e quando ele perguntar escolha **"Gravar em modo Imagem DD"**.

Sempre confira o **SHA-256** (está na release) antes de gravar.

## O que mudou (requisitos)

- **OTA-515 (aviso):** consertado o bug que fazia o painel mostrar "atualização disponível" **sempre**. Agora o aviso só aparece quando há uma versão realmente mais nova. (O auto-instalar com rollback é um passo seguinte, com seu teste.)
- **YSF-515 (reconexão):** o YSF/C4FM passa a **reconectar sozinho** ao refletor se cair (via override do serviço, sem mexer no RF protegido). Trocar de protocolo continua funcionando normalmente.
- **PERF-515 (medição):** o "ativar perfil" agora **mede e registra** quanto tempo levou (log `PERF-515 ... levou Xms` e campo `took_ms`). Isso mostra **onde** está a lentidão no Pi Zero, para o conserto certo no próximo ciclo.
- **Honesto:** a lentidão de fundo do perfil e a causa raiz do YSF estão nos scripts de RF protegidos; a 5.15 **mede e torna mais resiliente**, sem reescrever RF no escuro.

## Checklist físico

1. Gravar a imagem da placa (conferir SHA-256), em cartão separado.
2. **Pi Zero 32 — ativar perfil:** ativar um perfil e anotar quanto tempo levou. Depois baixe os dados técnicos (Sistema → "Baixar logs de erro") e me mande — a linha `PERF-515` diz onde está a lentidão.
   - [ ] Tempo de ativar perfil anotado / log enviado
3. **YSF (32 e 64):** conectar no YSF e verificar se, ao cair, ele **reconecta sozinho**.
   - [ ] Reconecta sozinho após queda
   - [ ] Se ainda cair sem reconectar, enviar o log
4. **OTA aviso:** na página Sistema, confirmar que mostra "Atualizado" quando está na versão mais nova (não mais "disponível" sempre).
   - [ ] Aviso correto
5. **Regressão:** DMR simplex e o que já funcionava continuam OK.
   - [ ] Sem regressão de DMR/RF

## Limites honestos

- A 5.15 **mede e torna o YSF mais resiliente**, mas o conserto de fundo (lentidão do perfil e causa raiz do YSF) depende do que seus logs mostrarem.
- VPS/CI não comprovam RF, UART/GPIO, BER/RSSI, Nextion físico nem associação Wi-Fi real.
