# D004 — comparação pareada de cinco vistas

**SIMULADO, desenvolvimento.** A pontuação foi executada somente após liberação independente. O estimador D003, as poses e os limiares permaneceram congelados.

## Gates

- Candidato total elegível: **9/9**.
- Candidato total elegível e dentro de 5%: **9/9**.
- Candidato parcial: **0/9**.
- Gate de cobertura 9/9: **PASSOU**.
- Gate empresarial 9/9 total e <=5%: **PASSOU**.

Estimativas parciais nunca foram tratadas como volume total.

## Resultado por cena

| cena | suporte controle | suporte candidato | delta | ganhas | perdidas | erro total candidato | erro espacial próprio candidato |
|---|---:|---:|---:|---:|---:|---:|---:|
| pyramid_center | 400 | 400 | +0 | 0 | 0 | 1.093% | 3.299% |
| pyramid_shifted_013 | 400 | 400 | +0 | 0 | 0 | 1.033% | 6.525% |
| two_stacks | 400 | 400 | +0 | 0 | 0 | 0.027% | 9.236% |
| prism | 400 | 400 | +0 | 0 | 0 | 3.263% | 21.135% |
| ramp | 400 | 400 | +0 | 0 | 0 | 1.339% | 18.859% |
| layer | 324 | 400 | +76 | 76 | 0 | 0.117% | 0.236% |
| pyramid_beam | 400 | 400 | +0 | 0 | 0 | 2.789% | 8.720% |
| layer_beam | 324 | 400 | +76 | 76 | 0 | 0.141% | 0.260% |
| pyramid_beam_dropout20 | 400 | 400 | +0 | 0 | 0 | 3.091% | 10.025% |

## Integridade

- Protocolo: `ddfcf8013a9661b81679e9efce1544afd35f1bd1c3dc9785edc7135fbceff521`.
- Estimador D003: `bdc14436bf06d54ca2d43bc90da40a937817a39d6f5779fd5627817663b0df83`.
- Liberação pré-score: `a5bba458fe3502ce60cefd2fdd79aec3558c008bfb638c259067b4823392b99d`.
- Foram usados cinco quadros por braço e cena, com o mesmo binário central nos dois braços.
- R007 não foi usado.

Os resultados continuam limitados ao simulador ideal e às nove cenas de desenvolvimento já inspecionadas.
