# PU2PNY-OS 4.00.000 — Ecossistema MMDVM consolidado

Data: 2026-10-14. Estado: IMPLEMENTAÇÃO/VALIDAÇÃO EM ANDAMENTO. Safety CI e Baseline Guard passaram; validação VPS da camada de capacidades/backend passou no commit `684820f49896d9a478644e7418932ed40a3a8870`; build de imagem ARM64/ARMHF em execução. Não representa aprovação HW ou PROD.

## Origem e proteção
Base imutável de referência ARMHF: commit `6e7dc53d94a80d8860ce54f513b738313907e5b8`, branch `pu2pny-os-0.3.31.124-armhf-pizero-regression-fix`. Base imutável ARM64: release `v0.3.31.122`, última linha ARM64 protegida antes da trilha Pi Zero. Branch de integração: `pu2pny-os-4.00.000-ecosystem`; backup prévio: `backup/0.3.31.124-pre-4.00.000-20261014`. Ler START_HERE, MASTER_SPEC, RELEASE_STATUS, TEST_MATRIX, CHANGELOG antes de qualquer alteração. O estado aprovado de DMR simplex TX/RX, D-Star/YSF aprovados, rede, wizard, Ao Vivo e RF é baseline protegido. Não substituir o produto por Pi-Star/WPSD.

## Contrato de entrega
A versão é 4.00.000; não usar rótulo PROD até gates SW/CI, VPS e HW aplicáveis. Suportar imagens ARM64 e ARMHF quando arquitetura/hardware permitirem. Todo componente opcional deve ser instalável/ativável pelo painel, sem terminal, com dependências verificadas, baixo consumo, backup e rollback. A UI distingue Disponível, Requer configuração, Requer hardware, Experimental, Incompatível e Não verificado; não inventar telemetria.

## Inventário funcional integral (implementar por módulos, preservar baseline)
- ARCH-007: catálogo MMDVM de capacidades detectadas e recursos disponíveis; ajuda em cada função.
- PROTO-050: DMR simplex/duplex, TS1/TS2, Color Code, TG, TGRewrite/dynamic TG, private call, Talker Alias, BrandMeister Security, XLX, DMR+, TGIF, HBLink, DMRGateway multi-network, OVCM, recursos Tier III somente em perfil compatível/isolado.
- PROTO-051: D-Star gateway/refletores/módulos, comandos de rádio, ACK/echo, controle de acesso, dados suportados.
- PROTO-052: YSF/C4FM, Wires-X via YSFGateway, DG-ID, FCS, parrot, comandos pelo rádio; GPS/APRS de localização permanece DESATIVADO por requisito anterior de APRS somente mensagens.
- PROTO-053: P25 Phase 1, NAC, P25Gateway, TG, Parrot, Soft ID quando upstream/hardware compatível.
- PROTO-054: NXDN, RAN, NXDNGateway, TG, Parrot e compatibilidade Icom/Kenwood comprovada.
- PROTO-055: POCSAG/DAPNET, RIC, mensagens, filas e paging com autorização.
- PROTO-056: FM analógico, CTCSS/COS, FMGateway, SVXLink/USRP/IAX somente em modem/rádio adequado; NÃO assumir FM em CA6JAU MMDVM_HS ADF7021.
- PROTO-057: M17 fork e AX.25/KISS/IL2P via firmware/hardware próprio; NÃO afirmar suporte M17 ou TNC em CA6JAU sem teste.
- RF-050: MMDVMCal, BER/RSSI reais, RX/TX offset, níveis, desvio, testes não destrutivos, backup/rollback.
- ARCH-008: MMDVMHost MQTT/JSON, MMDVM-Info, comandos remotos locais autenticados, eventos e cache; MQTT não exposto à Internet.
- DISPLAY-031: Nextion Basic/Enhanced, G4KLX, ON7LDS L2/L3/L3 HS, Pi-Star/WPSD HMI compatível, OLED/HD44780/LCDproc; exatamente um writer, sem flash HMI automático; gate HW standby/RX/TX.
- LIVE-024: Ao Vivo não regredir com nenhum módulo novo; sem polling pesado; preservar TX/RX, TG, slot, módulo, duração, estado de conexão e ausência de dados fictícios.
- ARCH-009: MMDVM-IQ/Multi SDR (1–7 portadoras quando comprovado), SDRs compatíveis; perfis separados da imagem hotspot.
- PROTO-058: MMDVM-CrossMode + Helix Voice Engine + backends de codec verificados; Helix usa IPC PCM local, padrão OFF, com shadow/process e fallback. HVC permanece bloqueado para produção e AMBE/AMBE+2 não é declarado nativo do Helix sem backend/licença/evidência próprios. AMBE3000/3003 podem ser usados quando presentes e validados. Sem transcoder real não declarar áudio cross-mode funcional.
- NET-050: Cloudflare Quick Tunnel temporário com URL/QR real e aviso de limitações SSE; túnel fixo com token protegido; Tailscale com URL login, IP/MagicDNS real sem aceitar rotas por padrão; ZeroTier Network ID hexadecimal de 16 caracteres, join/leave e status real.
- SEC-026: acesso remoto desativado na fábrica; senha remota individual obrigatória antes de abrir acesso; nenhum usuário/senha padrão; segredo em arquivo 0600 ou armazenamento seguro; autenticação/sessão, CSRF, rate limit, logs sanitizados; listeners LAN e remoto separados, sem confiar cegamente em RFC1918.
- UI-047: cada função com O que é, Para que serve, Hardware, Como configurar, Como usar pelo rádio, Status real, Teste, Diagnóstico e Restaurar.
- UPDATE-050: pacotes/repositórios assinados, versões pinadas, sem curl|bash, upgrades controlados, backup/rollback de identidade/configuração/rede/RF/display.

