# PU2PNY — Plano Mestre do Projeto

**Estado de referência:** 2026-09-18  
**Release em teste físico:** v0.2.3-alpha  
**Repositório:** PU2PNY/2PNY-OS  
**Produto público:** PU2PNY  
**Hostname:** `pu2pny`  
**Acesso principal:** `http://pu2pny.local/`

> Este documento é a referência de continuidade do projeto. Antes de remover, simplificar ou substituir qualquer recurso já funcionando, comparar a mudança com este plano e com os testes de regressão.

---

## 1. Objetivo do PU2PNY

PU2PNY é um sistema operacional próprio para hotspot/repetidora digital baseado em Raspberry Pi + MMDVM. Não é um fork de Pi-Star ou WPSD. Pode utilizar projetos consolidados como MMDVMHost e gateways de protocolos, mas a distribuição, automação, painel, APIs, detecção de hardware, rede, diagnóstico e experiência de uso são próprios.

Objetivos permanentes:

- primeiro acesso simples, com o mínimo de conhecimento técnico;
- configuração guiada sem esconder a possibilidade de ajustes avançados;
- suportar hotspot simplex, MMDVM duplex e modo repetidora;
- suportar protocolos digitais e crossmode de forma modular;
- painel moderno, responsivo, rápido e legível;
- baixo uso de CPU, RAM, disco e escrita no cartão SD;
- baixo aquecimento e ausência de polling agressivo;
- detecção real de hardware, sem adivinhar o modelo;
- funcionamento local mesmo sem Internet;
- atualização segura com backup, validação e rollback;
- diagnóstico claro quando algo falhar;
- nenhuma mudança deve quebrar um recurso físico já validado.

O projeto ainda é Alpha. Não declarar compatibilidade física como concluída sem teste real no equipamento correspondente.

---

## 2. Regra principal de desenvolvimento: preservar antes de ampliar

Toda nova versão deve:

1. partir da última versão fisicamente validada;
2. criar ponto de rollback antes das alterações;
3. preservar rede, RF, MMDVMHost, painel, mDNS e captive portal já funcionais;
4. executar testes de fonte;
5. gerar imagem ARM64;
6. validar checksum;
7. montar a imagem final;
8. executar o painel dentro da própria imagem;
9. testar rotas de primeiro acesso e pós-configuração;
10. somente publicar a Release depois de todos os gates passarem.

Mudanças de arquitetura devem ser modulares. Recursos experimentais não podem bloquear o boot, a rede, o MMDVMHost nem o painel principal.

---

## 3. Fluxo definitivo de primeiro acesso

### 3.1 Antes da configuração

A primeira inicialização deve tentar, nesta ordem:

- reconectar Wi-Fi previamente salvo, se existir;
- obter DHCP via Ethernet, se estiver ligada a roteador/rede;
- disponibilizar acesso direto local;
- iniciar AP de setup quando necessário.

### 3.2 Endereços oficiais

- AP de primeiro acesso: SSID aberto **`pu2pny`**
- AP de primeiro acesso: **`http://10.43.0.1/`**
- cabo direto ao computador: **`http://10.43.0.1/`**
- rede LAN/Wi-Fi normal: **`http://pu2pny.local/`**
- hostname: **`pu2pny`**

O endereço antigo `2pny.local` pode existir apenas como compatibilidade interna/legada. Não deve voltar para a identidade pública nem para a interface.

### 3.3 Ethernet

Cabo conectado a roteador:

- detectar hotplug mesmo depois do boot;
- tentar DHCP automaticamente;
- anunciar `pu2pny.local` por mDNS;
- não exigir que o usuário descubra o IP pelo roteador.

Cabo direto a notebook/PC:

- usar `10.43.0.1`;
- não anunciar gateway ou DNS que derrube a Internet Wi-Fi do computador;
- permitir que o PC continue usando sua própria Internet;
- quando o computador fornecer compartilhamento de Internet, o PU2PNY deve conseguir usar essa rota.

### 3.4 Wi-Fi

A tela de rede deve:

