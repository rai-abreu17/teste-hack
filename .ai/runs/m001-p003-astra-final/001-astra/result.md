Escolho **`trimmed3_kappa2` como P-004**. Tem maior valor informativo: testa se excluir apenas vistas muito menos compactas preserva ganhos sem as regressões da seleção dura. A mistura 50/50 testa sobretudo amortecimento, e sua previsão depende da linearidade da métrica.

- **Parâmetros fixos:** em cada ponto, manter vistas com aresta local ≤2× a mínima e aplicar mediana inferior. Sem ajuste posterior.
- **Controles:** reutilizar frames e manter aquisição, TIN, domínio e demais condições de P-003.
- **Previsões:** regressões de prisma/rampa ≤2 pp e retenção de ≥50% de cada um dos três maiores ganhos. São hipóteses, não resultados; a melhora mediana ≥1 pp permanece incerta.
- **Decisão:** aplicar integralmente o gate congelado, incluindo suporte, total e domínio. Apenas zerar regressões não basta para aprovação.

As nove cenas correlacionadas e o simulador ideal limitam a generalização.
