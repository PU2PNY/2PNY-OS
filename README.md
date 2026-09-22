# PU2PNY-OS

**PU2PNY-OS — Digital Radio Operating System**

Sistema operacional/appliance próprio para Raspberry Pi e hotspots MMDVM, com foco em baixo consumo, configuração sem terminal, operação multiprotocolo, diagnóstico, rollback e preservação rigorosa de baselines aprovados.

## Estado atual

- **Ciclo ativo:** `0.3.20-alpha`
- **Branch:** `pu2pny-os-0.3.20-alpha`
- **Base preservada:** `0.3.19-alpha`
- **Classificação:** **ALPHA / para teste físico**
- **Produção:** não
- **Repositório observado:** `PU2PNY/2PNY-OS`
- **Nome canônico aprovado:** `PU2PNY/PU2PNY-OS` — só considerar a renomeação concluída quando a metadata do GitHub confirmar.

A 0.3.20 ainda exige validação HW para funções dependentes de Raspberry Pi/MMDVM/Nextion/RF real. CI, software ou VPS não substituem teste físico.

## Primeiro acesso

Conforme o requisito atual NET-001:

- SSID de setup: `pu2pny`
- endereço local de setup: `10.43.0.1`
- acesso normal: `http://pu2pny.local/`
- o AP deve permanecer recuperável se o provisionamento falhar.

## Baselines protegidos

Tudo comprovadamente aprovado deve ser preservado. Em especial, DMR simplex TX/RX funcional é baseline obrigatório: defeitos de duplex devem ser corrigidos sem reescrever ou regredir simplex.

## Protocolos e áreas

O projeto cobre DMR, D-Star, YSF/C4FM e evolução controlada para outros modos suportados, além de rede/wizard, MMDVM, Ao Vivo, painel/API, displays, APRS/DPRS, Direct/P2P, update, backup, rollback e hardening.

## Documentação canônica

Leia nesta ordem antes de alterar o projeto:

1. [PU2PNY-OS_START_HERE.md](PU2PNY-OS_START_HERE.md)
2. [PU2PNY-OS_MASTER_SPEC.md](PU2PNY-OS_MASTER_SPEC.md)
3. [PU2PNY-OS_RELEASE_STATUS.md](PU2PNY-OS_RELEASE_STATUS.md)
4. [PU2PNY-OS_TEST_MATRIX.md](PU2PNY-OS_TEST_MATRIX.md)
5. [PU2PNY-OS_CHANGELOG.md](PU2PNY-OS_CHANGELOG.md)
6. [PU2PNY-OS_PROJECT_INSTRUCTIONS.md](PU2PNY-OS_PROJECT_INSTRUCTIONS.md)
7. [docs/README.md](docs/README.md) para índice da documentação histórica/técnica.

## Regra de release

Uma imagem só pode ser divulgada conforme o estado real dos gates: fonte → staging → ARM64 → XZ/SHA-256 → preflight REL-015 → validador final → artefato/publicação. HW só recebe PASS com hardware real.

> O projeto está em desenvolvimento. Não interpretar estado SW/VPS como aprovação física ou PROD.
