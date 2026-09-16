# R005 — contrato corrigido e equivalência preservada

Status: concluída localmente, após limitação do provedor interromper o agente Sol. Nenhuma aprovação independente de código é atribuída à chamada interrompida.

O módulo `r005_estimator.py` não importa truth ou avaliadores. Para cada célula/vista, expõe todos os triângulos que efetivamente contribuem: altura, índices, maior aresta 3D e área projetada. A altura e a qualidade são médias sobre o mesmo conjunto de contribuições. Qualidade geométrica permanece um indicador diagnóstico, sem calibração de incerteza.

O contrato comum valida configuração inclusive com entrada vazia. Quadros malformados são registrados com índice original; vistas indisponíveis ficam disponíveis para auditoria, mas não entram na fusão. Nenhum total é selecionado se houver quadro inválido, vista indisponível ou célula sem suporte. Volumes parciais continuam separados dos totais.

A mediana convencional preservou exatamente alturas/estados em 225 quadros e alturas, seleção de total e volumes nos 72 braços históricos. Onze testes passaram, incluindo CRC, truncamento, quadro inválido entre válidos, referência NaN, entrada vazia e pontos abaixo da referência. As perturbações de teste foram aplicadas em memória; nenhum quadro histórico foi modificado.

O controle fatorial mediana usual/inferior × com/sem aparagem κ=2 foi executado com aquisição aimed fixa em R006. A nova qualidade usa a média de arestas do conjunto contribuinte, portanto variantes com aparagem são novas variantes diagnósticas; não se sobrescrevem nem se declaram equivalentes às versões antigas que usavam a qualidade mínima de um triângulo.

Evidência: [validação](validation.json), [resultados R006](../m001-r006/results/results.json), [integridade histórica](../m001-r005-r006/integrity.json).
