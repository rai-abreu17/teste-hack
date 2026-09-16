**Decisão: (c) encerrar esta linha de ablações de fusão e manter `fixed3`.** Isso encerra a tentativa de promoção com a evidência atual; não demonstra que `fixed3` seja globalmente ótimo.

**Resultado simulado informado, não reexecutado aqui:** P-004 preservou a integridade do protocolo e passou nas previsões mecanísticas, mas foi reprovado pelo gate congelado: melhora mediana de 0,181 pp e 6/9 vitórias foram insuficientes. A regressão máxima caiu para 0,503 pp.

**Inferência:** a intervenção conseguiu conter as regressões de P-003, mas não preservou ganho suficiente para aprovação. Isso sustenta a explicação mecanística de P-004, não sua promoção. Os ganhos expressivos em poucas cenas também não substituem os critérios gerais. Como essas nove cenas já orientaram decisões sucessivas, outra escolha de fusão baseada nos mesmos deltas aumentaria o risco de adaptação ao conjunto. Não há, no contexto fornecido, uma hipótese adicional suficientemente independente para justificar outra ablação.

**Ação concreta e critério de parada:**

- Registrar P-004 como reprovado e conservar `fixed3` como referência operacional.
- Encerrar ajustes de fusão destinados à promoção nessas nove cenas, incluindo qualquer varredura de κ.
- Reabrir a linha somente com uma hipótese nova, sustentada por evidência além desses deltas, e avaliação em cenas independentes. Antes de observar seus resultados, congelar um único candidato, protocolo e gate; se falhar, não reajustá-lo usando o mesmo conjunto de avaliação.

Mudar aquisição/geometria permanece uma possibilidade de pesquisa, mas os dados apresentados não identificam qual mudança testar nem demonstram que esse seja o gargalo.
