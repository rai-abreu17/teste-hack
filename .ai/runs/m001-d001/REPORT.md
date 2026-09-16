# D001 — reconstrução por planos observados

**SIMULADO, desenvolvimento. Candidato reprovado para a meta empresarial de erro relativo do volume total ≤5%.** Foram reutilizados 54 quadros de P001, sem novas capturas ou consumo da rodada reservada R007. As 36 comparações mantêm a aquisição fixa dentro de cada par.

| Aquisição | Método | Total dentro de 5% | Total acima de 5% | Parcial |
| --- | --- | ---: | ---: | ---: |
| fixed3 | R005 de referência | 2 | 2 | 5 |
| fixed3 | D001 | 0 | 0 | 9 |
| translated3_aimed | R005 de referência | 2 | 2 | 5 |
| translated3_aimed | D001 | 1 | 1 | 7 |

## O que foi testado

Um candidato único agrupa triângulos vizinhos em planos de altura ajustados a pelo menos quatro vértices distintos, com resíduo vertical máximo de 2 mm e aresta local máxima de 10 cm. Triângulos sem grupo consistente são rejeitados. Os planos podem preencher regiões internas ao casco convexo a até 5 cm de um vértice; esse preenchimento tem rótulo explícito de **modelo**. Não há extrapolação para fora do casco. A mediana convencional foi mantida entre vistas, com prioridade para o suporte local sobre o preenchimento por modelo.

O rótulo interno `observed` significa domínio de interpolação dos triângulos aceitos, não área medida diretamente pelo sensor. Suporte de modelo tampouco comprova visibilidade ou continuidade da superfície. Nenhuma verdade ou identificação de cena entra no estimador. Segmentação, ajuste de plano e preenchimento formam uma intervenção conjunta; esta rodada não separa a contribuição causal de cada componente.

O protocolo e sete arquivos de fonte/teste foram selados antes da pontuação. SHA256 do protocolo: `774f27ef7e547f1939c79f8f43acc93d0f6813e111c0cb0c07c42d3c808070ea`. Houve previamente um smoke da pirâmide central sem verdade, que informou cobertura; as cenas já eram conhecidas e a rodada não é cega.

## Cobertura: células de 400

| Cena | fixed3 R005 → D001 | Modelo em D001 | aimed R005 → D001 | Modelo em D001 |
| --- | ---: | ---: | ---: | ---: |
| Pirâmide central | 400 → 382 | 12 | 400 → 384 | 8 |
| Pirâmide deslocada | 400 → 376 | 39 | 400 → 392 | 38 |
| Duas pilhas | 400 → 354 | 28 | 400 → 370 | 24 |
| Prisma | 336 → 388 | 66 | 380 → 400 | 26 |
| Rampa | 400 → 399 | 51 | 400 → 400 | 48 |
| Camada | 256 → 256 | 0 | 256 → 256 | 0 |
| Pirâmide com viga | 280 → 271 | 6 | 384 → 369 | 15 |
| Camada com viga | 176 → 176 | 0 | 240 → 240 | 0 |
| Pirâmide com viga/dropout | 240 → 225 | 3 | 199 → 178 | 3 |

A aquisição primária fixed3 perdeu todos os quatro totais elegíveis que a referência tinha. No prisma houve ganho de suporte, mas nenhum total no braço primário. As camadas mantiveram exatamente as lacunas anteriores.

## O resultado favorável isolado não justifica promoção

O prisma com três posições chegou a 400 células, com 26 células sustentadas apenas pelo modelo. Volume verdadeiro: **1,6875 L**; estimado: **1,71364 L**; erro líquido: **1,55%**. Contudo, a soma dos módulos dos erros de volume por célula foi **32,25%** do volume verdadeiro. Há cancelamento espacial expressivo: o acerto líquido do total não significa reconstrução correta da forma. Este resultado cumpre numericamente o limiar nessa cena simulada; não aprova o método no conjunto nem constitui validação física.

A revisão independente localizou o cancelamento: nas 380 células comuns, o candidato superestimou **93,639 mL**. Nas 20 células adicionadas, o modelo previu **zero**, enquanto a referência contém **67,5 mL**. O saldo caiu para **+26,139 mL**. Esse zero é uma previsão do plano reconstruído, não uma conversão das células ainda indisponíveis em zero. O fechamento da cobertura nominal introduziu uma subestimação que compensou erros em outra região.

A rampa no mesmo braço permaneceu total, mas piorou de **10,91%** para **12,59%** de erro absoluto. Na pirâmide deslocada fixed3, o erro espacial no domínio comum passou de **30,29%** para **45,98%**. Domínios comuns são calculados separadamente em cada par desta rodada; seus erros não devem ser comparados diretamente aos de outros recortes históricos.

Tempo de processamento dos três quadros pelo candidato: **50,7–226,2 ms** nesta execução local única. Não é medição embarcada, latência ponta a ponta ou benchmark repetido; a exigência empresarial de intervalo de atualização ainda não foi definida.

## Verificação e revisão

- **9/9 testes passaram**, incluindo rejeição de quadros inválidos/indisponíveis mesmo quando outra vista preenche 400 células; mediana, separação de suporte e limite do casco.
- Um teste documenta a ambiguidade: quatro pontos de um degrau podem pertencer exatamente a um plano inclinado. O teste confirma a limitação, não a resolve.
- **47 artefatos históricos**, **65 hashes de R006** e **67 hashes de D001** conferidos. São conjuntos sobrepostos, não 179 arquivos distintos.
- Sol implementou e outro Sol revisou o código de forma independente. Opus executou crítica geométrica prévia com contexto autocontido. Revisão pós-execução e arbitragem têm registros próprios.
- Nenhum limiar foi reajustado após a pontuação. Código de produção e resultados anteriores foram preservados.

As advertências de Opus sobre planos falsos e cascos sobre lacunas são pertinentes. Não adotamos suas afirmações universais de resolução por Nyquist, causalidade exclusiva da amostragem ou subestimação de 36% por área ausente: elas não decorrem destes resultados. Estimativas parciais não foram preenchidas com zero. A fusão existente é por célula, não mediana de totais com áreas distintas.

## Decisão e continuidade

Manter R005 como controle experimental e arquivar D001 sem promoção. R007 permanece reservada. O próximo ensaio deve separar a cobertura de aquisição da reconstrução: fixar R005 e testar uma geometria de captura previamente definida, contabilizando o possível ganho de cobertura e a perda de amostragem dos relevos. Não há justificativa para uma nova varredura de tolerâncias de D001 nestas cenas.

A arbitragem definiu **D002: fixed3 a 0,40 m versus 0,50 m**, R005 congelado, mesmas nove cenas e sequências. Reutilizar os 27 quadros de controle e gerar somente 27 candidatos após o pré-registro. D002 ainda não foi executada. A altura maior pode ampliar o domínio nas bordas e reduzir a densidade de pontos sobre os relevos; a proposta testa esse efeito conjunto, sem promessa de melhora. Astra escolheu R005 em vez da sugestão de Sol de carregar D001 para a comparação, evitando misturar a perda de cobertura da segmentação com a nova pergunta.

Arquivos: [protocolo](../../experiments/m001/protocol_d001.json), [resultados](results/results.json), [tabela](results/summary.csv), [diagnósticos do estimador](results/details.json), [validação](validation.json), [revisão Sol](sol-review.md), [crítica Opus](../m001-d001-opus/001-investigator/result.md), [arbitragem Astra](astra-decision.md).
