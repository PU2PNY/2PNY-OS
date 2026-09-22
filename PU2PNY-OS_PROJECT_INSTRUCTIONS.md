# PU2PNY-OS — INSTRUÇÕES PERMANENTES DO PROJETO

## 1. Precedência
Antes de analisar, corrigir, programar, publicar, gerar imagem ou modificar GitHub, servidor, CI/CD ou documentação:
1. Ler `PU2PNY-OS_START_HERE.md`.
2. Ler `PU2PNY-OS_MASTER_SPEC.md`.
3. Ler `PU2PNY-OS_RELEASE_STATUS.md`.
4. Ler `PU2PNY-OS_TEST_MATRIX.md`.
5. Ler `PU2PNY-OS_CHANGELOG.md`.
6. Consultar o repositório e a branch realmente em uso.
7. Comparar a mudança com os requisitos existentes e preservar tudo que já foi aprovado e funciona.

Fontes oficiais: MASTER_SPEC=requisitos; RELEASE_STATUS=estado; TEST_MATRIX=testes; CHANGELOG=decisões; código/repositório=implementação.

## 2. Baseline protegido
Tudo explicitamente aprovado, testado ou comprovado funcionando é BASELINE PROTEGIDO. Não pode ser removido, substituído, refatorado, redesenhado, renomeado ou alterado sem necessidade direta ou ordem explícita.

Regra: `funcionando + aprovado = preservar`.

Não alterar componentes fora do problema atual.

## 3. Escopo mínimo
Antes de alterar: identificar defeito e causa; localizar arquivos necessários; avaliar impacto no baseline; criar backup/ponto de retorno; definir testes de regressão. Não refatorar código funcional por conveniência nem mudar arquitetura/UI/comportamento fora do pedido.

## 4. DMR baseline crítico
DMR TX/RX funcional das versões anteriores é baseline obrigatório. DMR simplex comprovadamente funcional deve ser preservado. Se simplex funciona e duplex falha:

`preservar simplex + corrigir duplex`

Nunca reescrever todo o DMR para defeito exclusivo do duplex. Após mudança DMR retestar simplex TX/RX, duplex TX/RX, rádio→rede, rede→rádio, MMDVMHost, DMRGateway, TG, slot, Color Code, frequências RX/TX e Ao Vivo. Se duplex quebrar simplex, é regressão e deve haver rollback quando possível.

## 5. Preservação geral
A mesma regra vale para todo o sistema. Wi-Fi funcional não muda para corrigir D-Star; wizard aprovado não é refeito por problema RF; UI aprovada não é redesenhada durante correção de backend; baud, porta, offsets ou configuração funcional não mudam sem necessidade comprovada. Se uma versão anterior funcionava, investigar essa implementação antes de criar outra. Ausência de reclamação não equivale a teste comprovado.

## 6. Execução
- Não reiniciar o projeto do zero.
- PU2PNY-OS é sistema próprio; não virar fork de Pi-Star/WPSD.
- Não remover requisito aprovado.
- Não substituir componente funcional sem backup, teste e rollback.
- Antes de alterar RF, modem, baud, offsets, MMDVMHost, gateways, displays, rede ou boot, registrar estado atual.
- Falha deve voltar ao último estado funcional quando possível.
- Compilar, instalar ou ler documentação não equivale a teste físico.
- Não inventar BER, RSSI, chamadas, gateways, IDs, localização, progresso, conexão ou resultados.
- Valor sem fonte: `—`, `indisponível` ou `não verificado`.
- Evitar polling pesado, logs repetitivos e gravações excessivas no SD.
- Preservar baixo uso de CPU/RAM.
- Operação normal não deve exigir terminal.

## 7. Investigação e fontes
Antes de criar solução nova: analisar código atual; consultar versões/commits anteriores; comparar regressões; consultar documentação oficial; pesquisar dados atuais quando necessário; consultar issues/repositórios upstream; testar a hipótese; só então alterar.

Prioridade: documentação oficial → repositório/código oficial → especificação → fabricante → release notes/issues oficiais → fontes técnicas reconhecidas → fóruns apenas como apoio. Hipótese não é fato.

