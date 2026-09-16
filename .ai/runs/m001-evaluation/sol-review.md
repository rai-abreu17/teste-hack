# Revisão independente real — síntese

Executor: subagente `/root/evaluate_rounds`, GPT-5.6 Sol, reasoning high, iniciado via ferramenta de colaboração. Leitura real do workspace, sem alterações nem novas capturas. Este arquivo sintetiza a resposta recebida, não é uma transcrição integral.

- Confirmou atribuição confundida: comparação contra fixed3 mistura aquisição e fusão. P003 versus mediana da mesma aquisição: 7/9, ganho mediano aproximadamente 0,860 pp e regressão máxima 3,213 pp.
- Confirmou ausência de aparagem em 8/9 cenas P004. No prisma, mediana inferior reduz erro assinado em 1,863 pp, mas trimming posterior aumenta em 0,339 pp.
- Confirmou cancelamento: pyramid_beam melhora volume líquido, porém erro espacial normalizado aumenta de 25,35% para 25,94%.
- Qualidade mínima de um triângulo não caracteriza necessariamente a altura média entre todos os triângulos que contribuem naquela célula/vista.
- Total P003/P004 diverge do contrato P001 e falta tratamento/indexação robusta para quadros inválidos; não há evidência de quadros inválidos históricos.
- Confirmou máscaras parciais, especialmente dropout: 45/400 células, 16,3% do volume.
- Recomenda saneamento de contratos, controle por fator com aquisição fixa, métricas espaciais/volumétricas/cobertura separadas e só depois avaliação reservada.
