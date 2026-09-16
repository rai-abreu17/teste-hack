# BoxFlow — resumo dos testes executados e resultados

**Data de consolidação: 13/09/2026.** Este documento reúne os testes e verificações já registrados na conversa e nos arquivos do projeto. Nenhum teste novo foi executado para produzir este resumo.

## 1. Configuração avaliada e significado dos resultados

A versão atual usa maquete de **30 × 30 cm**, paredes de 15 cm, sensor centralizado a 40 cm do piso, **64 zonas em 8 × 8**, campo ideal de 45° por eixo e grade de integração com 400 células de 1,5 cm. A referência é `bench-vl53-30cm-v3` e o quadro binário tem 704 bytes.

O mock usa primeira interseção de raios com uma malha, por Möller–Trumbore. O estimador recebe quadro binário, pose e referência do vazio; não recebe preenchimento, forma, centro verdadeiro da pilha ou volume analítico. Nos experimentos, essas informações ficam somente no avaliador.

**Os resultados são de simulação geométrica.** O mock representa cada zona por um raio pontual; não simula a resposta óptica completa do VL53L5CX. O protocolo I²C 0x42 é próprio, e o firmware entregue ainda não integra o driver do sensor físico.

- `valid`: todos os centros de célula têm suporte; não significa precisão aprovada.
- `partial`: há volume observado, mas o total permanece nulo.
- `unavailable`: medição indisponível ou incompatível com a referência.
- `model_supported`: ajuste aceito sob uma hipótese de forma; não representa cobertura medida completa.
- **pp**: pontos percentuais; amplitude é o maior erro menos o menor erro, não uma margem de precisão.

## 2. Testes funcionais, compilação e comunicação

| Verificação executada | Resultado registrado | Limite da evidência |
| --- | --- | --- |
| Suíte principal Python | **24 testes passaram em 1,105 s** | Funcionamento do software, não precisão física |
| Suíte dos experimentos | **10 testes passaram em 0,185 s** | Verificações numéricas e de contrato |
| Compilação do mock WASM | Sucesso com WASI SDK 25 | Compilação do componente |
| Execução do WASM real no Node | Inicialização, snapshot, blocos de 28 bytes, quadro estável, freeze, NACK, limites, recuperação e framebuffer RGBA passaram | Host de callbacks; não execução do ESP32 |
| Compilação do ESP32 | Sucesso com Arduino CLI 1.5.1 e Arduino-ESP32 3.3.0 | Compilar não comprova execução |
| Uso de memória do firmware | Programa: 1.065.823 bytes, 81%; globais: 48.676 bytes, 14% | Saída do compilador |
| Replay nativo por HTTP | **17 cenas aceitas**, 64 retornos, transporte `native-c-test` | Emissor nativo em C, não firmware ESP32 |
| Rotas e resposta HTTP | `/api/scans`, `/api/latest`, `/api/raw/latest`, página, JS, CSS e saúde: 200; requisição sem autorização: 401; quadro truncado: 400 | Servidor local |
| Interface | JavaScript passou em `node --check`; rotas servidas; favicon: 204 | Não houve nova inspeção visual completa do dashboard atual |
| Integridade da entrega | ZIP conferido por CRC; hashes registrados; código e binários originais preservados na entrega dos experimentos | Integridade dos arquivos |

São **34 testes automatizados aprovados em duas suítes, executadas em momentos distintos**. Esse número não inclui cada cena ou cada posição como se fosse um teste unitário adicional.

A suíte principal verificou geometria e unidades, piso inclinado, transformação de pose, rejeição de referência antiga, deslocamento independente da referência, CRC, direções inválidas, quadros truncados, alcance, ausência de retorno, oclusão, faces verticais, entrada/retirada, HTTP e persistência. Também verificou duplicatas, sequência fora de ordem, identidade repetida com dados diferentes, nova sessão de inicialização, idade da medição e recuperação após falhas.

Os dez testes novos verificaram integração de superfícies lineares e volumes de referência, equivalência com o TIN do servidor, preservação das lacunas, recuperação de uma pirâmide deslocada, rejeição de formas incompatíveis, cancelamento de desvio vertical comum, permanência da deriva posterior, suporte finito da referência medida e rejeição de pacotes corrompidos.

## 3. As 17 cenas da maquete com o TIN original

Volumes em **litros**; 1 L = 0,001 m³. O erro percentual só aparece quando existe total publicado e a referência é diferente de zero.