- buscar SSIDs automaticamente;
- mostrar intensidade do sinal;
- mostrar tipo básico de segurança;
- permitir rede oculta/manual;
- permitir mostrar/ocultar senha;
- não exibir `Failed to fetch` quando uma única placa Wi-Fi precisa sair temporariamente do AP para escanear;
- informar claramente que a placa está sendo usada para a busca;
- restaurar o AP se a busca falhar;
- salvar a rede como autoconnect;
- reiniciar já tentando a rede salva.

Com duas interfaces Wi-Fi:

- uma pode permanecer no AP;
- a outra vira uplink Internet.

Com uma interface:

- AP pode ser temporariamente pausado para scan/conexão;
- o backend deve responder primeiro ao navegador;
- depois da conexão, o usuário continua em `http://pu2pny.local/`.

### 3.5 Captive portal

Manter:

- DHCP option 114;
- suporte aos checks comuns de Android, iOS/macOS e Windows;
- abrir o assistente durante o primeiro acesso;
- após provisionado, responder aos checks de Internet normalmente e não ficar preso como rede cativa.

O captive portal é conveniência. O acesso por `10.43.0.1` e `pu2pny.local` sempre deve funcionar mesmo quando o sistema operacional do cliente não abrir navegador automaticamente.

---

## 4. Assistente: simples primeiro, completo depois

Camadas de interface:

### Essencial

Primeiro acesso deve mostrar apenas:

- Internet;
- hardware;
- indicativo;
- DMR ID;
- hotspot ou repetidora;
- frequência;
- protocolo principal;
- operação normal ou crossmode;
- conclusão.

### Avançado

Depois do primeiro acesso:

- redes de cada protocolo;
- servidores/refletores;
- TG/salas;
- color code;
- timeslot;
- potência/níveis suportados;
- display;
- AP;
- áudio/ganho quando aplicável;
- reconnect e watchdog;
- diretórios/RadioID;
- histórico e diagnóstico.

### Expert

Somente para usuários avançados:

- parâmetros completos do MMDVMHost;
- gateways;
- portas;
- logs detalhados;
- calibração;
- parâmetros de modem;
- tuning específico por hardware;
- testes de serviço.

Não colocar parâmetros Expert no primeiro acesso.

---

## 5. Configuração RF

### 5.1 Hotspot simplex

Regra obrigatória:

- **RX = TX sempre**;
- interface mostra apenas uma frequência;
- offsets ficam internos em zero por padrão;
- não apresentar variação falsa RX/TX na conclusão ou no painel.

### 5.2 Repetidora/duplex

Somente nesse modo:

- RX e TX separados;
- permitir frequências distintas;
- Simplex/Duplex deve ser conceito separado de modelo de modem.

### 5.3 Aplicação segura

Manter:

- configuração ativa do MMDVMHost em área gravável `/var/lib/2pny/mmdvm`;
- temporários em `/run`;
- escrita atômica;
- backup da configuração anterior;
- rollback automático se MMDVMHost não iniciar ou não permanecer ativo;
- nenhuma escrita temporária em `/etc` sob serviço protegido;
- Talker Alias preservado para DMR (`DumpTAData=1`).

---

## 6. Detecção de hardware

Nunca adivinhar modelo. O sistema deve dizer claramente: detectado, candidato, não confirmado ou não suportado.

### Raspberry Pi

Detectar:

- modelo/revisão;
- serial/interface útil;
- I²C;
- SPI;
- HAT EEPROM quando disponível;
- interfaces DRM/framebuffer;
- temperatura e estado do sistema para diagnóstico.

### MMDVM

Detectar:

- portas `/dev/serial*`, ttyAMA, ttyS, ttyACM, ttyUSB e by-id;
- resposta real ao protocolo MMDVM;
- GET_VERSION;
- firmware/descrição;
- perfil/capabilities quando possível;
- MMDVM_HS, hats simplex/duplex, ZUMspot e equivalentes;
- baud rates necessários sem sondagem infinita.

A detecção deve ter timeout e nunca prender o assistente.

