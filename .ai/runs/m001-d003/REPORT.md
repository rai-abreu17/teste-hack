# D003 — triangulação conjunta dos pontos de quatro vistas

**SIMULADO, desenvolvimento. Candidato reprovado para promoção e para R007.** Foram reutilizados 36 quadros da aquisição `translated4_corners_level`; nenhuma captura nova foi produzida. O protocolo foi congelado antes da pontuação sob SHA-256 `e2d769b83910d8e4c2954ff6ab36f5afb8f6884a6991e8e688ed9a37a63ff957`.

D003 transforma os retornos aceitos das quatro vistas para as coordenadas da caixa, combina coincidências XY compatíveis e executa uma única triangulação Delaunay. Não extrapola fora do casco dos pontos. O controle R005 reconstrói cada vista separadamente e aplica a mediana por célula.

## Resultado do gate empresarial

| Resultado D003 nas nove cenas | Contagem |
| --- | ---: |
| Total elegível dentro de 5% | 0 |
| Total elegível acima de 5% | 0 |
| Parcial | 9 |

O gate congelado exigia nove totais elegíveis com erro relativo absoluto ≤5%. O resultado foi **0/9**, portanto falhou sem ambiguidade. Estimativas parciais não foram preenchidas com zero nem apresentadas como volume total.

## Suporte e erro no domínio próprio

| Cena | R005 células | D003 células | D003 erro líquido | D003 erro espacial |
| --- | ---: | ---: | ---: | ---: |
| Pirâmide central | 196 | 196 | +0,89% | 7,38% |
| Pirâmide deslocada | 196 | 196 | −4,82% | 8,34% |
| Duas pilhas | 196 | 196 | −4,04% | 9,47% |
| Prisma | 196 | 196 | +45,71% | 45,80% |
| Rampa | 196 | 196 | +40,33% | 40,72% |
| Camada | 324 | 324 | +0,18% | 0,23% |
| Pirâmide com viga | 172 | 196 | −0,49% | 10,15% |
| Camada com viga | 288 | 324 | +0,19% | 0,24% |
| Pirâmide com viga/dropout | 151 | 196 | −1,05% | 12,05% |

Esses percentuais usam apenas o domínio suportado de cada método. Não são erros do volume total. D003 reduziu o erro espacial em 8/9 cenas e o erro líquido em 6/9, além de recuperar 24, 36 e 45 células nas três cenas com viga/dropout. Isso mostra utilidade diagnóstica para fundir lacunas internas, mas não cumpre a cobertura do total.

Os baixos erros líquidos de pirâmide central, pirâmide com viga e dropout têm razões de cancelamento de aproximadamente 8,29, 20,77 e 11,45. Prisma e rampa continuam fortemente errados mesmo no domínio observado.

## Por que permaneceu parcial

Não houve quadro inválido/indisponível, erro Qhull, ponto coplanar omitido ou conflito no agrupamento. A limitação veio do domínio XY das observações:

- Nas formas localizadas, o casco vai de aproximadamente 0,0378 a 0,2622 m em cada eixo. Isso cobre os centros das linhas/colunas 3–16: `14 × 14 = 196` células.
- Nas camadas, o casco vai de aproximadamente 0,01581 a 0,28419 m. Isso cobre linhas/colunas 1–18: `18 × 18 = 324` células.

As quatro poses K4 arquivadas estão corretas em x/y 0,10 ou 0,20 m, z 0,40 m, sem inclinação. O resultado não decorre de bug do avaliador. A triangulação conjunta não cria informação fora do casco observado.

## Verificação

- **8/8 testes D003 passaram** antes da pontuação.
- Revisão independente confirmou protocolo, separação da verdade, 36 hashes de quadros e critérios de total.
- Auditoria pós-pontuação verificou **48/48 hashes**, 18 registros e nove detalhes.
- SciPy 1.17.0 e NumPy 2.4.2 foram registrados; a documentação atual consultada via Context7 sustenta o tratamento conservador de pontos listados em `Delaunay.coplanar`.
- O candidato combina pooling, fusão de coincidências e triangulação global numa intervenção única; esta rodada não atribui causalidade isolada a um componente.

## Decisão

Arquivar D003 sem ajustar seus limiares após os resultados. A evidência separa duas necessidades: a aquisição/FoV precisa sustentar o domínio total, e a reconstrução precisa respeitar descontinuidades de prisma/rampa. R007 permanece reservada.

Arquivos: [protocolo](../../experiments/m001/protocol_d003.json), [resultados](results/results.json), [tabela](results/summary.csv), [detalhes](results/details.json), [revisão Sol](sol-review.md).
