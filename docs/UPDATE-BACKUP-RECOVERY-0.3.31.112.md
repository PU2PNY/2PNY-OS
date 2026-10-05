# PU2PNY-OS — Update / Backup / Recovery 0.3.31.112

Status: **candidata de software, não ativada no runtime**.

Base: `pu2pny-os-0.3.31.111-governance` → `pu2pny-os-0.3.31.112-recovery`.

## Objetivo

Adotar nativamente no PU2PNY-OS o princípio seguro observado no fluxo DPX — validar antes da escrita destrutiva, criar ponto de retorno antes da mudança e abortar sem tocar no sistema ativo quando uma pré-condição falha — sem copiar firmware, código, licença ou identidade do DPX.

A implementação candidata é `src/2pny-update-manager-0.3.31.112.py`. O updater histórico `src/2pny-update-manager-0.3.20.py` permanece intacto e autoritativo no runtime até validação e autorização de integração.

## UPDATE-003 — preflight fail-before-write

Antes de qualquer mutação da árvore ativa, validar:

1. arquivo de pacote existente;
2. SHA-256 externo esperado;
3. versão solicitada e versão declarada pelo manifesto;
4. `schema=1`;
5. `from_compatible` contendo explicitamente a versão instalada;
6. arquivo por arquivo: caminho permitido, unicidade, SHA-256, tamanho e modo;
7. ausência de traversal, symlink/hardlink/device/FIFO no pacote;
8. ausência de pais de destino via symlink;
9. permissões efetivas de escrita;
10. espaço livre conservador para staging + backup + pacote + margem.

O comando `preflight` não cria diretório de transação, não altera versão, não reinicia serviço e não grava arquivo em `/etc`, `/usr` ou em qualquer destino ativo.

**Aceite mínimo:** pacote inválido, hash inválido, payload inválido, versão incompatível e path traversal precisam falhar antes de qualquer mutação ativa. Validação mínima: SW.

## UPDATE-004 — prepare antes de activate

`prepare` executa novamente o preflight, cria uma transação privada em `/var/lib/2pny/update-transactions/<txid>`, extrai somente payload permitido para staging, valida novamente SHA-256 e só então cria o backup.

Nenhum arquivo ativo é substituído nessa fase.

**Aceite mínimo:** transação chega a `phase=prepared` somente com staging e backup verificáveis; arquivo ativo permanece byte a byte no estado anterior. Validação mínima: SW/VPS.

## BACKUP-002 — ponto de retorno verificável

O backup pré-ativação:

- guarda somente arquivos que a atualização pretende substituir e o arquivo de versão;
- registra separadamente arquivos que não existiam antes, para removê-los no rollback;
- usa diretório de transação `0700` e arquivo de backup `0600`;
- possui `backup.json` com origem, destino, entradas, hashes e `archive_sha256`;
- precisa passar `verify_backup()` imediatamente após a criação e novamente antes de ativar;
- nunca é confundido com relatório sanitizado de suporte;
- não é enviado para rede/nuvem por padrão.

**Aceite mínimo:** adulteração de um byte no backup bloqueia a ativação antes de qualquer mutação ativa. Validação mínima: SW/VPS.

## UPDATE-005 — ativação atômica e health-check

A ativação só aceita transação em `prepared`. Antes da primeira escrita, revalida backup e todos os arquivos staged. Cada arquivo é instalado por temporário no mesmo filesystem, `fsync` e `os.replace()`. Depois atualiza a versão, reinicia somente units explicitamente listadas e verifica saúde das units que estavam saudáveis antes da mudança.

Não há `eval`, shell arbitrário, `curl | bash`, `apt full-upgrade` nem execução de comando recebido do pacote.

**Aceite mínimo:** staging adulterado ou backup adulterado bloqueia antes da mutação; destino recebe somente arquivo verificado por operação atômica. Validação mínima: SW/VPS.

## BACKUP-003 — rollback automático e manual

Se uma exceção ocorrer depois da primeira mutação ativa, o gerenciador:

1. verifica novamente o SHA do backup;
2. restaura arquivos anteriores por escrita atômica;
3. remove arquivos que não existiam antes da atualização;
4. restaura `/etc/2pny/version`;
5. registra `phase=rolled_back` ou `phase=rollback_failed` sem mascarar a falha;
6. permite rollback manual apenas de transação previamente `committed` ou `rollback_failed`.

**Aceite mínimo:** falha de health-check após ativação precisa restaurar conteúdo e versão anteriores. Validação mínima: SW/VPS; integração real exige HW quando afetar serviços de RF/display/rede.

## Segurança e baseline

- Allowlist de destinos permanece restrita a componentes PU2PNY já utilizados pelo updater anterior.
- O pacote não pode escolher comandos para executar.
- O mecanismo não altera, por si só, DMR/D-Star/YSF/RF/rede/display. Ele apenas instala um payload explicitamente autorizado; o Baseline Guard posterior deve impedir payload/commit acidental em áreas protegidas.
- O updater 0.3.20 não é removido nem modificado nesta candidata.
- A candidata 0.3.31.112 não deve ser empacotada como padrão antes de PASS SW e VPS e revisão do rollback.

## Testes candidatos

`ci/test-0.3.31.112-update-recovery.py` cobre:

- preflight sem escrita;
- SHA externo inválido;
- SHA de payload inválido;
- traversal;
- prepare sem mutação ativa;
- activate + rollback manual;
- falha de health-check + rollback automático;
- backup adulterado bloqueando ativação.

Até execução real do teste, o estado desses casos é **PENDENTE SW**. GitHub Actions enfileirado ou compilação não executada não conta como PASS.