### Fallback

Se automação falhar:

- permitir continuar para diagnóstico/manual;
- nunca salvar RF em porta vazia ou inventada;
- mostrar motivo simples e log técnico separado.

---

## 7. Displays e Nextion

Suporte de detecção planejado/esperado:

- Nextion/TJC serial direto;
- Nextion ligado à MMDVM;
- HDMI;
- DSI;
- USB display;
- I²C OLED/LCD;
- SPI TFT/OLED;
- framebuffer/DRM do kernel.

### Nextion

Estado atual de referência:

- detecção direta tenta baud comuns;
- Nextion via MMDVM pode usar `Port=modem`;
- layout de compatibilidade atual: `ScreenLayout=2`;
- brilho padrão definido pela configuração do sistema.

Pendência física crítica:

- ser "detectada" não basta; a tela precisa realmente mostrar dados;
- validar firmware/HMI da tela real;
- detectar quando há Nextion conectada mas o projeto HMI não é compatível;
- nunca gravar/atualizar HMI automaticamente sem confirmação, pois isso pode inutilizar uma tela com projeto diferente;
- criar diagnóstico de "display reconhecido, mas sem resposta visual";
- oferecer seleção manual do tipo de display quando necessário.

Suporte de display deve ser modular para incluir modelos futuros sem alterar o RF core.

---

## 8. Protocolos e redes

Protocolos-base já previstos na arquitetura:

- D-STAR;
- DMR;
- YSF/System Fusion;
- P25;
- NXDN;
- POCSAG/DAPNET quando o módulo correspondente estiver pronto.

Módulos/gateways previstos:

- MMDVMHost;
- ircDDB / gateway D-STAR;
- DMRGateway;
- YSFGateway;
- P25Gateway;
- NXDN gateway;
- DAPNET/POCSAG;
- crossmode;
- diretórios RadioID/callsign.

Futuros módulos previamente definidos:

- Dire Wolf / APRS;
- M17;
- OpenWebRX;
- suporte de display/Nextion avançado;
- PU2PNY Remote seguro.

Nenhum módulo futuro deve ser instalado de forma pesada ou ficar ativo consumindo CPU/RAM se o usuário não o utiliza.

---

## 9. Presets e ecossistema XLX026

PU2PNY deve facilitar uso com XLX026 sem bloquear outras redes.

Preset recomendado do projeto quando aplicável:

- D-STAR: XLX026 módulo D;
- DMR hotspot: módulo C / TG 6;
- YSF: YSF72426;
- crossmode deve respeitar a arquitetura do XLX026 e as redes escolhidas pelo usuário.

O preset é conveniência, não hardcode obrigatório. Usuário pode alterar rede/servidor.

---

## 10. Painel principal

Após provisionado, `http://pu2pny.local/` deve abrir o painel operacional, não o assistente.

### Funções mínimas

- estado do MMDVMHost;
- indicativo;
- DMR ID;
- modo hotspot/repetidora;
- frequência;
- protocolo;
- operação normal/crossmode;
- Internet;
- Ethernet;
- Wi-Fi;
- IPs;
- display;
- atividade recente;
- atalhos para Rede, Hardware, Rádio e Assistente.

### Evolução planejada

Inspirado nas necessidades já definidas para os painéis do projeto:

- TX/RX ao vivo;
- indicativo em transmissão;
- protocolo;
- TG/refletor/sala;
- duração de TX;
- BER;
- RSSI quando disponível;
- qualidade/sinal simplificado;
- histórico 24h;
- últimas chamadas;
- RadioID ↔ indicativo;
- nome/cidade quando disponível em diretórios;
- foto QRZ opcional, sem bloquear a página;
- submenu do indicativo;
- diagnóstico do último erro/reconnect.

A página ao vivo deve usar atualização eficiente, preferindo eventos/streaming ou polling adaptativo. Não criar loops agressivos por navegador.

---

## 11. Administração e navegação

Não deixar o usuário "preso" em uma conclusão.

Sempre deve existir:

