# Revisão independente pós-pontuação — M001-D004

Data: 2026-09-16. Escopo: integridade e validade da pontuação D004 já produzida. Nenhum código, protocolo, captura ou resultado foi alterado.

## Parecer

**O resultado D004 é válido como evidência simulada de desenvolvimento e o gate pré-registrado realmente passou.** O candidato obteve total elegível em 9/9 cenas, nenhum parcial e erro absoluto do volume total menor ou igual a 5% em 9/9. O maior erro foi 3,263%, em `prism`.

Esse resultado **autoriza somente preparar uma validação reservada**, com protocolo e artefatos novamente congelados antes de abrir R007. Ele não declara R007 validada, não autoriza incorporar R007 ao desenvolvimento e não demonstra precisão física, desempenho de hardware ou prontidão para implantação.

## Reexecução e integridade

- Recalculei as 120 entradas de `results/hash-manifest.json`: 120/120 coincidem com os arquivos atuais. SHA-256 do manifesto: `204e83e5c1cc5aed3316d93f24e13d19a1a353aa64b57db56c6b45c5a44cbe89`.
- O protocolo permanece em `ddfcf8013a9661b81679e9efce1544afd35f1bd1c3dc9785edc7135fbceff521`; o estimador D003 permanece em `bdc14436bf06d54ca2d43bc90da40a937817a39d6f5779fd5627817663b0df83`.
- A liberação pré-score usada pela execução permanece em `a5bba458fe3502ce60cefd2fdd79aec3558c008bfb638c259067b4823392b99d`. Por isso este parecer foi criado em arquivo separado e não modifica a liberação que integra a cadeia congelada.
- `experiments/truth.py` tem hash `fb88a8e3db2e9e57b9c813ce05c7a63d021985db28e158571194fa331e9ab351`, igual ao avaliador congelado por D003.
- Reexecutei as 18 reconstruções a partir dos 90 inputs referenciados. Cada objeto retornado pelo estimador coincide integralmente com o respectivo `estimate` em `details.json`.
- Os 90 hashes de input conferem. Há 81 caminhos únicos porque cada um dos nove centros aparece intencionalmente nos dois braços. Em cada par, a interseção dos conjuntos de inputs contém somente o centro compartilhado; as diagonais de controle e candidato não se sobrepõem.
- `results.json` contém 18 registros e nove pares únicos. `details.json` contém nove cenas, cada uma com os dois braços esperados. Não há registro duplicado ou cena ausente.
- Não houve quadro inválido, vista indisponível, conflito de merge, erro Qhull ou ponto coplanar omitido nos 18 resultados.

Hashes dos resultados conferidos:

| Artefato | SHA-256 |
| --- | --- |
| `results/results.json` | `ad93bb17edfe48a3e44e48a37776481c198c7352e25b1e0bbf35894234c77e91` |
| `results/details.json` | `8a708d7becefba30998d6c9bd77a580e2fabee7d3e4c2659abccf2c601358131` |
| `results/summary.csv` | `e88ad5963b7e458b304440d4b735f7ccf4af827c4b64f66f2ea50b5ed52e096c` |
| `validation.json` | `b847a0879905cb4c9e5d8e960ae0f61da5e15487506cfd5fb8e071119817411a` |
| `REPORT.md` | `a9416760d863d22ef43ce147cfae30721b6a06aa01ffb82ef88a915ebfd50909` |
| `run_d004_score.py` | `e824da4fbdc1ce71796723f2ee6a53ba0e47b154591122c42b075d4d50969d5e` |
| `test_d004_score.py` | `6a09986336fda74a4baca6ce0dea28680e1e1c7d9170dd798eacd4164acaf914` |

## Métricas recalculadas

Recalculei os volumes verdadeiros por célula, a integração analítica, os domínios próprio e comum, os erros assinado, absoluto e espacial e a razão de cancelamento diretamente a partir dos `heights`. Todos os valores conferem com os 18 registros e com `summary.csv`.

