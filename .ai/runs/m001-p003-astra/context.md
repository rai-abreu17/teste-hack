# Arbitragem P-003

P-003 foi corretamente REPROVADO: seleção dura pela menor aresta local venceu 7/9, mas melhora mediana foi 0,795 pp (<1) e regressões foram 3,891 pp no prisma e 3,224 pp na rampa (>2). Suporte 96%, total 4/9 e domínio 9/9 passaram. Aquisição/TIN/domínio ficaram fixos e a mediana reproduziu P-001 exatamente.

Opus 5 interpreta compactness como sinal que confunde obliquidade/alcance, relevo verdadeiro e pontes em descontinuidades. Recomenda `trimmed3_kappa2`: manter vistas com aresta <=2× a mínima e aplicar mediana inferior; prevê conter regressões e preservar >=50% dos três maiores ganhos. Observou que o gate mediano >=1 pp exige converter prism/ramp em ganho >=1 pp ou elevar shifted acima de 1 pp; zerar regressões não basta.

Sol recomenda fusão convexa fixa `0.5*mediana + 0.5*seleção compacta`. Vantagem: menor mudança e, se a métrica for integração linear seguida de erro absoluto, contém as regressões de prisma/rampa abaixo de 2 pp e preserva direção dos 7 ganhos. Admite que o gate completo provavelmente continuará falhando na mediana.

Ambas usam apenas informação do estimador, sem truth, e reutilizam frames. Limitação comum: nove cenas correlacionadas e simulador ideal.

Escolha uma única próxima ablação. Priorize valor informativo, isolamento causal e protocolo simples. Determine parâmetros antes da execução, previsões e mantenha o gate já congelado. Responda de forma curta; não invente resultados.
