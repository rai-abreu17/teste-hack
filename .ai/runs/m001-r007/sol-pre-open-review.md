# Revisão independente pré-abertura — M001-R007

Data: 2026-09-16. Escopo: revisão estática do protocolo, executores, avaliador, estimador, cadeia de hashes e estado pré-abertura. Não houve captura, reconstrução, importação de `experiments.truth` em runtime, pontuação ou criação de release.

## Decisão

**BLOQUEAR.** A pré-inscrição está íntegra e quase todos os controles solicitados conferem, mas existe uma possibilidade material de seleção/reclassificação pós-abertura: a validação de aquisição não vincula semanticamente cada frame à cena e ao comando que o gerou. O conjunto não deve ser aberto até esse vínculo ser imposto pelo código congelado e um novo manifesto pré-abertura ser revisado.

## Evidências que passaram

- `protocol_r007.json` contém exatamente 12 IDs e 12 tuplas físicas únicas. Todas têm `fill > 0`; as formas `0,1,2,3,4` estão presentes; os fills são `20,25,30,35,55,85,90,95`; há cinco cenas com obstáculo, cinco com dropout e duas com ambos. A comparação das tuplas `(fill, shape, cx, obstacle, dropout)` deu interseção zero com as nove cenas de D003 e com as nove de D004.
- O candidato coincide com o braço candidato D004 nas cinco origens e orientações: quatro diagonais internas em `(0.1225/0.1775, 0.1225/0.1775, 0.40)` e o centro `(0.15, 0.15, 0.40)`, todos com yaw/tilt/roll zero. Somente as sequências mudam para `701–705`.
- O contrato exige `12 × 5 = 60` frames novos, cinco por cena, somente sequências `701–705`, e proíbe reutilização de desenvolvimento. O capturador não aceita frames de entrada: ele chama o binário congelado 60 vezes, grava com modo exclusivo `xb` e a verificação de pristine impede uma segunda captura após qualquer frame parcial.
- O gate implementado em `aggregate_gate` só passa quando há exatamente 12 registros, 12 totais elegíveis e 12 cenas dentro de 5%. Resultado parcial ou inelegível não passa. Erro espacial e razão de cancelamento são calculados e reportados sem alterar o gate primário.
- O executor de aquisição não importa estimador, geometria ou truth. No scorer, as 12 reconstruções são concluídas por `reconstruct_all` antes da chamada de `evaluate_with_truth`; o único import de `experiments.truth` está dentro dessa função avaliadora.
- O scorer exige `independent-score-release.json` ligado aos hashes do manifesto e da validação de aquisição antes de reconstruir. Ele recusa se `results/`, `validation.json` ou `REPORT.md` já existirem; a criação de `results/` também usa `exist_ok=False` e os arquivos de resultados usam criação exclusiva onde aplicável.
- O manifesto pré-abertura contém 21 arquivos congelados e todos os 21 SHA-256 recalculados coincidem. O checksum destacado do protocolo também coincide. Hash do próprio manifesto: `95e34ff295f0d6561fb85713f6bd93d6f693eff6963ec68f05ec06e500a490bd`.

Hashes centrais conferidos:

| Artefato | SHA-256 |
| --- | --- |
| protocolo R007 | `a13c3f04135f8105736f29c213b57108412ca3b74bc3681ac0b6d3a32a6d7e31` |
| estimador D003 | `bdc14436bf06d54ca2d43bc90da40a937817a39d6f5779fd5627817663b0df83` |
| executor de aquisição | `4cfdcc90f02831bcc7b7a5b72348522c0eb8053568a8c1ec547f1d89063b3ccd` |
| scorer/avaliador R007 | `7ab979b007a42506f4df9d9246d0b028b8151cf8f977b2beb48aaabe9e2fbb38` |
| truth/evaluador exato | `fb88a8e3db2e9e57b9c813ce05c7a63d021985db28e158571194fa331e9ab351` |
| geometria runtime | `35a8c563ba5ba5047d29eedc3bd4cf6e14353fb40e8e34b19aee987df8854b0b` |
| simulador fonte | `32239a94172bee8570f4f26a23c7373fffc3587abd62b6e2a429bc68612f6270` |
| simulador binário | `865f3e1a84e8278d5f31ce8d13b1449ab372433b510b81a575f30e6988cf6e7e` |
| requisito de volume | `8736ded54a596250fee40fd9fc5f059d4b5e108ca6bb4bc5a61dabb22c8a6b52` |