| Cena | Referência (L) | Observado (L) | Cobertura (%) | Estado | Erro do total (%) |
| --- | ---: | ---: | ---: | --- | ---: |
| vazio | 0,000000 | 0,004441 | 100,00 | valid | — |
| entrada-25 | 0,187500 | 0,208823 | 100,00 | valid | 11,37 |
| entrada-50 | 0,375000 | 0,433881 | 100,00 | valid | 15,70 |
| entrada-75 | 0,562500 | 0,660934 | 100,00 | valid | 17,50 |
| entrada-100 | 0,750000 | 0,905937 | 100,00 | valid | 20,79 |
| redistribuicao | 0,562500 | 0,590570 | 100,00 | valid | 4,99 |
| duas-pilhas | 0,425000 | 0,435754 | 100,00 | valid | 2,53 |
| oclusao | 0,562500 | 0,416720 | 70,00 | partial | — |
| sem-retorno | 0,562500 | — | 0,00 | unavailable | — |
| fora-alcance | 0,562500 | — | 0,00 | unavailable | — |
| retirada-50 | 0,375000 | 0,433881 | 100,00 | valid | 15,70 |
| retirada-25 | 0,187500 | 0,208823 | 100,00 | valid | 11,37 |
| retirada-vazio | 0,000000 | 0,004441 | 100,00 | valid | — |
| prisma | 1,687500 | 1,334769 | 84,00 | partial | — |
| rampa | 0,843750 | 0,934938 | 100,00 | valid | 10,81 |
| camada | 6,750000 | 4,328526 | 64,00 | partial | — |
| principal | 0,562500 | 0,660934 | 100,00 | valid | 17,50 |

As quatro pirâmides centrais, de entrada-25 a entrada-100, **reprovaram a meta de desenvolvimento de erro absoluto até 5%**. Redistribuição e duas pilhas atenderam nesse conjunto; a redistribuição ficou muito próxima do limite, com +4,9903%.

O vazio apresentou resíduo de **0,004441 L**. A pilha principal, de 0,5625 L, foi estimada em **0,660934 L**, erro de **+17,50%**. Viga, prisma e camada mantiveram total nulo por cobertura parcial. Ausência de retorno e falta de alcance não viraram volume zero. Retiradas e cena principal repetem configurações; não são observações independentes de precisão.

## 4. Referência analítica deslocada independentemente

Foram feitas **162 avaliações: 81 desvios em dois perfis**, mantendo os quadros brutos fixos. Apenas a referência usada pelo estimador foi deslocada; o gerador não recebeu o desvio.

| Desvio da referência | Perfil histórico: referência de 6 m³ sobre 48 m² — observado | Maquete: referência de 0,5625 L — observado |
| --- | --- | --- |
| −20 mm | 6,980261 m³; válido | 2,457373 L; válido |
| −10 mm | 6,500261 m³; válido | 1,557373 L; válido |
| 0 | 6,022769 m³; válido | 0,660934 L; válido |
| +10 mm | 5,894006 m³; válido | 0,331650 L; indisponível |
| +50 mm | 5,414006 m³; indisponível | 0,006227 L; indisponível |

Os valores observados em estado indisponível são diagnósticos, não totais aceitos. No perfil histórico, foi reproduzida sensibilidade de **0,48 m³ por centímetro** sobre 48 m². Na maquete, **1 mm sobre 0,09 m² equivale a 0,09 L** quando suporte e corte das alturas não mudam. A resposta pode ser assimétrica e tornar a medição indisponível.

## 5. Comparação controlada: 64 zonas versus 3.185 raios ideais

Foram avaliadas **17 cenas com duas distribuições de raios**, mantendo a mesma maquete, pose, campo, quantização, grade e regra de integração. O perfil denso não é um modo do VL53L5CX nem um LiDAR comercial ensaiado.

| Cena ou medida | 64 zonas | 3.185 raios ideais |
| --- | ---: | ---: |
| Erro da pirâmide entrada-25 | +11,37% | +4,57% |
| Erro da pirâmide entrada-50 | +15,70% | +3,03% |
| Erro da pirâmide entrada-75 | +17,50% | +2,12% |
| Erro da pirâmide entrada-100 | +20,79% | +1,84% |
| Erro da redistribuição | +4,99% | +1,20% |
| Erro de duas pilhas | +2,53% | +1,63% |
| Erro da rampa | +10,81% | +23,02% |
| Prisma | Parcial, 84% de cobertura | Total publicado, mas erro de +25,80% |
| Cobertura com viga | 70% | 75% |
| Cobertura da camada | 64% | 81% |