- botão Painel principal;
- Alterar rede;
- Rever hardware;
- Editar rádio;
- reabrir assistente;
- voltar etapa;
- mostrar o que já foi concluído;
- preservar campos existentes ao editar.

Rotas esperadas:

- `/` → assistente se não configurado;
- `/` → dashboard se configurado;
- `/dashboard` → painel principal;
- `/admin` → painel principal/admin;
- `/wizard` → assistente;
- `/wizard?step=1` → rede;
- `/wizard?step=2` → hardware;
- `/wizard?step=3` → rádio.

---

## 12. Desempenho e consumo

Prioridade permanente: rápido, leve, frio e previsível.

Regras:

- não iniciar gateways não usados;
- preferir serviços sob demanda;
- evitar polling de 1 segundo quando evento/estado cacheado resolve;
- limitar históricos;
- rotacionar logs;
- evitar gravação contínua no cartão SD;
- cache apenas onde reduz custo real;
- nenhuma página deve criar carga proporcional ao número de abas abertas;
- atualização ao vivo deve ser leve;
- evitar processos duplicados;
- watchdog apenas quando necessário;
- serviços devem ter limites razoáveis de memória;
- nenhuma detecção de hardware deve ficar rodando continuamente depois de concluída.

Toda versão importante deve medir:

- CPU idle;
- RSS dos serviços;
- load;
- temperatura;
- espaço em disco;
- crescimento de logs;
- processos;
- tempo de boot;
- tempo até painel responder;
- tempo de scan Wi-Fi;
- tempo até MMDVMHost ativo.

A meta é regressão zero: aumento material de consumo precisa ser identificado e justificado antes da Release.

---

## 13. Segurança e confiabilidade

Manter:

- menor privilégio possível;
- systemd hardening sem tornar diretórios necessários read-only;
- configs graváveis apenas nas áreas adequadas;
- painel local por padrão;
- sem exposição remota perigosa por padrão;
- validação de entrada;
- porta RF validada antes de aplicar;
- atomicidade em arquivos;
- backup e rollback;
- release com SHA-256;
- logs suficientes para diagnóstico;
- CI reproduzível;
- nenhuma senha Wi-Fi em logs de interface;
- funcionalidades remotas futuras somente opt-in, autenticadas e isoladas.

---

## 14. Atualizações e drivers

Princípio:

- usar drivers/kernel modules oficiais já presentes no sistema quando possível;
- carregar rapidamente módulos comuns de serial/I²C/SPI;
- Internet serve para preparar pacotes oficiais, firmware e componentes necessários;
- evitar baixar driver arbitrário em runtime;
- atualização nunca deve quebrar rede/RF já funcional;
- antes de aplicar atualização estrutural, preservar backup/rollback.

Futuro gerenciador de atualização deve mostrar claramente:

- versão instalada;
- versão disponível;
- canal Alpha/Beta/Stable quando existir;
- mudanças;
- backup;
- progresso;
- rollback.

---

## 15. Diagnóstico

O usuário precisa saber o que aconteceu sem abrir SSH.

Painel de diagnóstico futuro deve exibir de forma simples:

- Internet;
- DNS;
- gateway;
- Wi-Fi;
- Ethernet;
- mDNS;
- AP;
- MMDVM;
- serial;
- MMDVMHost;
- display;
- gateways ativos;
- temperatura;
- CPU/RAM;
- espaço;
- último erro;
- último reconnect;
- versão e hash da imagem.

Modo Expert pode expor logs detalhados.

---

## 16. Itens que se perderam ou ficaram incompletos ao longo das versões

Estes pontos não podem ser esquecidos:

