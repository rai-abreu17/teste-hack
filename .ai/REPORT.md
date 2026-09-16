# BoxFlow — relatório atual de P&D

## Estado de 16/09/2026 — D003 reprovada, abstração compilada, D004 em preparação

A D003 reuniu em uma única triangulação os pontos das quatro vistas K4 já arquivadas. **Nenhuma das nove cenas produziu um volume total elegível**: sete cobriram 196/400 células e as duas camadas, 324/400. O candidato recuperou lacunas internas e reduziu erro espacial em 8/9 cenas, mas prisma e rampa ainda apresentaram erros próprios de 45,71% e 40,33%. Revisão Sol verificou 48/48 hashes; arbitragem Astra rejeitou a promoção. R007 continua intacta.

A causa dominante de parcialidade é o casco dos retornos aceitos não alcançar os centros periféricos. A próxima rodada definida é D004: duas aquisições pareadas de cinco vistas, z=40 cm, estimador D003 congelado e mudança apenas no XY das quatro diagonais. Ela não repete a varredura de altura já concluída. O pré-registro e as 36 únicas capturas novas estão em preparação antes da pontuação.

A lacuna de software entre sensor simulado e físico foi reduzida: `ITofSensor` e `SimTofSensor` foram implementados, preservando o contrato BFLD. O firmware atual foi compilado com Arduino-ESP32 3.3.0 e passou 26/26 testes. O backend físico continua ausente e falha explicitamente se selecionado. Duas tentativas no editor Wokwi não chegaram à simulação por falha de rede/fila remota; a CLI instalada exige um token não disponível. Assim, a execução ESP32 → chip → HTTP → dashboard e hardware real continuam pendentes.

- [Relatório e arbitragem D003](runs/m001-d003/REPORT.md)
- [Decisão Astra D003/D004](runs/m001-d003/astra-decision.md)
- [Abstração e compilação ESP32](runs/m001-driver-abstraction/REPORT.md)

## Auditoria do plano — prioridade revisada em 15/09/2026

A pedido do usuário, a D002 foi suspensa antes das capturas para confrontar o [plano do chip](../plano-chip-tof-wokwi-boxflow.md) com a implementação. A [auditoria das oito etapas](PLAN_GAP_AUDIT.md) registra o que existe, as alternativas documentadas e as pendências.

As lacunas principais são **abstração para troca do driver** e **execução integrada no Wokwi**. Ruído gaussiano, dimensões livres/posição Y da carga, INT/LPn e 15 Hz também não foram implementados. HTTP/servidor em lugar de MQTT/cálculo embarcado e escala30cm em lugar de60cm são diferenças que precisam ser tratadas conforme as decisões posteriores, sem refazer componentes prontos.

A proposta D002 omitiu um ensaio existente de35/40/45/50cm: a50cm, a pirâmide tem81% e a camada49% de suporte. Essa evidência deve ser reutilizada antes de qualquer continuação. O runner/protocolo D002 ficaram como rascunhos; nenhum quadro novo foi gerado.

## D001 concluída — reconstrução por planos reprovada

O novo candidato foi implementado, revisado e comparado com R005 usando **54 quadros existentes, 36 comparações e 9 testes aprovados**. Não houve novas capturas nem alteração dos resultados anteriores. A aquisição foi mantida fixa dentro de cada comparação.

Na aquisição primária `fixed3`, D001 deixou **9/9 cenas parciais**. Com três posições, houve **1 total dentro de 5%, 1 acima e 7 parciais**. O resultado de 1,55% no prisma dependeu de cancelamento: as 20 células adicionadas receberam zero pelo modelo, omitindo 67,5 mL que compensaram excesso em outras regiões; o erro espacial foi 32,25%. A rampa piorou para 12,59%.

**D001 não será promovida.** R005 permanece controle e R007 continua reservada. A próxima rodada deve isolar cobertura de aquisição com estimador congelado, sem reajustar tolerâncias do candidato sobre as mesmas cenas. Hardware permanece não testado.

- [Relatório D001 e tabela de cobertura](runs/m001-d001/REPORT.md)
- [Revisão independente](runs/m001-d001/sol-review.md)
- [Arbitragem D001](runs/m001-d001/astra-decision.md)
- [Validação e integridade](runs/m001-d001/validation.json)

## Execução R005/R006 concluída

A meta informada pela empresa foi interpretada como **erro relativo de volume total até 5%**. As cinco variantes avaliadas têm o mesmo resultado nas nove cenas: **2 dentro da meta, 2 acima e 5 parciais**. Nenhuma solução foi aprovada para o conjunto.

R005 corrigiu contratos de validade e alinhou qualidade/altura da TIN. A mediana convencional reproduziu exatamente os 225 quadros e 72 braços anteriores. Onze testes passaram. R006 reutilizou 54 quadros e gerou 45 comparações, 18.000 registros por célula e mapas de erro/cobertura; seis testes do avaliador passaram.

