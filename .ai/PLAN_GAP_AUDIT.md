# Auditoria do plano do chip ToF — 15/09/2026

Documento confrontado: [plano-chip-tof-wokwi-boxflow.md](../plano-chip-tof-wokwi-boxflow.md). Esta é uma comparação com código e evidências locais existentes. O plano foi tratado como referência para a auditoria solicitada, não como autorização para substituir automaticamente decisões posteriores ou implementar tudo nesta etapa. Não foram repetidos testes nem realizadas novas capturas.

**Conclusão atualizada em 16/09/2026:** existe um mock geométrico com protocolo, firmware, receptor e dashboard, mas o objetivo de demonstrar o percurso completo no Wokwi ainda está pendente. A interface de troca e o backend simulado foram implementados depois desta auditoria; o backend físico ainda não existe. A pesquisa de precisão avançou, porém não encerrou a integração nem atingiu a meta geral.

## Comparação das oito etapas

| Etapa do plano | Situação encontrada | O que falta ou diverge | Evidência |
| --- | --- | --- | --- |
| 1. Contrato próprio | Implementado por uma alternativa documentada | Nome `boxflow-lidar`; identificação `BFLD`/versão/CRC; endereço `0x42`. Não existem `WHO_AM_I=0xBF`, endereço `0x29` ou taxa de 15 Hz como descritos no plano. | [Contrato](../docs/CONTRATO.md), [sketch](../wokwi/sketch.ino), [configuração](../wokwi/config.h) |
| 2. Modelo geométrico | Implementado parcialmente em relação ao plano | Ray casting com direções normalizadas, piso, paredes, cinco formas e viga; considera distância oblíqua. Não há ruído gaussiano configurável, largura/profundidade livres da carga ou deslocamento independente Y da carga. Dropout não é ruído gaussiano. | [Gerador](../wokwi/boxflow-lidar.chip.c), [controles](../wokwi/boxflow-lidar.chip.json) |
| 3. Registradores e interrupção | Protocolo alternativo pronto; interrupção ausente | Quadro próprio de 704 bytes com ponteiro de dois bytes, comando de captura e polling. Não há mapa `0x00–0xCF`, seleção 4×4/8×8, pino INT nem leitura orientada a interrupção. | [Contrato](../docs/CONTRATO.md), [callbacks](../wokwi/boxflow-lidar.chip.c), [aquisição](../wokwi/sketch.ino) |
| 4. Definição JSON | Implementada com outra configuração | Só VCC/GND/SCL/SDA; faltam INT e LPn. Display de 256×218, em lugar de 96×96, já funciona no teste WASM. Há controles de altura relativa, forma, centro X, pose do sensor, oclusão e falhas; não os seis controles exatos do plano. | [Chip JSON](../wokwi/boxflow-lidar.chip.json), [diagrama](../wokwi/diagram.json), [framebuffer](../docs/framebuffer.png) |
| 5. Código do chip | Núcleo implementado e testado em host WASM | Inicialização, estado, I²C, timer e heatmap existem. Captura é disparada por comando, dura 100 ms e não produz interrupção. O firmware tenta capturar a cada 3 s; não é ranging contínuo de 15 Hz. | [Chip C](../wokwi/boxflow-lidar.chip.c), [teste WASM](../tests/test_wasm.mjs), [resultado existente](../build/wasm-results.txt) |
| 6. Abstração do sensor no ESP32 | Interface e backend simulado implementados | `ITofSensor`, `SimTofSensor` e seleção `BOXFLOW_SIM` existem; o backend físico ainda falha explicitamente na compilação até ser implementado. Driver físico e calibração continuam pendentes. Volume permanece no servidor. | [Interface](../wokwi/ITofSensor.h), [backend](../wokwi/SimTofSensor.cpp), [relatório](runs/m001-driver-abstraction/REPORT.md) |
| 7. Caminho ao dashboard | Componentes HTTP implementados; **integração completa pendente** | Wi-Fi Wokwi-GUEST/canal 6 existe. Transporte é binário por HTTP, com servidor Python/SQLite e consultas HTTP no navegador. MQTT e WebSocket não foram implementados. Endpoint padrão usa gateway privado/local. O trajeto completo ESP32 emulado → mock → rede → dashboard ainda não foi observado com esta revisão. | [Sketch](../wokwi/sketch.ino), [configuração](../wokwi/config.h), [servidor](../server/app.py), [painel](../server/static/app.js), [testes e limites](../docs/TESTES.md) |
| 8. Verificação antes de apresentar | Compilação e testes de componentes feitos; **aceitação final pendente** | Há registros de compilação ESP32, execução WASM, testes HTTP e comparação analítica offline. Isso não comprova execução do ESP32 no Wokwi nem volume calculado pelo firmware. Identidade é validada pelo contrato alternativo, não WHO_AM_I. A meta geral de 5% não foi atingida. | [Compilação](../build/firmware-compile.txt), [testes](../docs/TESTES.md), [D001](runs/m001-d001/REPORT.md) |

