# PU2PNY-OS — RELEASE STATUS

**Branch de trabalho:** `pu2pny-os-0.3.4-alpha`  
**Base preservada:** `pu2pny-os-0.3.3-alpha`  
**Backup criado antes das mudanças:** `backup/0.3.3-hw-feedback-20260919`  
**Data do último feedback físico incorporado:** 2026-09-19  
**Estado global:** ALPHA / correção. **Não PROD.**

## Baseline que não pode regredir

| Área | Estado | Evidência | Observação |
|---|---|---|---|
| AP `pu2pny` no primeiro acesso | HW PASS | usuário | conexão ao AP funcionou corretamente |
| `http://pu2pny.local/` no AP | HW PASS | usuário | acesso considerado excelente |
| Hardware Pi/MMDVM detectado | HW PASS | usuário + UI | preparação chegou a 100% |
| RF básica validada | HW PASS | usuário | não ampliar escopo antes de preservar |
| DMR funcional anterior | HW baseline | histórico físico do projeto | regressão obrigatória em toda nova imagem |
| Rollback ao falhar troca de protocolo | HW PASS | usuário | DMR/estado anterior voltou após erro |

## Bloqueadores atuais

| Requisito | Estado | Nível | Resultado |
|---|---|---:|---|
| NET-002 Wi-Fi pós-save/reboot | FALHA | HW | SSID selecionado não conectou ao roteador; AP reapareceu |
| NET-003 estado real do AP | FALHA | HW | painel mostrou "AP desligado" enquanto SSID permanecia visível |
| NET-004 Ethernet/mDNS pós-hotplug | PARCIAL | HW | IP DHCP `192.168.100.22` abriu; `pu2pny.local/wizard` não acompanhou o fluxo imediatamente |
| PROTO-002 D-Star | FALHA | HW | MMDVMHost não permaneceu ativo; rollback executado |
| PROTO-003 YSF | FALHA | HW | mesmo padrão; rollback executado |
| PROTO-005/006 preflight MQTT | FALHA | HW/DOC | log: `MQTT Error connecting: No such file or directory`; precisa diagnóstico antes do restart |
| LIVE-002 submenu atividade | FALHA | HW | abre e fecha com atualização |
| LIVE-003 BER/RSSI condicional | PENDENTE | HW | campos vazios ocupam a tela |
| LIVE-004 duração destacada | PENDENTE | HW | tempo difícil de localizar |
| DISPLAY-002..005 Nextion runtime | FALHA/PARCIAL | HW | flicker/retângulo vermelho e dados instáveis |
| APRS-001 notificação | PARCIAL | HW/browser | permissão negada; precisa fallback in-app |
| WIZ-001 idioma inicial | PENDENTE | DOC | requisito novo registrado |
| UI/NET diagnóstico Expert/rota | PENDENTE | DOC | requisito novo registrado |

## Diagnóstico técnico atual do erro MQTT

**Fato HW:** antes da falha, o MMDVMHost encerra normalmente por SIGTERM. Na tentativa com D-Star/YSF, o novo MMDVMHost registra erro de conexão MQTT e o serviço cai; a transação restaura a configuração anterior.

**Fato DOC/código:** a imagem 0.3.3 configura Mosquitto em loopback e o serviço MMDVMHost declara dependência de `mosquitto.service`. O aplicador multi-protocolo reescreve a configuração e reinicia MMDVMHost, porém hoje não executa um gate explícito comprovando que o broker está acessível para o usuário do rádio imediatamente antes do restart.

**Conclusão permitida neste momento:** existe uma falha no caminho de restart/preflight MQTT durante troca de protocolo. **A causa raiz exata ainda não é HW confirmada**; não atribuir a broker, biblioteca, arquivo ou permissão sem capturar estado runtime no momento da falha.

## Próxima sequência obrigatória

Rede/Wizard primeiro; depois preflight RF/MQTT; DMR regressão; D-Star; YSF; somente então Live/UI/Nextion/APRS. Cada bloco só avança após testes do bloco anterior e rollback disponível.

## Implementação 0.3.4 já staged

O código corretivo está na branch de trabalho, mas os estados HW da tabela acima continuam válidos até novo teste físico.

- Rede/Wi-Fi: correção staged; **SW/CI pendente, HW pendente**.
- Estado real do AP: correção staged; **SW/CI pendente, HW pendente**.
- MMDVMHost/MQTT/D-Star/YSF: preflight e rollback determinístico staged; **não chamar D-Star/YSF de funcionando antes do HW**.
- Ao Vivo, idioma, Expert, APRS e rodapé: implementação staged; **SW/CI pendente**.
- Nextion: mudança de renderização staged; **HW obrigatório** para confirmar ausência de flicker.
- Artefato 0.3.4: **ainda não liberado** até ARM64 + validação estrutural + SHA-256.

A causa raiz do erro observado ao trocar protocolos permanece classificada como não confirmada em HW. O código agora impede uma troca quando o endpoint MQTT local não está pronto e produz evidência mais específica para o próximo teste.

## Build 0.3.4-alpha publicado

**Estado do artefato:** SW PASS / Alpha para teste físico.

- GitHub Actions: source PASS.
- Build ARM64: PASS.
- Validação estrutural da imagem: PASS.
- SHA-256: gerado e anexado à release.
- Publicação: prerelease `v0.3.4-alpha`.
- Tamanho da imagem comprimida: 584112608 bytes.
- SHA-256 da imagem: `4bc808da8f4c3fc259dd72a66a08e68e1a704b5cf13f754692c9864b40282e2c`.

**Importante:** isso não muda os casos HW que ainda estavam FAIL/PENDENTE. Wi-Fi pós-reboot, DMR regressão, D-Star, YSF, Nextion e comportamento físico do Ao Vivo precisam ser retestados no Raspberry Pi/MMDVM/display real antes de qualquer estado PROD.
