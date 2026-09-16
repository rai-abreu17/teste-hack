# Reavaliação de resultados e preparação das próximas rodadas

Esta avaliação substitui a interpretação causal de P-004 na decisão de parada. Preserva os resultados numéricos e as reprovações históricas. Nenhuma arquitetura foi aprovada em hardware. `fixed3` permanece controle experimental; não constitui solução validada ou alteração implantada na aplicação.

A direção R-005–R-007 foi confirmada pela [arbitragem real GPT-6 Astra](../runs/m001-evaluation-astra/001-astra/result.md), após revisão real do Sol com leitura do workspace e revisão textual do Opus. As especulações do Opus sobre um limiar de 0,1 pp e média global de vista foram rejeitadas: não havia evidência para o limiar e o código calcula média local por célula.

## Evidência nova, obtida dos artefatos existentes

O diagnóstico [audit_rounds.py](../experiments/m001/audit_rounds.py) reutiliza 27 quadros, reproduz a mediana P-001 e os erros P-004, verifica hashes e não modifica os resultados anteriores. A saída [attribution.json](../runs/m001-evaluation/results/attribution.json) contém a decomposição por cena e a proveniência. É análise posterior dos dados de desenvolvimento, não nova validação.

1. **P-004 alterou dois fatores:** descartou vistas por compactness e trocou mediana convencional pela mediana inferior. Para duas alturas `a,b`, a convencional retorna `(a+b)/2`; a inferior retorna `min(a,b)`. Esta troca reduz alturas independentemente da qualidade geométrica.
2. **Em 8/9 cenas não houve descarte.** Somente o prisma teve descarte, em oito células. Rampa, viga e dropout melhoraram devido à mediana inferior. Portanto, retirar a afirmação de que o mecanismo de aparagem foi confirmado.
3. **No prisma, a aparagem isolada piorou o erro.** Com a mesma aquisição, trocar apenas mediana convencional por inferior reduz erro assinado em 1,863 pp; acrescentar a aparagem eleva o erro em 0,339 pp. Mantendo mediana convencional, aparar eleva em 0,169 pp. O ganho líquido P-004 nessa cena não prova utilidade da aparagem.
4. **A comparação contra `fixed3` inclui aquisição e fusão.** Para isolar fusão, comparar também contra `translated3_aimed` com mediana. Por exemplo, no dropout, o ganho P-004 é 6,426 pp contra fixed3, mas apenas 1,903 pp contra mediana com a mesma aquisição.
5. **O domínio de avaliação pode ser pequeno.** No dropout são 45/400 células (11,25% da área), contendo 16,30% do volume verdadeiro. No prisma, 132/400 células contêm 76% do volume; em layer_beam, 168/400 contêm 42%. A máscara comum é útil para comparar localmente, mas não demonstra solução do volume total nem cobertura do box inteiro.
6. **Erro volumétrico líquido permite cancelamento espacial.** Na pirâmide deslocada, fixed3 tem erro absoluto de volume de 1,623%, mas soma de erros absolutos por célula normalizada pelo mesmo volume de 23,689%. Essas métricas respondem a perguntas distintas; publicar ambas.

## O que continua válido

- Translação pode recuperar linhas de visada no modelo ideal; isso não garante amostragem suficiente ou volume mais preciso.
- Rotação pura no mesmo centro não altera oclusão intrínseca; ainda pode mudar enquadramento e amostragem.
- Repetições fixas são iguais sem dropout; diferentes sequências recuperam retornos no dropout simulado.
- P-002/P-003/P-004 não passaram seus gates experimentais. Esses gates foram propostos no processo de pesquisa e não são requisitos de precisão do produto.
- Nenhuma regra testada aumentou a seleção de total além de 4/9. Seleção de total significa suporte TIN completo sob o contrato do modelo, não acurácia garantida.

## Próximas rodadas, em ordem

### R-005 — saneamento e atribuição (preparada; diagnóstico inicial executado)

Objetivo: tornar as comparações interpretáveis antes de procurar outro candidato.