- Não existem `frames/`, `results/`, `capture-commands.json`, `acquisition-manifest.json`, `acquisition-validation.json`, `validation.json`, `REPORT.md`, `independent-pre-open-release.json` ou `independent-score-release.json` em `.ai/runs/m001-r007/`. A busca pelos IDs das cenas fora dos arquivos R007 congelados não encontrou frames, resultados ou pontuações prévias.
- `python .ai/experiments/m001/test_r007.py`: 9/9 testes passaram.
- `python .ai/experiments/m001/run_r007.py verify-preopen`: passou, confirmou 21 arquivos congelados e o hash do manifesto acima.

O comando documentado `python -m unittest .ai/experiments/m001/test_r007.py` não é portátil neste Windows: o loader retornou `ValueError: Empty module name` por causa do caminho iniciado por `.ai/`. A execução direta do mesmo arquivo passou. Isso deve ser corrigido na documentação, mas não é o motivo principal do bloqueio.

## Achado bloqueante: frames não estão ligados à cena de aquisição

Durante a captura, cada entrada de `capture-commands.json` registra `scene_id`, sequência, vetor de comando, `stdout_sha256` e `stdout_path`, o que seria suficiente para provar a origem. Porém `validate_acquisition()` não valida esses campos. Ele verifica apenas:

1. que a lista possui 60 entradas;
2. que o hash do arquivo de comandos coincide com o hash declarado no manifesto de aquisição;
3. que cada arquivo no caminho esperado possui envelope, CRC, pose e sequência válidos;
4. que o hash de cada arquivo coincide com o valor corrente de `candidate_frames`.

O cabeçalho BFLD validado não contém `fill`, `shape`, `cx`, obstáculo, dropout ou ID da cena. Portanto, depois de abrir R007 e observar os frames, é possível permutar arquivos com a mesma sequência entre diretórios de cenas, atualizar `candidate_frames`, reescrever coerentemente `capture-commands.json` e seu hash, e produzir uma nova `acquisition-validation.json` com `passed=true`. A checagem `scene_table_unchanged` verifica apenas que o protocolo ainda tem 12 cenas. O scorer posterior confere o conjunto de caminhos e os hashes correntes, mas também não compara cada frame com `scene_id`, comando, `stdout_path` e `stdout_sha256` originais. Assim, ele pontuaria um frame relabelado contra a truth da cena de destino.

Esse caminho permite seleção/reclassificação pós-abertura e quebra a afirmação de que a matriz fixa de 12 cenas foi adquirida e preservada sem seleção. O fato de a captura normal produzir o mapeamento correto não basta, porque os artefatos de aquisição ainda não têm vínculo independente quando podem ser reescritos.

## Condição para nova revisão

Antes de qualquer release, o código congelado deve validar, para cada uma das 60 combinações `(scene_id, sequence)`, o comando exato derivado do protocolo, `stdout_path`, `stdout_sha256`, pose/sequência e o hash do arquivo correspondente; deve também rejeitar entradas duplicadas, ausentes, extras ou fora de ordem contratual. O scorer deve exigir essa validação vinculada. Como isso altera arquivos congelados, será necessário recalcular o manifesto pré-abertura e submetê-lo a nova revisão. Ainda não existem frames R007, portanto o reparo pode ser feito sem consumir o holdout.

Nenhum arquivo de release foi criado por esta revisão.
