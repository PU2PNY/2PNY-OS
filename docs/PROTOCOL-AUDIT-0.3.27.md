# PU2PNY-OS — Auditoria de protocolos 0.3.27-alpha

Data: 2026-09-26  
Base: v0.3.26-alpha / commit de imagem fad9d4c7ca147e04520a9a09b64d2aa797d4e766  
Rollback: backup/0.3.26-pre-0.3.27-20260926

## Princípio
Esta auditoria não autoriza substituição de um caminho fisicamente aprovado. YSF/C4FM simplex, D-Star simplex e DMR simplex permanecem baseline protegida. DMR duplex continua isolado.

## YSF / C4FM
Estado SW auditado:
- MMDVMHost ativa [System Fusion] apenas no perfil YSF.
- Loopback MMDVMHost ↔ YSFGateway preservado: LocalPort 3200 / GatewayPort 4200.
- YSFGateway preservado: RptPort 3200 / LocalPort 4200.
- WiresXCommandPassthrough=0: comandos Wires-X do rádio são processados pelo YSFGateway local.
- Startup é resolvido para um refletor real do catálogo; configuração inválida é bloqueada.
- Reconnect=0 e Revert=0 permanecem no baseline.
- YSF e FCS permanecem suportados pelo gateway atual.

Comparação histórica:
- 0.3.8/0.3.9/0.3.16 já continham o mesmo contrato de portas e Wires-X.
- 0.3.20 reforçou a resolução exata de Startup pelo catálogo de hosts, evitando configuração de gateway sem destino resolvível.
- Nenhuma regressão de fonte que justifique reescrever o runtime YSF foi encontrada entre a base funcional e v0.3.26.

Resultado:
- runtime YSF/C4FM NÃO ALTERADO na 0.3.27.
- simplex permanece baseline física aprovada anteriormente.
- Wires-X por rádio, troca real de sala e TX/RX da nova imagem: PENDENTE DE TESTE FÍSICO.

Fonte upstream consultada: g4klx/YSFClients e g4klx/MMDVMHost.

## D-Star
Estado SW auditado:
- MMDVMHost ↔ DStarGateway preservado em loopback 20011/20010.
- módulo RF local é independente do módulo remoto.
- DPlus, DExtra, DCS e XLX permanecem habilitados no DStarGateway.
- ReflectorAtStartup=1 e ReflectorReconnect=Never permanecem compatíveis com comandos manuais do gateway/radio implementados no projeto.
- catálogo/hostfiles e rollback transacional permanecem no caminho atual.

Resultado:
- runtime D-Star NÃO ALTERADO na 0.3.27.
- D-Star simplex permanece baseline física protegida.
- regressão física na nova imagem e comandos reais pelo rádio: PENDENTE DE TESTE FÍSICO.

## DMR
Estado SW auditado:
- simplex e duplex continuam separados por use_mode.
- simplex mantém o caminho marcado simplex-protected.
- duplex/repetidora habilita TS1+TS2 somente no ramo duplex.
- MMDVMHost ↔ DMRGateway preservado em 62032/62031.
- TG/Private Call, comandos XLX TG4000/TG4001–4026/TG4099 e arbitragem de voz permanecem nos patches pinados.
- BrandMeister continua autenticando no DMRGateway; a senha não pertence ao MMDVMHost.
- BrandMeister Hotspot Security já era exigida pelo helper DMR; a falha encontrada era persistência/UX no primeiro provisionamento e reutilização segura da senha salva.

Correção 0.3.27:
- campo visível BrandMeister Hotspot Security Password na área DMR.
- campo HTML type=password; valor salvo não volta ao navegador.
- estado público expõe apenas booleano configured.
- segredo fica em /var/lib/2pny/protocol-secrets/dmr.secret, diretório 0700/arquivo 0600.
- primeiro provisionamento também passa a persistir o segredo depois de aplicação DMR bem-sucedida.
- alteração de master pode reutilizar o segredo já salvo quando o campo é deixado vazio.
- dmr.secret foi incluído no backup transacional.
- DMRGateway/MMDVMHost/patches DMR NÃO foram alterados.

Resultado:
- DMR simplex permanece baseline protegida.
- DMR duplex estruturalmente auditado, mas TX/RX/áudio/timeout reais continuam PENDENTE DE TESTE FÍSICO.
- autenticação real BrandMeister com a senha do usuário continua PENDENTE DE TESTE FÍSICO/REDE REAL.

Fontes upstream/oficiais consultadas: BrandMeister Docs (HotSpot Security / Connecting Hotspots), g4klx/MMDVMHost.

## APRS
Achado:
- o cliente 0.3.21 já possuía mensagens bidirecionais, fila persistente, ACK/REJ, retry limitado e deduplicação.
- porém ainda emitia beacon de posição se um arquivo legado contivesse latitude/longitude e a UI ainda oferecia geolocalização/mapa.

Correção 0.3.27:
- daemon message-only: nenhum gerador/envio de pacote de posição.
- API sanitiza configuração legada e preserva apenas enabled/callsign/server/port/ssid.
- removidos da UI latitude, longitude, geolocalização, mapa/radar, APRS.fi, intervalo/comentário/beacon e último/próximo beacon.
- preservados envio, recebimento, fila, ACK, REJ, retries, notificações e identificação APRS-IS.

APRS-IS real e ACK de destinatário externo: PENDENTE DE TESTE FÍSICO/REDE REAL.

## Arquivos de protocolo congelados
A release 0.3.27 exige comparação byte a byte com v0.3.26 para:
- src/2pny-protocol-network-apply-0.3.21.py
- src/2pny-protocol-network-apply-all-0.3.20.py
- src/2pny-dstargateway-0.2.9.service
- src/2pny-ysfgateway-0.2.9.service
- src/2pny-mmdvmhost-0.3.13.service
- ci/patch-dmrgateway-pu2pny-0.3.20.py
- ci/patch-dmrgateway-voice-arbiter-0.3.21.py

## Validação
- DOC: auditoria histórica/código concluída.
- SW/VPS: testes focais e gates da release.
- HW: somente após Raspberry Pi + MMDVM/radios reais.