Nas **sete cenas distintas com total em ambos os perfis**, sem repetições, o erro absoluto médio foi **11,96% com 64 zonas** e **5,34% no denso**. Atenderam à meta de 5%: **2 de 7** e **6 de 7**, respectivamente. O prisma não entra nessa média porque o perfil de 64 zonas ficou parcial.

Mais raios melhoraram a média desse conjunto, mas não resolveram todas as limitações da reconstrução. Rampa e prisma mostraram que cobertura completa e maior densidade não garantem precisão.

## 6. Altura de montagem e cobertura

O primeiro ensaio comparou **quatro alturas do sensor e três cenas**:

| Altura sobre o piso | Vazio | Pirâmide de 7,5 cm | Camada de 7,5 cm |
| --- | ---: | ---: | ---: |
| 35 cm | 64% | 64% | 49% |
| 40 cm | 100% | 100% | 64% |
| 45 cm | 64% | 64% | 81% |
| 50 cm | 81% | 81% | 49% |

Posteriormente foram avaliadas **46 configurações**, com alturas de 28 a 50 cm, passo de 1 cm, para pirâmide e camada. Na camada, 43–46 cm deram 81% de cobertura; 47 cm deram 90%; 48 cm deram 100%; 49 cm caíram para 73%; 50 cm para 49%.

Aumentar a altura não melhora a cobertura de forma monotônica: piso, carga e paredes alteram os retornos úteis. **Subir de 40 para 45 cm não tornou a camada válida; ela continuou parcial.** O resultado de 48 cm é específico dessa configuração.

## 7. E0 — sensibilidade à posição da pilha

Foram testados **21 centros entre 13 e 17 cm, com passo de 2 mm**, mantendo a altura da pilha em 7,5 cm e a referência em 0,5625 L.

| Métrica do TIN original | Resultado |
| --- | ---: |
| Menor erro | +1,39% |
| Maior erro | +17,50% |
| Mediana | +5,20% |
| Média | +6,78% |
| Amplitude | 16,11 pp |
| Desvio-padrão populacional | 5,35 pp |
| Quadros válidos | 21/21 |
| Mudanças de estado | 0 |

A oscilação foi reproduzida. O valor de **6,78% era a média, não a mediana**, no briefing recebido.

## 8. E1 e E2 — recortes e filtro de inclinação

Resultados sobre a **área observada de cada método**. Para os parciais, a referência foi integrada na mesma área; o erro não foi calculado contra o volume inteiro como se houvesse um total válido.

| Método | Mediana do erro (%) | Amplitude (pp) | Desvio-padrão (pp) | Cobertura da base (%) | Totais válidos |
| --- | ---: | ---: | ---: | ---: | ---: |
| TIN original 8 × 8 | 5,20 | 16,11 | 5,35 | 100,00 | 21/21 |
| Recorte 6 × 6 | 4,96 | 16,11 | 5,35 | 49,00 | 0/21 |
| Recorte 4 × 4 | -10,01 | 5,70 | 1,65 | 16,00 | 0/21 |
| Inclinação ≤ 35° | 41,65 | 68,62 | 25,11 | 85,75–87,25 | 0/21 |
| Inclinação ≤ 45° | 11,99 | 19,38 | 6,99 | 94,00–97,75 | 0/21 |
| Inclinação ≤ 55° | 5,20 | 16,11 | 5,35 | 100,00 | 21/21 |

- **Recorte 6 × 6:** não reduziu a amplitude. Observou 49% da base, embora a pilha testada estivesse dentro dessa região.
- **Recorte 4 × 4:** amplitude menor que 8 pp, mas apenas 16% da base observada, perda de 10,4% a 18,2% do volume verdadeiro da pilha e viés mediano de −10,01% na parte mantida. Nas mesmas células, o TIN original já produzia os mesmos valores; a redução da oscilação veio da seleção de região.
- **Inclinação de 45°, configuração principal:** piorou mediana e amplitude, além de produzir lacunas. Não atingiu a meta de 8 pp.
- **Inclinação de 35°:** descartou ainda mais superfície útil e piorou os resultados.
- **Inclinação de 55°:** não alterou a varredura principal.

Todos os filtros foram também aplicados aos 60 casos reservados. Os limites de 35°, 45° e 55° publicaram totais em **14/60, 28/60 e 50/60 casos**, respectivamente. Portanto, pontuar só os casos aceitos daria uma comparação incompleta. O limite de aresta de 10 cm foi mantido como proteção adicional; E2 não substituiu integralmente a regra anterior.

