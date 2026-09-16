# M-001 — decisão de parada após P-004

**Nota de revisão:** a interpretação causal abaixo foi substituída pela [reavaliação](m001-evaluation-next-rounds.md). A reprovação numérica permanece. P-004 alterou aparagem e agregador; o diagnóstico mostrou ausência de aparagem em 8/9 cenas. Preserva-se este texto como histórico, sem endossar sua afirmação de mecanismo confirmado.

P-003 testou seleção dura pela vista com triângulo local mais compacto. Venceu 7/9 cenas, preservou suporte, mas foi reprovado por melhora mediana de 0,795 pp e regressões acima de 3 pp no prisma e na rampa.

Após revisões reais de Claude Opus 5 e GPT-5.6 Sol, o GPT-6 Astra escolheu P-004: aparar vistas com compactness superior a 2× a mínima e aplicar mediana inferior. O protocolo foi congelado antes da execução.

P-004 confirmou as previsões mecanísticas: conteve as regressões em até 0,503 pp e preservou pelo menos metade dos três maiores ganhos de P-003. Mesmo assim, foi reprovado: melhora mediana de 0,181 pp e 6/9 vitórias. Suporte de 96%, total 4/9 e domínio 9/9 passaram.

Decisão Astra: encerrar ajustes de fusão destinados à promoção nessas nove cenas e manter `fixed3` como referência operacional. A linha só deve reabrir com hipótese independente e novas cenas de avaliação congeladas antes dos resultados. Isso não prova que `fixed3` seja globalmente ótimo nem valida hardware.
