# Arbitragem da avaliação para próximas rodadas

User pede avaliar resultados para começar próximas rodadas. Houve leitura de código local, auditoria computacional de 27 frames existentes e duas revisões reais: Sol via subagente com acesso aos arquivos e Opus via runner textual.

Dados verificados:
- P003 versus fixed3: aquisição+fusão, 7/9 ganhos, mediana 0,795 pp; versus mediana da MESMA aquisição: 7/9, mediana 0,860 pp, regressão máxima 3,213 pp. Ambos falham gate antigo.
- P004 alterou trimming E mediana: statistics.median torna-se mediana inferior. Em 8/9 cenas nenhum descarte; apenas prism descarta 8 células.
- Controle 2x2 na aquisição aimed: prism tem efeito assinado -1,863060 pp só pela mediana inferior e +0,338551 pp pela aparagem adicional. Aparar mantendo mediana convencional piora erro em +0,169276 pp. Nas cenas de rampa/viga/dropout todo efeito é da mediana inferior.
- P004 versus mediana da mesma aquisição: 5 ganhos volumétricos locais e 4 empates, mediana 0,045431 pp. Contra fixed3 continua 6/9 e 0,181 pp; o gate não muda.
- Common_all: dropout 45/400 células e 16,30% do volume; prism 132/400 e 76%; layer_beam 168/400 e 42%.
- Erro principal é abs(soma residual de volume)/volume verdadeiro no domínio; permite cancelamento. Em pyramid_beam, mediana inferior reduz erro líquido, mas soma de erros absolutos por célula normalizada sobe 25,3517% -> 25,9389%.
- Qualidade = mínimo da maior aresta dos triângulos que contribuem numa célula/vista; altura = média das alturas desses triângulos. Não é média global da vista.
- P003/P004 total=all(heights!=None), P001 também considera invalid/unavailable. Históricos usados são válidos; risco futuro não altera reprovações atuais.
- Audit preservou SHA256 dos quatro resultados, verificou hashes de 27 quadros, reproduziu mediana P001 e valores P004. Nenhuma captura foi refeita.

Sol confirmou os fatos, pede corrigir contrato qualidade-altura, validar falhas, atribuir efeito por fator e publicar cobertura+erro espacial. Opus concorda em retirar confirmação de trimming e definir critério MVP antes de candidato/holdout. Porém Opus também introduziu inferências NÃO aceitas pelo orquestrador local: limiar de 0,1 pp sem evidência numérica; 'média global de vista' embora código faça média local por célula; equivalência entre medianas agregadas provar que aquisição não importa. Não endossar esses pontos. Pequenos ganhos determinísticos podem ser calculados; relevância prática continua indefinida.

Plano recomendado:
R005: saneamento do contrato e controle 2x2 diagnóstico, mantendo protocolo antigo/artefatos intactos. Contrato de retorno uniforme para frames inválidos; pares qualidade-altura coerentes; separar módulos de estimativa e truth; repetir apenas verificações afetadas por mudanças.
R006: diagnóstico por célula de descontinuidades, sombras, FoV, densidade e interpolação; verdade só no avaliador; sem ranking de novos kappa. A hipótese nova virá da localização dos erros, não de ajustar às medianas.
R007: critério MVP explícito; UM candidato congelado; avaliação primária única em cenas reservadas com famílias novas e combinações paramétricas inéditas. Versões antigas são controles, não candidatos selecionados pelo holdout. Reportar volume, erro espacial, cobertura e abstenções; vazio em litros e relativo indefinido. Gates passados são experimentais, não requisito do produto.

Entregue decisão concisa (máximo 450 palavras): correção da interpretação anterior, o que manter, prioridade e saída exigida de cada próxima rodada. Não pedir aprovação do usuário para diagnóstico local já autorizado, nem tratar fixed3 como vencedor físico. Não executar novos experimentos.
