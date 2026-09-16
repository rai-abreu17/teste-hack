# D004 — handoff antes da pontuação

Estado: aquisição simulada concluída e validada; reconstrução, suporte e volume ainda não calculados.

O protocolo pareado usa cinco entradas por braço em cada uma das nove cenas P001. O controle referencia os 36 quadros K4 arquivados e os nove quadros centrais `baseline_fixed1-1.bin`. O candidato usa 36 quadros novos nas diagonais internas e referencia exatamente os mesmos nove arquivos centrais. As cópias `fixed3-1.bin` foram conferidas como byte a byte idênticas aos centros selecionados.

Artefatos para revisão independente:

- `../../experiments/m001/protocol_d004.json` e `protocol_d004.sha256`: hipótese, poses, estimador D003 congelado, gates e limite de parada;
- `pre-acquisition-manifest.json`: fontes, executável e 45 quadros históricos registrados antes de qualquer captura candidata;
- `capture-commands.json`: os 36 comandos executados;
- `acquisition-manifest.json`: hashes e cabeçalhos dos 36 quadros novos;
- `acquisition-validation.json`: validação final de aquisição.

Não existe diretório `results` nesta rodada. A revisão deve liberar explicitamente uma fase posterior antes de qualquer chamada ao estimador ou à verdade de cena.
