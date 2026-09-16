# Implementação P-001

Este diretório recebe apenas binários, logs e resultados novos da rodada P-001. O protocolo e o código-fonte experimental ficam em `.ai/experiments/m001/`.

Execução a partir da raiz do workspace:

```powershell
python .ai/experiments/m001/execute.py
```

O executor compila os dois harnesses, roda os testes dirigidos e, se todos passarem, executa as 72 comparações. Todos os comandos de alto nível, códigos de saída, stdout e stderr são gravados em `command-log.json`; cada captura e consulta do oráculo é registrada em `results/capture-commands.json`.