- Nextion foi detectada, mas ainda precisa de validação física de conteúdo na tela;
- busca Wi-Fi já regressou em versão anterior e precisa continuar como teste obrigatório;
- primeiro acesso já teve erros de AP/Ethernet/captive portal; qualquer mudança de rede precisa regressão física;
- painel pós-configuração ficou ausente até 0.2.3;
- frequência simplex apareceu divergente em 0.2.2 e agora deve permanecer travada RX=TX;
- BER e RSSI ainda não fazem parte do painel operacional final;
- RadioID ↔ indicativo ainda é roadmap;
- redes completas DMR/D-Star/YSF ainda precisam de telas e presets;
- crossmode existe como perfil básico, mas gateways/ponte completos ainda precisam de implementação e validação;
- APRS/Dire Wolf, M17, OpenWebRX e DAPNET ainda são módulos futuros;
- foto QRZ é opcional/futura;
- histórico 24h e TX/RX ao vivo ainda precisam ser implementados no PU2PNY;
- chamadas privadas/recursos específicos de gateway ainda precisam ser validados;
- painel em camadas Essencial/Avançado/Expert precisa ser concluído;
- suporte físico deve incluir simplex, duplex e diferentes displays, não apenas o hardware atual de teste.

---

## 17. Baseline v0.2.3-alpha a preservar

Esta versão introduziu/validou em CI:

- nome público PU2PNY;
- AP `pu2pny`;
- `10.43.0.1` como primeiro acesso;
- `pu2pny.local`;
- configuração do MMDVMHost em `/var/lib/2pny/mmdvm`;
- rollback RF;
- detecção ampliada de display;
- layout Nextion 2;
- busca Wi-Fi assíncrona para interface única;
- hotspot simplex RX=TX;
- painel principal;
- redirecionamento `/` assistente → dashboard conforme provisionamento;
- edição posterior das etapas;
- imagem ARM64 validada e publicada.

Tudo acima precisa continuar funcionando nas próximas versões, salvo substituição comprovadamente melhor e testada.

---

## 18. Próximo ciclo após o teste físico da v0.2.3

Não adicionar grandes módulos antes de fechar regressões físicas da base.

Ordem recomendada do próximo ciclo:

1. validar boot e primeiro acesso;
2. validar busca Wi-Fi;
3. validar troca AP → Wi-Fi;
4. validar Ethernet em roteador;
5. validar cabo direto;
6. reiniciar e confirmar autoconnect;
7. validar MMDVM;
8. validar frequência simplex;
9. validar Nextion mostrando conteúdo real;
10. validar dashboard;
11. transmitir DMR e confirmar atividade;
12. medir CPU/RAM/temperatura;
13. corrigir regressões encontradas;
14. congelar uma baseline funcional;
15. iniciar painel ao vivo + BER/RSSI + histórico;
16. depois avançar para redes/gateways/crossmode completos.

---

## 19. Matriz de regressão obrigatória

Antes de qualquer Release:

### Rede
- AP aparece;
- captive portal;
- 10.43.0.1;
- busca SSID;
- senha;
- troca Wi-Fi;
- autoconnect após reboot;
- Ethernet DHCP;
- cabo direto;
- pu2pny.local;
- notebook mantém sua Internet quando ligado diretamente.

### Hardware
- modelo Raspberry;
- serial;
- MMDVM;
- firmware;
- display;
- timeout;
- fallback.

### RF
- hotspot RX=TX;
- repetidora RX/TX separados;
- serviço inicia;
- serviço permanece ativo;
- rollback funciona;
- config não grava em /etc protegido.

### UI
- mobile;
- tablet;
- desktop;
- modo escuro;
- modo claro;
- alto contraste;
- conclusão;
- dashboard;
- voltar/editar;
- sem campos técnicos desnecessários no fluxo inicial.

### Performance
- CPU;
- RAM;
- temperatura;
- logs;
- boot;
- tempo de resposta;
- consumo com várias abas.

---

## 20. Regra de continuidade para futuras conversas

Ao iniciar qualquer nova correção ou versão do PU2PNY:

1. consultar este arquivo;
2. comparar a alteração com a baseline atual;
3. marcar se o item é **funcionando**, **em teste**, **pendente** ou **futuro**;
4. não retirar funcionalidades anteriores silenciosamente;
5. registrar no changelog o que foi preservado;
6. atualizar este plano somente quando uma decisão do projeto mudar de verdade.

