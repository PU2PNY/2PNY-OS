# PU2PNY-OS — PROJECT INSTRUCTIONS

Este arquivo materializa no repositório as regras de execução do projeto.

- Leia START_HERE, MASTER_SPEC, RELEASE_STATUS, TEST_MATRIX e CHANGELOG antes de modificar qualquer componente.
- Consulte a branch realmente em trabalho e compare com o último baseline validado.
- Não iniciar do zero e não transformar em fork de Pi-Star/WPSD.
- Preserve DMR TX/RX já validado.
- Rede, RF, modem, gateways, displays e boot exigem backup/rollback antes da mudança.
- Falha deve voltar ao último estado comprovadamente funcional quando possível.
- Use DOC/SW/VPS/HW/PROD; não chamar build/CI de teste físico.
- Não inventar dados.
- Baixo uso de CPU/RAM/SD é requisito.
- Operação normal não depende de terminal.
- Toda decisão nova recebe ID de requisito e atualiza documentação/matriz antes de ser considerada permanente.
- Ordem: Base/Boot → Rede/Wizard → Hardware → RF/MMDVM → DMR → D-Star → YSF → demais protocolos → Runtime/Live → UI → Display → APRS → P2P → Update/Backup → Security → HW completo → RC → PROD.