Os mapas localizam a maior densidade de erro perto das transições nas cenas com relevo. Nas camadas, o obstáculo à declaração de volume total é cobertura. Um contrafactual exclusivo do avaliador mostrou que corrigir perfeitamente a faixa de transição reduziria a pirâmide central para cerca de 3%, mas ainda deixaria a rampa acima de 5% e manteria as cinco cenas parciais. Isso não é resultado de um algoritmo implementável.

**R007 reservada não foi iniciada:** falta um candidato tecnicamente justificado para a meta. O próximo desenvolvimento deve tratar reconstrução nas mudanças de superfície e cobertura de aquisição em ensaios separados. Resultados históricos e seus hashes foram preservados.

- [Decisão vigente R005/R006](decisions/m001-r005-r006-execution.md)
- [Relatório do diagnóstico](runs/m001-r006/REPORT.md)
- [Mapas por cena](runs/m001-r006/results/maps.svg)
- [Critério empresarial de volume](requirements/mvp-volume.md)
- [Revisão independente da execução](runs/m001-r005-r006/sol-review.md)
- [Arbitragem da execução](runs/m001-r006-astra/001-astra/result.md)

O trabalho anterior foi reutilizado. E0–E4, o executor multiagente, as análises cegas, a pesquisa e as críticas cruzadas não foram refeitos.

## Resultado atual

P-001 executou 72 comparações em nove cenas e oito braços. Foram processadas 225 capturas; todas têm 704 bytes e passaram pela validação de quadro. A compilação C passou com `-Wall -Wextra -Werror` e os 7 testes locais passaram.

A translação aumentou a linha de visada ideal: os braços transladados chegaram a 100% de visibilidade mediana no oráculo. Esse oráculo ignora FoV e orientação e não entra no estimador. O ganho geométrico não se converteu em menor erro de forma consistente. Contra `fixed3`, `translated3_aimed` venceu em erro absoluto no domínio comum em 5/9 cenas, com redução mediana assinada de 0,147 ponto percentual, e manteve total válido em 4/9.

A arbitragem real do GPT-6 Astra decidiu manter `fixed3` como referência e `translated3_aimed` como desafiante. Ainda não existe vencedor nem evidência para hardware.

P-002 reutilizou as capturas e testou somente uma aresta TIN mais restrita, 0,07 m contra 0,10 m. O desafiante teve melhora absoluta mediana de 0,419 pp, preservou o domínio original em 4/9 cenas e caiu para 2/9 totais válidos. A mudança foi reprovada.

P-003 testou seleção dura por compactness e foi reprovado apesar de vencer 7/9: a melhora mediana foi 0,795 pp e prisma/rampa regrediram mais de 3 pp. P-004 combinou aparagem com κ=2 e mediana inferior: regressão máxima 0,503 pp, ganho mediano 0,181 pp e 6/9 vitórias. Também foi reprovado. Estes números comparam contra fixed3 e incluem mudanças de aquisição e fusão.

A reavaliação encontrou um confundimento: P-004 não descartou vistas em oito das nove cenas. Nessas cenas, sua diferença frente à mediana da mesma aquisição veio da mediana inferior. No prisma, único caso com descarte, aparar piorou o erro em relação à mediana inferior sem aparagem. A afirmação anterior de mecanismo confirmado foi retirada.

O domínio comum também limita as conclusões: no dropout inclui somente 45/400 células e 16,30% do volume verdadeiro. `fixed3` permanece controle experimental, sem promoção de qualquer solução. Não ajustar candidatos para aprovação sobre estas nove cenas; elas ainda servem para diagnóstico causal e verificação de correções.

## Evidência

- [Resumo P-001](runs/m001-implementation/results/summary.md)
- [Resultados completos P-001](runs/m001-implementation/results/comparisons.json)
- [Resultados P-002](runs/m001-p002/results/comparisons.json)
- [Resultados P-003](runs/m001-p003/results/comparisons.json)
- [Resultados P-004](runs/m001-p004/results/comparisons.json)
- [Arbitragem Astra](runs/m001-astra-final/001-astra/result.md)
- [Decisão técnica inicial](decisions/m001-final-decision.md)
- [Decisão de parada P-004](decisions/m001-p004-stop-decision.md)
- [Reavaliação e próximas rodadas — decisão vigente](decisions/m001-evaluation-next-rounds.md)
- [Diagnóstico fatorial e hashes preservados](runs/m001-evaluation/results/attribution.json)
- [Revisão independente Sol](runs/m001-evaluation/sol-review.md)
- [Revisão independente Opus](runs/m001-evaluation-opus/001-investigator/result.md)
- [Arbitragem da reavaliação](runs/m001-evaluation-astra/001-astra/result.md)
- [Estado das hipóteses](hypotheses/m001-results.md)
- [Estado operacional](STATE.md)

## Próxima ação

R005 e R006 foram executadas. Desenvolver e justificar um único candidato a partir dos achados antes de abrir R007. A meta agora é 5% de erro relativo no volume total; cobertura, abstenções e erro espacial permanecem explícitos. Nenhuma nova captura ou validação reservada foi executada nessas rodadas.

Todos os resultados novos são **SIMULATED**. O simulador não modela resposta finita de zona, histogramas, distorção óptica, ruído real, calibração extrínseca, sincronização ou temperatura.