| Cena | Controle: suporte / erro total | Candidato: suporte / erro total | Ganhas / perdidas | Erro espacial candidato | Cancelamento candidato |
| --- | ---: | ---: | ---: | ---: | ---: |
| `pyramid_center` | 400 / 5,819% | 400 / 1,093% | 0 / 0 | 3,299% | 3,02x |
| `pyramid_shifted_013` | 400 / 3,089% | 400 / 1,033% | 0 / 0 | 6,525% | 6,32x |
| `two_stacks` | 400 / 2,994% | 400 / 0,027% | 0 / 0 | 9,236% | 342,52x |
| `prism` | 400 / 36,387% | 400 / 3,263% | 0 / 0 | 21,135% | 6,48x |
| `ramp` | 400 / 34,332% | 400 / 1,339% | 0 / 0 | 18,859% | 14,08x |
| `layer` | 324 / parcial | 400 / 0,117% | 76 / 0 | 0,236% | 2,01x |
| `pyramid_beam` | 400 / 4,305% | 400 / 2,789% | 0 / 0 | 8,720% | 3,13x |
| `layer_beam` | 324 / parcial | 400 / 0,141% | 76 / 0 | 0,260% | 1,85x |
| `pyramid_beam_dropout20` | 400 / 1,775% | 400 / 3,091% | 0 / 0 | 10,025% | 3,24x |

O controle produziu total elegível em 7/9 e passou o limite de 5% em 4/9. O candidato ganhou 152 células no total — 76 em `layer` e 76 em `layer_beam` — e não perdeu nenhuma. Todos os candidatos terminaram com 400/400 células, zero célula fora do casco e zero célula dentro do casco rejeitada pelo estimador.

O gate empresarial congelado mede erro líquido do volume total, portanto o resultado 9/9 está correto. A fidelidade espacial é uma limitação material: `prism` e `ramp` têm erro espacial de 21,135% e 18,859%, e `two_stacks` combina erro líquido de 0,027% com cancelamento de 342,52x. Isso não reprova o gate definido, mas impede interpretar o 9/9 como reconstrução local precisa. A validação reservada deve manter o reporte de erro espacial e cancelamento ao lado do volume total.

## Isolamento da verdade e R007

A ordem do executor está correta: ele conclui `reconstruct_all(protocol)` para os 18 casos antes de chamar `evaluate_with_truth(reconstructed)`. O único import de `experiments.truth` fica dentro da função avaliadora; `d003_estimator.py` não importa verdade e recebe somente os cinco binários do braço. A verdade aparece apenas na fase posterior, para calcular as métricas dos resultados já reconstruídos.

Os caminhos efetivamente usados pertencem somente aos 36 K4 históricos, nove centros compartilhados e 36 candidatos D004. Nenhum caminho ou input contém R007, e não há arquivo reservado no workspace. O `reserved_R007_used=false` foi, portanto, conferido contra os inputs, em vez de aceito apenas por estar codificado no resultado.

O executor e seu teste não integravam a liberação pré-score como fontes autohashadas; foram gravados antes dos resultados e incluídos no manifesto pós-score. Essa é uma limitação de proveniência, não uma divergência numérica: as fórmulas e gates já estavam congelados no protocolo, o código corresponde a eles, as 18 saídas foram reproduzidas e todas as métricas foram recalculadas independentemente. Uma futura validação reservada deve congelar também o executor e o avaliador explícitos antes de qualquer abertura do conjunto.

## Testes e conclusão operacional

- D003: 8/8 testes passaram.
- D004 aquisição: 7/7 testes passaram.
- D004 pontuação: 8/8 testes passaram.
- Auditoria adicional: 20/20 grupos de verificação passaram, incluindo os 120 hashes, replay das 18 reconstruções, recomputação das métricas, pareamento, overlap intencional do centro, gate e isolamento de R007.

Parecer final: **aceitar o PASS de desenvolvimento D004 e preparar, sem ainda executar nem declarar, a validação reservada**. O novo protocolo deve permanecer 9/9 total e <=5% sem ajustes após abertura, conservar os diagnósticos espaciais e manter separada qualquer evidência física futura.
