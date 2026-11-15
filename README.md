# PU2PNY-OS

Sistema próprio para hotspots digitais MMDVM, com painel web, operação sem terminal e foco em baixo consumo, estabilidade e recuperação. A evolução da geração 5.x preserva as configurações e funções já aprovadas em hardware.

## Versão publicada: 5.12.001 P1 ALPHA

**Informações conferidas em 15/11/2026.** A [5.12.001 P1](https://github.com/PU2PNY/2PNY-OS/releases/tag/pu2pny-v5.12.001-p1) foi publicada em **14/11/2026**, com quatro imagens. **Candidata para teste físico; hardware ainda não homologado nesta versão; produção não aprovada.**

[Release e notas completas](https://github.com/PU2PNY/2PNY-OS/releases/tag/pu2pny-v5.12.001-p1) · [CI: 6/6 jobs em sucesso](https://github.com/PU2PNY/2PNY-OS/actions/runs/43597269377) · [Checklist de teste físico](https://github.com/PU2PNY/2PNY-OS/blob/1e375c761f8b2ce9fa009065e831081be2ab9a82/docs/PU2PNY-OS_5.12.001_HW_CHECKLIST.md).

| Destino | Download 5.12.001 P1 | Integridade |
|---|---|---|
| Raspberry Pi — ARM32 | [Imagem .img.xz](https://github.com/PU2PNY/2PNY-OS/releases/download/pu2pny-v5.12.001-p1/pu2pny-32-5.12.001.img.xz) | [SHA-256](https://github.com/PU2PNY/2PNY-OS/releases/download/pu2pny-v5.12.001-p1/pu2pny-32-5.12.001.img.xz.sha256) |
| Raspberry Pi — ARM64 | [Imagem .img.xz](https://github.com/PU2PNY/2PNY-OS/releases/download/pu2pny-v5.12.001-p1/pu2pny-64-5.12.001.img.xz) | [SHA-256](https://github.com/PU2PNY/2PNY-OS/releases/download/pu2pny-v5.12.001-p1/pu2pny-64-5.12.001.img.xz.sha256) |
| Orange Pi Zero — H2+ | [Imagem .img.xz](https://github.com/PU2PNY/2PNY-OS/releases/download/pu2pny-v5.12.001-p1/pu2pny-opizero-5.12.001.img.xz) | [SHA-256](https://github.com/PU2PNY/2PNY-OS/releases/download/pu2pny-v5.12.001-p1/pu2pny-opizero-5.12.001.img.xz.sha256) |
| NanoPi NEO — H3 | [Imagem .img.xz](https://github.com/PU2PNY/2PNY-OS/releases/download/pu2pny-v5.12.001-p1/pu2pny-nanopineo-5.12.001.img.xz) | [SHA-256](https://github.com/PU2PNY/2PNY-OS/releases/download/pu2pny-v5.12.001-p1/pu2pny-nanopineo-5.12.001.img.xz.sha256) |

Os arquivos `.sha256` e os quatro manifestos `BUILD-INFO` estão na mesma release. O CI verificou integridade XZ, checksums, arquitetura, commit e preservação dos componentes protegidos. **Build e CI não comprovam TX/RX, conexão remota nem funcionamento físico de displays.**

- **Código das imagens/tag:** [`38f3ac23582e4c5a424b09a5901b03f828aa617a`](https://github.com/PU2PNY/2PNY-OS/commit/38f3ac23582e4c5a424b09a5901b03f828aa617a).
- **Tag:** `pu2pny-v5.12.001-p1`.
- **Branch da versão:** [`release/pu2pny-5.12.001`](https://github.com/PU2PNY/2PNY-OS/tree/release/pu2pny-5.12.001).
- **Base das imagens:** 5.12.000 P0 específica de cada placa.

### O que mudou na P1

- Menu de navegação com alternativa estática quando o JavaScript principal falha.
- Bloco do relógio novamente visível na página Sistema; o fuso efetivo ainda precisa de confirmação no equipamento.
- Páginas OLED e LCD com identidade PU2PNY-OS, indicativo, protocolo, modo, duração, IP e métricas reais quando disponíveis.
- Expert com diagnóstico de leitura HTTP/AP/gateways e exportação TXT ampliada.

MMDVMHost, aplicador RF, NextionDriver ON7LDS, bootloader, drivers, rede e presets foram preservados nos gates de manifesto desta P1. Os detalhes e limites estão no [estado da versão](https://github.com/PU2PNY/2PNY-OS/blob/1e375c761f8b2ce9fa009065e831081be2ab9a82/PU2PNY-OS_RELEASE_STATUS.md).

## Validação e pendências

| Área | Estado atual |
|---|---|
| Quatro imagens, XZ, SHA-256 e publicação | **PASS em SW/CI** |
| Boot, painel, RF e displays na P1 em equipamento real | **PENDENTE / NÃO VERIFICADO** |
| Ativação DMR/YSF/D-Star e confirmação de conexão remota | Regressões/pendências registradas; **sem correção física comprovada** |
| HTTP/AP Orange Pi e funcionamento NanoPi | **PENDENTE em hardware** |
| Nextion: campos extras CPU/disco/IP | **PENDENTE**; preservar baseline ON7LDS |
| Direct privado/grupo por CGNAT e relay | **Sem relay operacional comprovado** |
| Transcoding AMBE/cross-mode | **Sem backend/vocoder real comprovado para declarar funcionamento** |
| Produção | **NÃO APROVADA** |

O painel ainda pode exibir `5.11.000` mesmo com `/etc/2pny/version` em `5.12.001` ([#30](https://github.com/PU2PNY/2PNY-OS/issues/30)). Há relatos anteriores de falha ao ativar protocolos, falha de navegação, fuso Europe/London e subtensão em Pi 4; a P1 não comprova a resolução desses problemas. Consulte as [issues abertas](https://github.com/PU2PNY/2PNY-OS/issues) e a [matriz de testes](https://github.com/PU2PNY/2PNY-OS/blob/1e375c761f8b2ce9fa009065e831081be2ab9a82/PU2PNY-OS_TEST_MATRIX.md).

## Teste e primeiro acesso

1. Escolha a imagem correspondente à placa e à arquitetura.
2. Confira o SHA-256 e grave em um cartão separado, preservando o cartão e a configuração aprovados para rollback.
3. Acesse o painel pelo endereço anunciado pelo equipamento. `http://pu2pny.local/` é o nome previsto no projeto; mDNS/nomes por placa continuam sujeitos aos testes registrados. Se necessário, use o IP real atribuído pelo roteador.
4. Siga o [checklist da P1](https://github.com/PU2PNY/2PNY-OS/blob/1e375c761f8b2ce9fa009065e831081be2ab9a82/docs/PU2PNY-OS_5.12.001_HW_CHECKLIST.md) e registre o resultado de cada placa, protocolo e display.

NanoPi NEO requer Ethernet ou Wi-Fi USB conforme a configuração. Não grave firmware HMI/TFT automaticamente.

## Projeto e baselines protegidos

O PU2PNY-OS mantém arquitetura, painel e integração próprios, usando componentes upstream quando apropriado.

O escopo da geração 5.x inclui DMR, D-Star, YSF/C4FM e expansão modular para P25, NXDN, POCSAG/DAPNET, APRS/DPRS por mensagens, displays, Direct/P2P, Helix, backup e recovery. **Requisito planejado não significa recurso homologado:** disponibilidade depende do hardware, firmware, gateway e resultado dos testes.

DMR simplex, D-Star/YSF simplex e demais baselines históricos aprovados devem ser preservados conforme suas evidências. A aprovação do **NextionDriver ON7LDS na 5.00.002** permanece protegida; ela não homologa automaticamente a P1, outras telas ou novos campos. Consulte a [regra de display](https://github.com/PU2PNY/2PNY-OS/blob/1e375c761f8b2ce9fa009065e831081be2ab9a82/docs/PU2PNY-OS_DISPLAY_BASELINE.md).

## Documentação atual

Os links abaixo apontam para o snapshot documental posterior à publicação da P1, commit `1e375c761f8b2ce9fa009065e831081be2ab9a82`.

- [START HERE — entrada do projeto](https://github.com/PU2PNY/2PNY-OS/blob/1e375c761f8b2ce9fa009065e831081be2ab9a82/PU2PNY-OS_START_HERE.md)
- [MASTER SPEC — requisitos](https://github.com/PU2PNY/2PNY-OS/blob/1e375c761f8b2ce9fa009065e831081be2ab9a82/PU2PNY-OS_MASTER_SPEC.md)
- [RELEASE STATUS — entrega e bloqueadores](https://github.com/PU2PNY/2PNY-OS/blob/1e375c761f8b2ce9fa009065e831081be2ab9a82/PU2PNY-OS_RELEASE_STATUS.md)
- [TEST MATRIX — evidências e testes](https://github.com/PU2PNY/2PNY-OS/blob/1e375c761f8b2ce9fa009065e831081be2ab9a82/PU2PNY-OS_TEST_MATRIX.md)
- [CHANGELOG — histórico de alterações](https://github.com/PU2PNY/2PNY-OS/blob/1e375c761f8b2ce9fa009065e831081be2ab9a82/PU2PNY-OS_CHANGELOG.md)
- [PROJECT INSTRUCTIONS — regras de execução](https://github.com/PU2PNY/2PNY-OS/blob/1e375c761f8b2ce9fa009065e831081be2ab9a82/PU2PNY-OS_PROJECT_INSTRUCTIONS.md)
- [UI CONTRACT — contrato do painel](https://github.com/PU2PNY/2PNY-OS/blob/1e375c761f8b2ce9fa009065e831081be2ab9a82/docs/PU2PNY-OS_UI_CONTRACT.md)

## Histórico e organização do repositório

A branch padrão `main` ainda contém o código histórico da fundação; **o código da versão 5.12.001 está na branch e no commit indicados acima**. Esta atualização altera apenas a apresentação documental da página principal.

As versões 0.1.1 e 0.3.23 deixaram de representar a versão publicada atual. O [README anterior](https://github.com/PU2PNY/2PNY-OS/blob/4c004348d937462dd32510c989f32d4d24b0d052/README.md) permanece no histórico. Releases e baselines anteriores continuam disponíveis para consulta e rollback.

**Registro de 15/11/2026:** README da `main` atualizado com a release P1, quatro destinos, links conferidos, documentação canônica e estados de validação. Nenhuma imagem, configuração RF, serviço ou baseline foi alterado.
