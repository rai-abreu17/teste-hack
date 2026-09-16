# Problema e primeira missão

O BoxFlow estima volume/ocupação em boxes. A arquitetura atual é uma teoria de solução e um protótipo; suas escolhas não constituem validação física. O VL53L5CX é candidato do MVP, e LiDAR é uma alternativa de evolução a investigar.

**Pergunta MVP:** qual arquitetura acessível demonstra estimativa volumétrica mensurável e repetível na maquete, com cobertura incompleta, oclusões e limitações conhecidas?

**Pergunta industrial:** quais mudanças de aquisição, sensor, montagem, calibração e reconstrução precisam ser avaliadas para boxes reais?

## Missão M-001 — iniciada após conclusão da arbitragem 009-astra

Reavaliar tecnicamente a arquitetura atual, pesquisando sensores candidatos, cobertura, posição, quantidade de sensores, rotação, translação, múltiplas aquisições e reconstrução. Comparar alternativas com ground truth e explicar o caminho para escala real. Não escolher antecipadamente sensor, mecanismo ou algoritmo.

Começar pelo [inventário existente](evidence/inventory.md). Aproveitar os resultados e protocolos já disponíveis; repetir apenas quando houver mudança, falha de integridade, lacuna concreta ou necessidade de reprodução registrada. A orientação explícita do usuário é não refazer o que já existe.

## Contrato de evidência

Cada afirmação deve distinguir HIPÓTESE, EVIDÊNCIA, RESULTADO EXPERIMENTAL e CONCLUSÃO. Acrescentar a origem: SIMULADO, CALCULADO, MEDIDO EM HARDWARE, ESTIMADO, INFERIDO ou FONTE EXTERNA.

Publicar volume verdadeiro, estimado, erro absoluto e erro relativo percentual para V_real > 0. Para vazio, publicar erro absoluto e indicar erro relativo indefinido. Informar cenário, configuração, algoritmo, quantidade de capturas, cobertura e regiões desconhecidas. Não comparar volume parcial com a verdade do box inteiro como se fosse estimativa total.

Não adotar um novo limite percentual arbitrário. A meta histórica de 5% e os gates de experimentos anteriores são contexto, não critérios automaticamente aprovados nesta missão.

O MVP pode admitir incerteza residual documentada. Uma decisão exige dados reproduzíveis, comparação das alternativas relevantes e limites explícitos; não exige debate infinito. Simulação ideal não equivale a ensaio do sensor físico.
