# Revisão independente pré-pontuação — M001-D004

Data: 2026-09-16. Escopo: integridade da pré-registração e da aquisição. Nenhum volume, suporte ou erro foi calculado nesta revisão; protocolo, código e capturas não foram alterados.

## Decisão

**LIBERAR a fase de pontuação**, exclusivamente com o estimador D003 e os critérios já congelados em `protocol_d004.json`.

A cadeia de hashes está íntegra, as fontes congeladas continuam idênticas, os 45 quadros históricos selecionados permanecem inalterados, os nove centros são compartilhados por identidade binária, e a aquisição candidata contém exatamente os 36 quadros pré-registrados. Não encontrei erro de pareamento, alteração posterior ao congelamento, execução de verdade/pontuação ou uso de R007 que invalide a comparação.

Esta liberação não aprova cobertura, volume, o gate empresarial nem prepara R007. Ela apenas autoriza calcular os resultados D004 conforme o protocolo congelado.

## Evidência criptográfica recalculada

| Artefato | SHA-256 recalculado |
| --- | --- |
| `protocol_d004.json` | `ddfcf8013a9661b81679e9efce1544afd35f1bd1c3dc9785edc7135fbceff521` |
| `protocol_d004.sha256` | `d958ab2b9b5dffb8952816d236d113c11306795b7cb8a288c52deae07006e60f` |
| `pre-acquisition-manifest.json` | `6ec13daa6f7049123e8649ba22c69cacb5ff6e4b8d7e2426f37cf456e152df5b` |
| `capture-commands.json` | `fbaa0308c9304dee9ed7ef68bb365e6f5580f6816b7669168e51ec643c72f6ca` |
| `acquisition-manifest.json` | `2413dc80b289242d391e51d2aaccac3c8eef048d5289df20c35738e2b30c4c8c` |
| `acquisition-validation.json` | `085df3312acdbec092528c708985f412570556ce9d5e4e4669f7e7d19162cfb6` |
| `d003_estimator.py` | `bdc14436bf06d54ca2d43bc90da40a937817a39d6f5779fd5627817663b0df83` |
| `run_d004.py` | `daeb5cb4f281947b7878cbe1ff7767421e25461c5242395bfce3e79003ac20c6` |
| `test_d004.py` | `9f7560ae5dd26d61b076d1a642b7c389a6a050cfe5b7d914f99aa44b59150533` |
| `scene_dump_m001.exe` | `865f3e1a84e8278d5f31ce8d13b1449ab372433b510b81a575f30e6988cf6e7e` |

O hash declarado no arquivo `.sha256` coincide com o protocolo, com o pré-manifesto, com o manifesto de aquisição e com a validação. Os 15 itens de `frozen_sources` e os 17 itens de `frozen_files` do pré-manifesto foram recalculados contra o workspace, sem divergências. A cadeia `pre-manifesto -> manifesto de aquisição -> validação`, incluindo os hashes do log de comandos e do simulador, também fecha.

Os tempos do sistema de arquivos corroboram a ordem: protocolo e seu hash foram gravados antes do pré-manifesto; o pré-manifesto antecede todos os 36 quadros candidatos; os quadros antecedem ou coincidem com os manifestos finais. O diretório não é um repositório Git, portanto a conclusão sobre ausência de modificação posterior apoia-se na cadeia de hashes congelada e nessa cronologia, não em histórico de commits.

## Reuso e pareamento

- Recalculei os hashes dos 36 quadros K4 `translated4_corners_level-1..4.bin` e dos nove centros `baseline_fixed1-1.bin`; todos coincidem com o pré-manifesto.
- Comparei cada centro selecionado com seu alias `fixed3-1.bin`: 9/9 pares são byte a byte idênticos. O mesmo arquivo central selecionado serve aos dois braços em cada cena.
- Conferi independentemente os 54 registros históricos de captura correspondentes aos 36 K4, nove centros e nove aliases. Cena, `fill`, `shape`, `cx`, obstáculo, dropout, range, sequência e pose coincidem com P001/D004, e cada `stdout_sha256` coincide com o binário arquivado.
- As nove cenas D004 são exatamente as nove cenas de `protocol.json`, na mesma ordem e com os mesmos parâmetros. Não houve seleção de subconjunto.
- Há exatamente nove diretórios candidatos, cada um com uma única captura 201, 202, 203 e 204. Os 36 caminhos do disco são exatamente os 36 caminhos do manifesto; não há arquivo candidato extra ou ausente.
- Os 36 comandos usam os parâmetros de cena corretos e as poses pré-registradas: `(0,1225; 0,1225)`, `(0,1775; 0,1225)`, `(0,1225; 0,1775)` e `(0,1775; 0,1775)` m, sempre em `z=0,40 m` e com yaw/tilt/roll zero. Todos terminaram com código 0, `stderr` vazio e 704 bytes.