## Evidência executada em 2026-10-14
- Safety CI run `38574305041`: PASS — sintaxe, fixtures, cross-build ARM64/ARMv6 e handlers protegidos byte-idênticos.
- Baseline Guard run `38574304897`: PASS.
- VPS SentinelX `WartyWallaby`, commit `684820f49896d9a478644e7418932ed40a3a8870`: PASS para scanner de capacidades, políticas `no_network_probe`/`no_rf_write`, cadeia completa de patch backend e `go test`. Isto é VPS, não HW.
- Build release run `38575811918`: EM EXECUÇÃO para ARM64 e ARMHF/ARMv6.
- RF real, BER/RSSI reais, duplex RF, áudio/transcoding real e displays físicos: PENDENTE HW.

## Gate por módulo
1. Auditar implementação existente e documentação upstream/licenças antes de codar; não duplicar funcionalidades aprovadas.
2. Especificar dependências de hardware e firmware; não instalar serviços desnecessários na imagem mínima.
3. Implementar em commits pequenos na branch 4.00.000, mas com escopo total fechado por este plano; não alterar arquivos protegidos sem justificativa/backup.
4. Executar testes unitários/integração e build ARM64/ARMHF; SentinelX/VPS para software, API, segurança, serviços, falha/reconexão e rollback.
5. Executar regressão DMR simplex TX/RX, duplex TX/RX, D-Star, YSF, gateways, Wi-Fi/AP, mDNS, Ao Vivo e display; teste RF e Nextion requer Raspberry Pi real.
6. Atualizar MASTER_SPEC, CHANGELOG, RELEASE_STATUS e TEST_MATRIX com IDs, evidência, nível e estado; SHA-256 da imagem, commit, CI e validação estrutural antes de qualquer link de release.

## Fontes upstream principais
https://github.com/g4klx/MMDVM
https://github.com/g4klx/MMDVM-Host
https://github.com/g4klx/DMRGateway
https://github.com/g4klx/YSFClients
https://github.com/g4klx/P25Clients
https://github.com/g4klx/NXDNClients
https://github.com/g4klx/DAPNETGateway
https://github.com/g4klx/FMGateway
https://github.com/g4klx/MMDVM-Display
https://github.com/g4klx/MMDVM-Info
https://github.com/g4klx/MMDVMCal
https://github.com/g4klx/MMDVM-IQ
https://github.com/g4klx/MMDVM-Multi
https://github.com/g4klx/MMDVM-CrossMode
https://github.com/g4klx/MMDVM-Transcoder
https://github.com/g4klx/MMDVM-TNC
https://github.com/M17-Project/MMDVMHost
https://github.com/DVMProject/dvmhost
https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/
https://tailscale.com/kb/
https://docs.zerotier.com/