## Mudanças documentadas que não devem ser desfeitas como se fossem esquecimentos

- **Escala de 30×30 cm:** [DECISOES.md](../docs/DECISOES.md) registra uma orientação posterior do usuário substituindo a maquete de 60×60 cm. Não há justificativa para restaurar 60 cm só para reproduzir o plano antigo.
- **Protocolo próprio BFLD/0x42:** já está documentado e integrado ao firmware e ao receptor. Mudar apenas o endereço ou adicionar WHO_AM_I não tornaria o mock compatível com o VL53L5CX. Falta sobretudo a abstração de driver, não uma troca cosmética de endereço.
- **HTTP em lugar de MQTT:** há implementação aproveitável, com tratamento de falhas e histórico. MQTT continua ausente em relação ao plano, mas não é necessário reescrever o transporte para demonstrar o sistema se HTTP continuar sendo a arquitetura escolhida.
- **Display maior e blocos de 28 bytes:** são realizações alternativas das finalidades do plano. Não são trabalhos que precisam ser refeitos para obter 96×96 ou exatamente 32 bytes.
- **Volume no servidor:** é uma divergência arquitetural explícita. A fórmula simplificada `H−d` do plano não deve ser aplicada diretamente a distâncias oblíquas. O receptor existente usa direções, pose e referência do piso. Afirmar que a produção está pronta e que basta trocar o driver seria incorreto: também faltam adaptação de validade, relógio, pose e calibração.

## Trabalho anterior ignorado na proposta D002

Já existe um ensaio de **35, 40, 45 e 50 cm** sobre vazio, pirâmide central e camada:

- [Script](../tools/check_mounting.py).
- [Resultados arquivados](../build/mounting-comparison.json).
- [Tabela e interpretação](../docs/MONTAGEM_30CM.md).

| Cena | Suporte a 40 cm | Suporte a 50 cm |
| --- | ---: | ---: |
| Vazio | 100% | 81% |
| Pirâmide central de 7,5 cm | 100% | 81% |
| Camada de 7,5 cm | 64% | 49% |

Logo, a hipótese de elevar a montagem não é nova e já tem evidência desfavorável nestas cenas. A D002 proposta acrescentaria outras condições e a organização em três quadros, mas não poderia ser apresentada como primeiro teste de altura. Nas cenas determinísticas sem dropout, repetir a mesma pose não cria novas interseções geométricas. Qualquer continuação precisa primeiro verificar equivalência/proveniência e reutilizar esses resultados; não gerar novamente todo o ensaio por padrão.

**D002 suspensa antes de novas capturas.** O protocolo e eventual runner são rascunhos, não experimento concluído. A crítica Opus solicitada durante a preparação terminou em timeout; não há parecer completo a atribuir a essa execução. Isso não bloqueia esta auditoria documental.

## Pendências prioritárias

1. **Fechar a demonstração integrada no Wokwi:** registrar execução do ESP32 com o chip atual, leitura de 64 zonas/704 bytes/CRC, envio aceito pelo receptor e atualização do dashboard; incluir uma falha e recuperação. Reutilizar circuito, firmware, chip e painel existentes.
2. **Implementar o backend físico sobre a separação já criada.** Integração e validação com VL53L5CX real continuam dependentes de driver/calibração e ensaios próprios; a interface concluída não encerra isso.
3. **Reconciliar plano e arquitetura atual:** HTTP versus MQTT, processamento no servidor versus firmware, polling versus INT e cadência. Registrar quais requisitos continuam obrigatórios antes de implementar recursos divergentes indiscriminadamente.
4. **Completar recursos ainda ausentes se mantidos no escopo:** ruído configurável, dimensões e posição Y da carga, INT/LPn e ranging contínuo. Esses itens não estão cobertos por dropout, movimento do sensor ou testes offline.
5. **Continuar a investigação de precisão sem confundi-la com integração:** 5% do volume total permanece requisito não demonstrado de forma geral. Aproveitar diagnósticos e ensaios já feitos; R007 continua reservada.

As afirmações externas do plano, como “primeiro sensor ToF da comunidade” e disponibilidade de recursos/planos Wokwi, não foram verificadas nesta auditoria de implementação. Elas não devem ser tomadas como evidência de conclusão do projeto.

Revisão: o agente independente `/root/d002_review` (GPT-5.6 Sol) conferiu as etapas6–8 com acesso ao código e aos registros e confirmou as lacunas de driver, transporte alternativo e ausência de execução integrada. Não atribuímos aprovação à tentativa Opus incompleta da D002.
