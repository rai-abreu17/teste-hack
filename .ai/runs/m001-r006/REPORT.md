# R006 — localização dos erros e critério empresarial

Concluída: 54 quadros existentes, 45 comparações, 18.000 registros por célula. Nenhuma nova captura. O protocolo foi registrado por SHA-256 antes da execução. A meta informada pelo usuário foi registrada separadamente como erro relativo absoluto de volume total de no máximo 5%.

## Resultado perante 5%

| Método | Total dentro de 5% | Total acima de 5% | Parcial/sem decisão de total |
|---|---:|---:|---:|
| fixed3, mediana | 2/9 | 2/9 | 5/9 |
| aimed, mediana | 2/9 | 2/9 | 5/9 |
| aimed, mediana inferior | 2/9 | 2/9 | 5/9 |
| aimed, κ=2 + mediana | 2/9 | 2/9 | 5/9 |
| aimed, κ=2 + mediana inferior | 2/9 | 2/9 | 5/9 |

Essa é uma avaliação descritiva dos dados de desenvolvimento. Não é validação reservada, física ou do sensor real. As cenas parciais não foram contabilizadas como totais aprovados. Vazio tem erro relativo indefinido; o diagnóstico atual não contém uma cena vazia.

## Evidência espacial

Na referência fixed3, a região de transição/sombra contém:

| Cena | Fração da área suportada | Fração do erro espacial | Fração do volume verdadeiro suportado |
|---|---:|---:|---:|
| Pirâmide central | 30,00% | 85,75% | 73,60% |
| Pirâmide deslocada | 30,00% | 86,44% | 73,60% |
| Duas pilhas | 32,00% | 92,32% | 100,00% |
| Prisma | 14,29% | 83,97% | 28,95% |
| Rampa | 20,00% | 84,36% | 36,00% |
| Pirâmide com viga | 24,29% | 85,64% | 72,22% |
| Pirâmide com viga e dropout | 25,42% | 85,21% | 66,12% |

A densidade de erro por área é maior nessas regiões para ambas as aquisições em todas as sete cenas com relevo. A condição diagnóstica de concentração foi observada. Isso localiza o erro, mas não demonstra sozinho a causa: em duas pilhas, por exemplo, a faixa rotulada contém todo o material. A região de sombra representa somente bloqueio potencial pela viga; não modela a oclusão pela própria pilha.

Na camada plana, fixed3 apresenta apenas 0,197% de erro líquido no domínio comum. Porém o FoV contínuo ideal alcança 324 células, os retornos preenchem 64 bins e a TIN sustenta 256/400 células. Há 2,43 litros de volume de referência fora do suporte. Com aimed, o FoV alcança 328 células e os retornos 136 bins, mas o suporte continua em 256. Erro local e cobertura insuficiente são problemas diferentes; aqui a limitação para declarar total é cobertura.

O domínio comum desta rodada é a interseção **dos dois braços avaliados**, não a interseção histórica dos oito braços P001. Na cena dropout ele contém 183 células, em vez das antigas 45. Não comparar diretamente percentuais desses domínios diferentes como melhora de algoritmo.

## Limites e verificações

Seis testes do avaliador passaram: diagonal coplanar excluída, quina mantida, segmento de sombra limitado ao alvo, distinção FoV/centros discretos, cancelamento espacial e partições sem preenchimento de lacunas. O executor verificou os 54 hashes de quadros, equivalência das medianas, referência integrada e conservação de área/volume/erro entre partições.

As máscaras de transição usam faixa fixa de 1,5 cm definida no protocolo. São rótulos apenas do avaliador. Não representam probabilidade calibrada de erro ou observação física. A metrologia do sensor real e a latência de atualização não foram validadas.

## Artefatos

- [Mapas de erro e cobertura](results/maps.svg)
- [Resumo por cena e método](results/summary.csv)
- [Métricas e partições](results/results.json)
- [Registros por célula](results/cells.jsonl)
- [Triângulos e dados por vista](results/views.jsonl)
- [Hashes](results/hash-manifest.json)
