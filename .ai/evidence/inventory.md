# Inventário reaproveitado — 13/09/2026

Inspeção documental, sem reexecutar experimentos da aplicação. Números abaixo são resultados publicados no pacote, classificados como SIMULADO; não são novas medições.

| Recurso existente | Uso na reavaliação |
| --- | --- |
| [Resumo consolidado dos testes anteriores](../../BoxFlow_Resumo_Testes_Resultados_Antes_Orquestracao.md) | Consolidação já disponível, adicionada ao inventário sem reproduzir seus testes; documento observado após o snapshot inicial |
| [README da aplicação](../../README.md) | Arquitetura implementada, limitações e comandos históricos |
| [Experimentos de 64 zonas](../../docs/EXPERIMENTOS_64_ZONAS.md) | E0–E4, controles, resultados negativos, hardware e Wokwi pendentes |
| [Protocolo fixado](../../experiments/protocol.json) | Posições, alturas reservadas, gates e métricas; preservar limites históricos |
| [Resultados de comparação](../../build/experiments/comparison.json) | Cenas, máscaras, volumes, erros e ajustes já produzidos |
| [Vazio e deriva](../../build/experiments/measured-zero.json) | Ensaios existentes de desvio comum e deriva |
| [Hashes dos artefatos](../../build/experiments/artifact-hashes.json) | Conferir integridade antes de reutilização técnica |
| [Código de experimentos](../../experiments/run_comparison.py) e [ground truth](../../experiments/truth.py) | Extensão incremental, sem copiar o simulador |
| [Geometria](../../server/geometry.py) e [estimadores](../../experiments/estimators.py) | Identificar os limites entre medição e reconstrução |
| [Custom Chip](../../wokwi/boxflow-lidar.chip.c), [diagrama](../../wokwi/diagram.json), [configuração](../../wokwi/wokwi.toml) | Integração existente; não comprova execução completa no Wokwi |
| [Testes históricos](../../docs/TESTES.md) e [teste de experimentos](../../experiments/test_experiments.py) | Evidência funcional anterior, distinta de precisão física |

Resultados de referência já documentados: TIN com amplitude de erro de 16,11 pp na varredura principal; ajuste piramidal com amplitude de 0,98 pp na mesma família e 2,32 pp nos casos reservados. Isso é identificação condicionada à forma em simulação ideal, não validação geral de pilhas.

A cadeia completa ESP32 → mock → HTTP no Wokwi está documentada como pendente. Servo e múltiplas vistas não foram implementados na etapa E6. Não duplicar E0–E4 apenas para preencher novas rodadas.

As recomendações definitivas de documentos históricos devem ser lidas à luz da orientação atual: sensor, mecanismo e arquitetura estão abertos à reavaliação. Esses documentos foram preservados.