## Auditoria dos quadros

Validei os 36 binários diretamente, sem chamar o estimador. Todos possuem envelope de 704 bytes, assinatura `BFLD` v2.1, cabeçalho de 64 bytes, matriz 8 x 8, registro de 10 bytes, geometria 3, range de 4000 mm, payload de 640 bytes, duração de 100 ms, sequência e pose esperadas e CRC-32 válido. Os 2.304 registros de zona têm status/reservado, distância e vetor unitário dentro do contrato.

Amostras inspecionadas:

| Cena / sequência | SHA-256 | CRC-32 | Pose XYZ (m) | Status 0/1/2 |
| --- | --- | --- | --- | --- |
| `pyramid_center` / 201 | `bc8443c907969931ba0c4a7bc480e7924a175316b6752c391d861aee38a8b50a` | `fa018609` | `0,122500002; 0,122500002; 0,400000006` | `7/57/0` |
| `layer_beam` / 204 | `fb1502ffb6ed7ac62800b5ca9db53c6fd5d02cce594567f16dfeec9cf6396e79` | `46acc840` | `0,177499995; 0,177499995; 0,400000006` | `0/64/0` |
| `pyramid_beam_dropout20` / 203 | `9ffe7cac4c041546ac27665ef548b6173ff03d3c933eb92f28a2b0da607ed44a` | `a2fe6ac1` | `0,122500002; 0,177499995; 0,400000006` | `10/54/0` |

As pequenas diferenças decimais das poses são a representação esperada em `float32` e ficam dentro da tolerância congelada de `1e-7`.

## Congelamento do estimador e isolamento

O objeto `estimator` de D004 é estruturalmente idêntico ao objeto `candidate` de `protocol_d003.json`. O hash atual de `d003_estimator.py` coincide com o valor congelado. Não existe import do estimador, de `server`, de R005 ou de módulo de verdade em `run_d004.py`; a aquisição apenas verifica fontes, seleciona quadros arquivados e executa o simulador em modo de quadro.

Nenhum comando D004 usa `--oracle`; não existe diretório `results`, arquivo de score/truth ou saída de volume nesta rodada. Os únicos inputs candidatos são as nove cenas P001 e as quatro poses congeladas. Não há arquivo R007 no workspace, referência R007 nos comandos/caminhos candidatos ou consumo de conjunto reservado.

Há uma ressalva de higiene: `archived_command_map()` abre o `capture-commands.json` histórico completo, que contém 225 registros de captura e 63 registros antigos de `oracle`, antes de filtrar apenas `kind == "capture"`. `load_protocol()` também abre `comparisons.json` para verificar seu hash congelado. A revisão de fluxo mostra que valores de oracle/comparação não são consultados, retornados, usados em condições, incorporados aos comandos nem persistidos na aquisição; uma divergência de hash apenas abortaria a execução. Como as poses já estavam congeladas, as cenas são declaradamente de desenvolvimento e nenhum oracle ou score foi executado, isso não cria um caminho causal de verdade para as capturas e não bloqueia a pontuação. Para rodadas futuras, um manifesto de proveniência contendo somente os registros de captura tornaria esse isolamento mais direto e auditável.

## Testes executados

- `python .ai/experiments/m001/test_d003.py`: **8/8 testes passaram**.
- `python .ai/experiments/m001/test_d004.py`: **7/7 testes passaram**.
- Auditoria independente adicional: **21/21 verificações passaram**, cobrindo cadeia de hashes, 36 K4 + 9 centros + 9 aliases, 36 candidatos, comandos, pareamento 9 x 4, cabeçalhos/CRC/poses, 2.304 registros, inexistência de resultados e ausência de R007.

Parecer final: a pontuação pode prosseguir sem alterar qualquer entrada. Ela deve carregar exatamente os 45 inputs por braço já identificados, usar `d003_estimator.py` no hash acima, manter o centro binariamente comum e aplicar os gates D004 sem ajuste posterior.
