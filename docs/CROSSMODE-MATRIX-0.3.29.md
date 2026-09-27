# PU2PNY-OS 0.3.29 — matriz de cross-mode

Estado: **análise técnica / não habilitado automaticamente na 0.3.29-alpha**.

Referência primária: upstream G4KLX `MMDVM-CrossMode` e `MMDVM-Transcoder`. O programa novo de cross-mode foi projetado para usar o MMDVM-Transcoder. A versão inicial declara D-Star, DMR, YSF DN e FM; P25/NXDN fazem parte do objetivo final, não da versão inicial. O hardware do transcoder usa STM32H723 com AMBE3003/AMBE3000.

| Origem RF | Destino/rede | Possível no upstream atual? | Método seguro no PU2PNY-OS | Transcoder | Estado 0.3.29 |
|---|---|---|---|---|---|
| DMR | YSF DN | Sim, dentro dos modos iniciais | MMDVM-CrossMode isolado | Obrigatório | NÃO HABILITADO / HW PENDENTE |
| YSF DN | DMR | Sim, dentro dos modos iniciais | MMDVM-CrossMode isolado | Obrigatório | NÃO HABILITADO / HW PENDENTE |
| DMR | D-Star | Sim, dentro dos modos iniciais | MMDVM-CrossMode isolado | Obrigatório | NÃO HABILITADO / HW PENDENTE |
| D-Star | DMR | Sim, dentro dos modos iniciais | MMDVM-CrossMode isolado | Obrigatório | NÃO HABILITADO / HW PENDENTE |
| YSF DN | D-Star | Sim, dentro dos modos iniciais | MMDVM-CrossMode isolado | Obrigatório | NÃO HABILITADO / HW PENDENTE |
| D-Star | YSF DN | Sim, dentro dos modos iniciais | MMDVM-CrossMode isolado | Obrigatório | NÃO HABILITADO / HW PENDENTE |
| DMR | NXDN | Não habilitado pelo programa inicial novo | Não ativar | — | NÃO SUPORTADO NESTA ALPHA |
| NXDN | DMR | Não habilitado pelo programa inicial novo | Não ativar | — | NÃO SUPORTADO NESTA ALPHA |
| YSF | NXDN | Não habilitado pelo programa inicial novo | Não ativar | — | NÃO SUPORTADO NESTA ALPHA |
| NXDN | YSF | Não habilitado pelo programa inicial novo | Não ativar | — | NÃO SUPORTADO NESTA ALPHA |
| YSF | P25 | Não habilitado pelo programa inicial novo | Não ativar | — | NÃO SUPORTADO NESTA ALPHA |
| P25 | YSF | Não habilitado pelo programa inicial novo | Não ativar | — | NÃO SUPORTADO NESTA ALPHA |

## Regras de integração

1. Cross-mode não intercepta DMR, D-Star ou YSF nativos quando não selecionado.
2. Sem transcoder detectado e validado, a UI deve informar **Transcoder necessário**.
3. YSF VW não é anunciado como disponível na fase inicial; a documentação upstream da versão inicial limita System Fusion a YSF DN.
4. P25/NXDN permanecem desligados até o upstream usado e a cadeia completa de áudio/metadados serem validados.
5. Só marcar uma direção como APROVADA depois de RX origem → transcode → TX destino → áudio → metadados → retorno em hardware real.
6. Nenhuma mudança de ganho do modo nativo pode ser usada para mascarar defeito exclusivo do cross-mode.

Fontes:
- https://github.com/g4klx/MMDVM-CrossMode
- https://github.com/g4klx/MMDVM-Transcoder
- https://github.com/g4klx/YSFClients