## 8. Plugins, web e SentinelX
Usar plugins/conectores disponíveis para validação independente quando aplicável. GitHub para código/branch/Actions/releases; SentinelX para VPS/Linux; web para documentação atual; CI para build/testes; hardware real quando necessário.

Quando a mudança puder ser reproduzida sem RF físico, testar na VPS via SentinelX quando disponível: instalação, dependências, scripts/systemd, permissões, APIs, frontend/backend, rede compatível, backup/restore, rollback, segurança, performance e logs. Registrar antes/depois.

## 9. Limites da VPS
VPS não comprova RF real, MMDVM físico, UART/GPIO física, BER/RSSI real, TX/RX RF, duplex RF real, Raspberry Pi real ou Nextion físico.

`VPS aprovado ≠ HW aprovado`.

## 10. Validação
- DOC: documentação/código.
- SW: software/CI.
- VPS: VPS/Linux.
- HW: Raspberry Pi + hardware real.
- PROD: produção.

Estados: PENDENTE, EM TESTE, APROVADO, FALHOU, REGRESSÃO, BLOQUEADO, NÃO VERIFICADO. Só afirmar hardware com HW; só chamar produção quando requisitos críticos estiverem PROD.

## 11. Requisitos permanentes
Usar IDs: ARCH-, BOOT-, NET-, WIZ-, HW-, RF-, PROTO-, LIVE-, UI-, DISPLAY-, APRS-, QRZ-, P2P-, DATA-, UPDATE-, BACKUP-, SEC-, PERF-, TEST-, REL-.

Toda decisão permanente deve receber ID, entrar no MASTER_SPEC e CHANGELOG, atualizar RELEASE_STATUS quando aplicável, criar/alterar caso no TEST_MATRIX e definir critério de aceite/nível mínimo.

## 12. Regressão e rollback
Fluxo: `baseline → alteração → teste específico → regressão → comparação`. Nova funcionalidade não compensa regressão. Mudança de risco deve ter rollback. Se algo funcional parar, localizar a última versão funcional e restaurar só o necessário.

## 13. Dependências, Shell e segurança
Não atualizar dependência sem necessidade. Verificar compatibilidade, changelog, licença, ARM64 e rollback. Shell deve preferir `set -euo pipefail`, aspas, validação de argumentos/caminhos, evitar `eval`, usar permissões mínimas e evitar root desnecessário. Não usar `curl ... | bash` sem validar origem/integridade. Nunca expor senhas, tokens, API keys, chaves privadas ou cookies em GitHub, frontend, logs ou diagnóstico.

## 14. Performance
Priorizar event-driven, cache, workers compartilhados, leitura incremental, SSE quando adequado, logs rotacionados e poucas gravações no SD. Evitar polling agressivo, processos pesados por navegador, leitura integral repetitiva de logs, chamadas externas por evento e processos duplicados.

## 15. Ordem padrão
Base/Boot → Rede/Wizard → Hardware → RF/MMDVM → DMR → D-Star → YSF/C4FM → demais protocolos → Runtime/Event Bus → Ao Vivo → Painel/API → Displays → APRS/DPRS → QRZ → P2P → Update/Backup/Rollback → Segurança → testes físicos → RC → Produção. Regressão crítica pode ter prioridade.

## 16. Gate de release
Antes de gerar/divulgar imagem: `requisito → implementação → teste → resultado → regressão → pendências`.

Não liberar como completa com requisito crítico ausente, regressão DMR/RF/rede/wizard/boot, build ARM64 incompleto, imagem sem validação estrutural, SHA-256 ausente, artefato divergente do commit, teste obrigatório pendente ou falta de HW quando a afirmação exigir hardware.

Antes do link verificar commit, branch, CI/build ARM64, artefato, estrutura, SHA-256, versão, serviços essenciais, TEST_MATRIX, regressões, pendências e nível real de validação.

## 17. Regra central
**Preservar tudo que já funciona e foi aprovado. Corrigir somente o errado. Adicionar somente o solicitado/aprovado. Testar antes de afirmar. Nunca transformar suposição em fato.**

Toda versão nova deve ser um superset seguro da última versão aprovada. Exemplo: `DMR simplex perfeito + duplex com defeito = simplex intocado + correção exclusiva do duplex + regressão completa depois.`
