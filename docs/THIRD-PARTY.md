# 2PNY — política de componentes de terceiros

O 2PNY-OS é um projeto próprio (`PU2PNY/2PNY-OS`) e não é fork. Componentes externos devem ser integrados de forma explícita, rastreável e reversível.

## Regra principal

O 2PNY Core, a UI, o provisionamento, o diagnóstico e a integração com displays permanecem código do 2PNY. Projetos externos entram preferencialmente como **processos/serviços separados**, com configuração própria, versão fixada, licença preservada e possibilidade de atualização/remoção sem substituir o Core.

## Classificação inicial

| Componente | Uso no 2PNY | Licença identificada no GitHub | Política |
|---|---|---:|---|
| MMDVMHost (`g4klx/MMDVM-Host`) | motor RF | GPL-2.0 | permitido como serviço externo; versão/commit deve ser fixado e registrado |
| Dire Wolf (`wb2osz/direwolf`) | APRS/AX.25/TNC/IGate | GPL-2.0 | permitido como módulo externo opcional; preservar licença e disponibilizar o código-fonte correspondente à versão distribuída |
| DMRGateway (`g4klx/DMRGateway`) | DMR multi-rede | GPL-2.0 | permitido como módulo externo opcional; preservar licença e código-fonte correspondente |
| M17Gateway (`M17-Project/M17Gateway`) | M17 | GPL-2.0 | permitido como módulo externo opcional; preservar licença e código-fonte correspondente |
| OpenWebRX/OpenWebRX+ | WebSDR | AGPL-3.0 | manter como aplicação separada; cumprir obrigações de fonte/licença antes de distribuição |
| AIOC (`skuep/AIOC`) | referência para futura interface USB de áudio/PTT/COS | MIT | conceitos e código podem ser usados conforme os termos MIT, mantendo copyright/licença quando houver reutilização de código |
| Ham Dashboard (`VA3HDL/hamdashboard`) | referência de UX/dashboard | MIT | usar como referência ou reutilizar apenas com aviso/licença MIT preservados |
| DroidStar (`nostar/DroidStar`) | laboratório/referência de protocolos | licença não identificada pelo GitHub na auditoria de 17/09/2026 | **não copiar código**; usar apenas comportamento/documentação pública como referência até existir licença inequívoca |
| HBlink4 (`n0mjs710/HBlink4`) | referência para DMR | licença não identificada pelo GitHub na auditoria de 17/09/2026 | **não incorporar código** sem licença explícita |
| NextionDriver (`on7lds/NextionDriver`) | referência funcional para display | licença não identificada pelo GitHub na auditoria de 17/09/2026 | reimplementar as ideias no 2PNY; não copiar código sem licença explícita |

## Regras de distribuição

1. Registrar repositório upstream, versão/tag/commit e SHA quando aplicável.
2. Nunca baixar `latest` silenciosamente em uma imagem de produção.
3. Manter os avisos de copyright e licença exigidos pelo projeto upstream.
4. Para componentes GPL/AGPL distribuídos em binário, manter uma forma clara de obter o **código-fonte correspondente à versão exata** distribuída.
5. Não misturar código sem licença explícita ao Core.
6. Serviços externos não recebem acesso root por padrão; usar usuário dedicado, limites de memória/processos e `systemd` hardening.
7. Um módulo externo com falha não pode impedir boot, provisionamento, painel ou diagnóstico básico.
8. Nenhum módulo é habilitado automaticamente para transmissão RF sem configuração e validação explícitas.

## Ordem de integração segura

1. inventário/status de módulos;
2. Nextion com implementação própria do 2PNY;
3. Dire Wolf/APRS como serviço opcional;
4. DMRGateway como serviço opcional;
5. M17Gateway;
6. OpenWebRX em perfil de hardware que comporte o consumo adicional;
7. AIOC/RadioLink como projeto de hardware separado.

> Este documento é uma política técnica de engenharia e conformidade do projeto, não aconselhamento jurídico.