## 9. E3 — ajuste paramétrico de pirâmide e cone

Os modelos estimaram centro, altura e inclinação a partir dos retornos; a base foi derivada desses parâmetros. A forma do modelo foi uma hipótese declarada, não uma informação recebida do gerador sobre a cena. Os parâmetros verdadeiros e volumes analíticos ficaram fora do estimador.

Além das 21 posições principais, foram testados **60 casos reservados**, com 20 posições intercaladas e alturas de pilha de 4,0, 6,5 e 9,0 cm. Configurações e limites foram fixados antes desses ensaios; não foi aplicado fator multiplicativo de correção ajustado à verdade.

| Conjunto | Amplitude TIN (pp) | Mediana do modelo piramidal (%) | Amplitude do modelo (pp) | Desvio-padrão do modelo (pp) | Ajustes aceitos |
| --- | ---: | ---: | ---: | ---: | ---: |
| Principal: 7,5 cm | 16,11 | -0,34 | 0,98 | 0,29 | 21/21 |
| Reservados: 4,0 cm | 16,02 | -0,50 | 2,03 | 0,68 | 20/20 |
| Reservados: 6,5 cm | 15,45 | 0,54 | 0,59 | 0,21 | 20/20 |
| Reservados: 9,0 cm | 14,62 | 0,00 | 0,39 | 0,13 | 20/20 |
| Todos os reservados | 18,49 | 0,07 | 2,32 | 0,58 | 60/60 |

Na cena central, a pirâmide ajustada estimou **0,559502 L**, contra 0,5625 L: erro de **−0,53%**. A altura estimada foi 7,458 cm e a inclinação, 44,83°. O alvo de amplitude menor que 5 pp foi atingido na varredura principal e nas três alturas reservadas.

O ajuste usa critérios de quantidade de pontos, resíduo RMS, resíduo máximo, identificabilidade e base contida no box. Quando recusado, o volume do modelo permanece nulo.

**Controles:** foram avaliadas 18 configurações, incluindo duas pilhas, prisma, rampa, camada, viga, perdas configuradas de retornos, vazio e falta de alcance. A hipótese piramidal recusou as quatro famílias incompatíveis nas 12 configurações correspondentes. Parte delas repete a mesma geometria, porque `centerX` não altera duas pilhas ou camada. Aceitou a pirâmide com viga e perdas configuradas de 20% e 50%, com erros condicionais próximos de −0,5%; recusou vazio e perda total de observação.

**Cone:** recusado em 21/21 casos principais e aceito em apenas 8/60 reservados, embora esses casos fossem pirâmides. Isso mostra que resíduo baixo não identifica automaticamente a forma verdadeira. O resultado dos oito aceitos não sustenta declarar o cone vencedor.

O ajuste piramidal foi o método mais estável **para essa família simulada**. A família ajustada coincide com a geradora: os resultados não comprovam precisão equivalente em pilhas reais irregulares. O volume do modelo é condicionado à forma e fica separado do volume diretamente observado. O dashboard manteve o TIN original.

## 10. E4 — referência medida do vazio

Foram usadas **oito aquisições nativas do vazio**, com média por zona e interpolação da superfície aprendida. O experimento avaliou **48 configurações de injeção**, comparando dois métodos, totalizando **96 registros**: pirâmide e camada, erro vertical declarado e erro de distância radial, aplicados em comum ou somente depois do vazio.

O mock é determinístico: os oito quadros não têm ruído temporal independente. Portanto, esse ensaio não comprova redução de ruído por média.

**Desvio vertical comum ao vazio e à carga:** entre −10 e +10 mm, o resultado com vazio medido permaneceu em **0,660907 L**. O desvio comum cancelou, mas o erro do TIN continuou próximo de +17,5%.

**Desvio vertical surgido após o vazio**, para a pilha verdadeira de 0,5625 L:

| Desvio posterior (mm) | Volume observado (L) | Erro (%) |
| --- | ---: | ---: |
| -2 | 0,577768 | 2,71 |
| -1 | 0,619168 | 10,07 |
| 0 | 0,660907 | 17,49 |
| 1 | 0,750906 | 33,49 |
| 2 | 0,840907 | 49,49 |

De 0 para +1 mm, o volume aumentou aproximadamente **0,09 L**, equivalentes a 16% da referência. A resposta negativa foi assimétrica pelo corte das alturas negativas em zero.