- Manter o controle fatorial: mediana convencional/inferior × com/sem aparagem. Não selecionar κ a partir dessas nove cenas.
- Uniformizar rejeição de quadros inválidos, vistas indisponíveis e referência inválida entre os estimadores. Hoje P-003/P-004 usam apenas existência de altura para selecionar total; P-001 também valida estado de quadros/vistas.
- Associar qualidade à altura efetivamente agregada. Atualmente a menor aresta vem de um triângulo, mas a altura escolhida pode ser a média de vários triângulos da vista.
- Separar módulos de fusão e avaliação. Os helpers atuais estão em arquivos que importam truth no nível do módulo, embora não recebam truth nas funções de fusão. Isso não comprova vazamento histórico, mas dificulta garantir a separação futura.
- Conferir integridade das entradas, cardinalidade e hashes antes de processar novos dados. Corrigir cobertura de testes de falhas; os sete testes antigos não validam todos os contratos novos.

Saída exigida: relatório de equivalência nas entradas válidas e rejeição consistente nas entradas defeituosas. Nenhuma hipótese de desempenho será promovida nessa etapa.

### R-006 — localizar o erro por célula (proposta, não executada)

Hipótese diagnóstica: parte do erro provém de triângulos que cruzam transições de superfície e de regiões sem amostragem suficiente. Ainda não está demonstrada a causa dominante.

- Reusar os quadros existentes e manter aquisição/estimador fixos.
- Registrar, por célula e vista, alturas, triângulos contribuintes, arestas, área projetada, quantidade de retornos e discordância entre vistas.
- No avaliador apenas, separar células planas, transições, sombra de viga e regiões sem suporte; calcular erro espacial e parcela do erro de volume de cada grupo. Não usar rótulos verdadeiros para escolher vistas.
- Distinguir LoS ideal, alcance angular do sensor, retornos discretos e suporte interpolado. Os três primeiros não são equivalentes ao último.
- Fazer comparações separadas: aquisição com fusão fixa; fusão com aquisição fixa. `fixed3` continua como controle de custo igual.

Critério falsificável: a hipótese perde sustentação se a concentração de erro nas regiões de transição/sombra não exceder o esperado pela área e volume dessas regiões, ou se o erro planar dominar. Documentar a alternativa encontrada antes de escolher um novo mecanismo.

### R-007 — avaliação reservada (proposta, não executada)

- Selecionar um único candidato após R-006; congelar código, parâmetros, máscaras, métricas e regras de falha antes de abrir a avaliação reservada.
- Separar desenvolvimento e avaliação por geometria, não apenas por sequência. Novas alturas/centros nas mesmas cinco formas testam generalização paramétrica; não equivalem a novas famílias. Incluir superfícies não usadas na escolha do candidato, cuja referência possa ser integrada independentemente.
- Cobrir vazio, camadas, assimetrias, alturas diversas, transições, oclusão e dropout. Poses/cenas devem respeitar limites reais do simulador, sem contar entradas sanitizadas para a mesma geometria como casos diferentes.
- Relatar erro de volume total quando elegível, erro e volume no domínio comum, erro espacial, cobertura, abstenções e custo de aquisição. Não descartar silenciosamente cenas sem domínio completo. Vazio usa erro absoluto em litros, com erro relativo indefinido.
- Agregar por família e por condição de oclusão; não tratar várias pirâmides correlacionadas como replicações físicas independentes.
- Definir critério MVP em erro absoluto, cobertura e latência conforme o uso demonstrado. Preservar gates históricos, mas não inventar uma nova precisão industrial ou relaxar o gate depois de ver os resultados.

Se o candidato falhar, o conjunto reservado passa a desenvolvimento e não pode ser reutilizado para declarar validação de uma variante ajustada.

## Direção recomendada

Abrir R-005 e R-006 com os dados existentes; depois decidir entre melhorar reconstrução ou mudar aquisição. Não há evidência suficiente para comprar mais sensores, recomendar outra tecnologia ou promover compactness. Teste físico, quando disponível, deve comparar de modo pareado a referência e o candidato, com volume de referência independente.
