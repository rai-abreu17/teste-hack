# Execução R005/R006 frente à meta de 5%

Decisão confirmada pela [arbitragem real Astra](../runs/m001-r006-astra/001-astra/result.md): aceitar R005 como saneamento e R006/R006-C como diagnóstico; não declarar a meta atingida nem abrir R007 sem candidato.

## Entregas executadas

- R005: módulo instrumentado separado da verdade, contratos de validade uniformes, qualidade e altura associadas ao mesmo conjunto de triângulos. Onze testes aprovados. Equivalência exata dos resultados convencionais em 225 quadros e 72 braços existentes.
- R006: protocolo congelado, 54 quadros reutilizados, 45 comparações, 18.000 registros por célula, mapas SVG e seis testes do avaliador aprovados. Hashes e conservação de partições verificados.
- R006-C: contrafactual somente do avaliador, protocolo separado congelado antes do cálculo; nenhuma correção com verdade foi incorporada ao estimador.
- Nenhuma captura nova. Quarenta e sete artefatos históricos conferidos contra hashes anteriores, sem divergências.

## Resultado para a empresa

A [meta informada](../requirements/mvp-volume.md) foi interpretada como erro relativo absoluto de volume total de no máximo 5%. Em cada uma das cinco variantes diagnósticas, duas cenas atendem, duas excedem e cinco não produzem volume total. Não há aprovação geral do MVP.

No controle fixed3, os totais são: pirâmide central 17,499%; pirâmide deslocada 1,857%; duas pilhas 2,530%; rampa 10,808%. As cinco restantes são parciais. A aquisição transladada não muda a contagem de aprovação/abstenção.

## Evidência para a próxima decisão

A maior densidade de erro nas faixas de transição/sombra foi observada nas sete cenas com relevo, para ambas as aquisições. Trata-se de associação espacial, não identificação definitiva da causa. A banda contém também uma parcela importante do material, especialmente nas duas pilhas.

Camadas planas têm baixo erro local e grande lacuna de suporte: no caso sem viga, 256/400 células suportadas, deixando 2,43 L de referência fora do domínio. O FoV ideal e a amostragem discreta precisam ser considerados separadamente da reconstrução. Ausência de sombra comum da viga não garante suporte completo.

R006-C removeu somente o residual nas células verdadeiras de transição, mantendo todas as lacunas. A pirâmide central cairia para 2,895% (fixed3) e 3,099% (aimed); a rampa ainda ficaria em 5,146% e 5,089%, respectivamente. Isso não é desempenho de algoritmo e não permite usar verdade no estimador. Sob esse contrafactual específico, corrigir a faixa de 1,5 cm isoladamente é insuficiente para a rampa e não corrige cobertura.

## Prontidão R007

R007 de validação reservada **não foi aberta**: os resultados não selecionam um candidato capaz de atender à meta nas condições avaliadas. Abrir o conjunto reservado antes de definir candidato e escopo consumiria a independência desse conjunto sem uma comparação primária defensável.

Próximo desenvolvimento: reconstrução que trate mudanças de superfície com dados medidos, comparada com aquisição fixa; em paralelo conceitual, geometria de aquisição que amplie cobertura nas camadas, com reconstrução fixa. Não escolher outro κ nem usar os rótulos verdadeiros para seleção. A altura do sensor pode ser uma hipótese de footprint, mas ainda não foi ensaiada e pode reduzir densidade útil nas pilhas. O candidato só será congelado após esse desenvolvimento; então R007 avalia generalização em cenas reservadas.

A hipótese sugerida pela arbitragem é segmentar superfícies a partir das observações e restringir triângulos que cruzem descontinuidades detectadas, explicitando quais lacunas podem ser reconstruídas com suporte dos dados e quando abster-se. Trata-se de hipótese de desenvolvimento; parâmetros e protocolo ainda precisam ser definidos antes dos resultados. Uma nova regra não deve ser confundida com os filtros de gradiente históricos já testados.

## Limites de execução multiagente

As duas delegações iniciais Sol foram interrompidas pelo limite do provedor após produzir arquivos parciais; o orquestrador reutilizou e concluiu esses arquivos localmente. A interpretação Opus foi executada de fato em `m001-r006-opus`. Não atribuir aprovação de implementação às chamadas interrompidas.

Após a liberação do provedor, uma [revisão real Sol](../runs/m001-r005-r006/sol-review.md) foi concluída em uma nova execução do agente. Confirmou partições, cardinalidades, hashes, fronteira estimador/verdade e recalculou os 36 resultados por domínio do contrafactual. Seu veredito também foi que R007 ainda não está pronta.

As propostas de oráculo de amostragem/reconstrução do texto Opus não foram adotadas: não isolavam causalmente os estágios como descrito. Foi usado apenas o contrafactual algébrico explícito R006-C, com escopo limitado. Cenas parciais têm referência não nula, mas não têm estimativa total elegível; não se confundem com cenas vazias.

## Artefatos

- [Relatório R005](../runs/m001-r005/REPORT.md)
- [Relatório R006 e mapas](../runs/m001-r006/REPORT.md)
- [R006-C](../runs/m001-r006-counterfactual/results.json)
- [Integridade histórica](../runs/m001-r005-r006/integrity.json)