**Erro radial comum:** não cancelou completamente. Com +10 mm, o observado chegou a **0,695957 L**; com −10 mm, ficou em **0,625705 L**, com 81% de cobertura e total nulo. Uma deriva radial posterior de +1 mm deixou 28 pontos fora do suporte aprendido, reduzindo a cobertura para 49%.

**Camada:** a 40 cm de montagem, permaneceu parcial, com 64% de cobertura. A sensibilidade vertical da região observada foi aproximadamente **0,0576 L/mm**, coerente com a área observada de 0,0576 m².

A referência medida compensou a translação vertical comum nas condições testadas; não eliminou deriva posterior, mudanças de suporte ou erro de reconstrução. **E3 e E4 foram avaliados separadamente; sua combinação não foi validada.**

## 11. Conferência dos experimentos e dos arquivos

A grade do TIN experimental foi comparada com a do servidor em cada um dos **99 casos do comparador**: 21 principais, 60 reservados e 18 controles. Os resultados coincidiram. A integração da verdade por células foi conferida contra fórmulas analíticas independentes.

Foram produzidos e inspecionados quatro gráficos: erro por posição, recortes e volume retido, casos reservados e desvio comum versus deriva. Os dados detalhados e quadros binários foram preservados com hashes.

A análise de uma amostra pronta também foi executada pela ferramenta `experiments.analyze_frame`: TIN de **0,660934 L**, modelo piramidal de **0,559502 L** e TIN com referência medida de **0,660907 L** para a cena principal. Essa ferramenta lê o quadro existente sem receber os parâmetros verdadeiros da cena.

O pacote dos experimentos foi conferido com **373 arquivos, 7.495.635 bytes e CRC do ZIP válido**. Os códigos do servidor, mock, firmware e respectivos binários permaneceram iguais à versão-base; os experimentos foram entregues separadamente da lógica do dashboard.

## 12. Wokwi: tentativas e estado final

A criação do Custom Chip no editor foi acessível, mas a conferência das primeiras tentativas de colagem não confirmou arquivos idênticos. O envio por importação foi inicialmente recusado pela revisão automática por falta de autorização explícita.

**O usuário depois autorizou o envio.** A tentativa foi retomada: o seletor anterior estava inválido; um novo seletor foi aberto, mas a conexão de controle retornou timeout. Consultar as abas e tentar uma nova aba também falhou. O resultado do envio não pôde ser confirmado. O bloqueio mais recente foi técnico, não falta de autorização.

**Não foi observada a cadeia completa ESP32 emulado → I²C do mock → gateway → HTTP → dashboard.** Não houve confirmação de execução do firmware atual nem de HTTP originado dele. O transporte HTTP validado continuou sendo `native-c-test`.

O usuário relatou ter aberto e validado o dashboard da versão anterior no próprio navegador. Esse relato não foi contado como uma nova inspeção executada por mim na revisão atual.

## 13. O que não foi testado ou não foi comprovado

- Sensor VL53L5CX físico, driver ULD real, calibração física e leitura por ESP32 real.
- Resposta óptica, luz ambiente, refletância do material, poeira, múltiplos retornos, ruído e mistura de retornos dentro de uma zona.
- Precisão para pilhas reais e irregulares ou desempenho em escala industrial.
- Cancelamento geral de todos os erros de pose e referência.
- Combinação do ajuste piramidal com a referência medida, integrada ao dashboard.
- Servo e nova aquisição com múltiplas vistas; E6 não foi implementado.
- Ensaios de integração por footprint e nove vistas citados no briefing: não foram reproduzidos nesta etapa e não entram nos resultados próprios acima.

A oscilação do mock demonstra limitações de amostragem e reconstrução nesse modelo; não comprova que sua causa seja mistura óptica de pixels. Aprovação funcional, cobertura completa e precisão volumétrica são resultados diferentes.

## 14. Evidências usadas na consolidação

Caminhos relativos à pasta `boxflow-wokwi` do projeto:

- `build/verification-v3.txt` e `build/experiment-tests.txt`.
- `build/wasm-results.txt` e `build/firmware-compile.txt`.
- `build/http-verification-v3.json` e `samples/manifest.json`.
- `build/reference-sensitivity.json`, `build/resolution-comparison.json` e `build/mounting-comparison.json`.
- `build/experiments/comparison.json`, `build/experiments/measured-zero.json` e respectivos hashes.
- `docs/TESTES.md`, `docs/COMPARACAO.md` e `docs/EXPERIMENTOS_64_ZONAS.md`.
- Resultados das tentativas no navegador registrados nesta conversa.
