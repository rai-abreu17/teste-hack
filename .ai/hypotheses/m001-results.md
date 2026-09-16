# M-001 — estado das hipóteses após P-001/P-002

- **H-002, parcial:** inclinação redistribui a amostragem, mas não remove oclusão intrínseca.
- **H-003/H-005, parcial:** centros transladados chegaram a 100% de LoS ideal e até 96% de suporte TIN mediano; a melhora de volume foi inconsistente.
- **H-004, refutada para rotação pura:** girar no mesmo centro não recuperou LoS bloqueada.
- **H-006, parcial:** repetição fixa foi idempotente sem dropout e recuperou suporte com dropout simulado; fusão multivista ainda não venceu consistentemente.
- **Aresta TIN de 0,07 m, refutada:** P-002 preservou o domínio original em 4/9 cenas e reduziu total válido para 2/9.
- **Compactness como substituta da mediana, refutada:** P-003 venceu 7/9, mas excedeu o limite de regressão.
- **Compactness como triagem, não sustentada pela atribuição atual:** P-004 não aparou vistas em 8/9 cenas. No único caso ativo, prisma, a aparagem piorou o erro frente ao controle com o mesmo agregador. A melhora veio da mediana inferior e/ou aquisição; retirada a confirmação mecanística anterior. Gate histórico continua reprovado.
- **Triangulação conjunta D003, refutada como solução total:** recuperou lacunas internas e reduziu erro espacial em 8/9 cenas, mas ficou parcial em 9/9. O casco dos retornos aceitos cobre 196/400 células nas formas localizadas e 324/400 nas camadas; prisma e rampa ainda erram 45,71% e 40,33% no domínio próprio.
- **Aquisição D004 com diagonais internas, confirmada no desenvolvimento simulado:** com centro comum e D003 congelado, produziu 9/9 totais e 9/9 erros líquidos ≤5%. Ainda há erro espacial de 21,135% no prisma, 18,859% na rampa e cancelamento extremo em duas pilhas; exige R007 reservada e validação física.

Reavaliação vigente: [atribuição causal e próximas rodadas](../decisions/m001-evaluation-next-rounds.md).

Todos os estados são SIMULATED. Hardware permanece inconclusivo.
