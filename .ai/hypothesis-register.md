# Registro de hipóteses

**Atualização M-001:** a tabela abaixo preserva a importação inicial. Para H-002–H-006 e compactness, prevalecem os [resultados posteriores](hypotheses/m001-results.md) e a [reavaliação causal](decisions/m001-evaluation-next-rounds.md). Não interpretar os estados históricos NÃO TESTADO como ausência dos ensaios P-001–P-004.

Origem comum: [briefing de P&D do usuário](RD-BRIEF.md). As evidências existentes abaixo são importadas do [inventário](evidence/inventory.md); não foram reexecutadas nesta configuração. Nenhuma linha equivale a validação industrial.

| ID | Descrição | Origem / justificativa | Evidências favoráveis | Evidências contrárias / limite | Experimento necessário | Status |
| --- | --- | --- | --- | --- | --- | --- |
| H-001 | Sensor fixo pode bastar para cenários restritos do MVP | Usuário; menor complexidade | E0 e E3 fornecem resultados ideais existentes | TIN varia com posição; camada pode ficar parcial; hardware não validado | Reusar E0/E3 e identificar cenário fora da família ainda não avaliado | CONFIRMADO PARCIALMENTE, apenas simulação documentada |
| H-002 | Inclinação pode melhorar a região observada | Usuário; redistribuir FoV | Pose/tilt já representados no mock | Não há comparação controlada apresentada para esta hipótese | Comparar posição fixa e inclinação, mesma cena e domínio | NÃO TESTADO |
| H-003 | Duas ou mais vistas fixas podem reduzir oclusão | Usuário; mudar centro óptico | Plausibilidade geométrica, sem resultado quantitativo do projeto | Calibração, registro e interferência não avaliados | Dois centros ópticos, ground truth e custo de aquisição equivalente | NÃO TESTADO |
| H-004 | Mecanismo rotacional pode ampliar enquadramento | Usuário; hipótese sensor+servo | Cálculo ideal distingue FoV de visibilidade | Rotação com centro óptico fixo não elimina o bloqueio do mesmo raio | Distinguir rotação pura de deslocamento introduzido pelo mecanismo | NÃO TESTADO no MVP |
| H-005 | Deslocamento linear pode oferecer vistas úteis | Usuário; paralaxe | Justificativa geométrica, ainda sem ensaio | Tempo, vibração e erro de pose desconhecidos | Trajetória curta com orçamento de capturas explícito | NÃO TESTADO |
| H-006 | Múltiplas aquisições podem melhorar estimativa | Usuário; combinar informação | Pipeline de quadros já existe | Repetir mock determinístico não cria evidência independente | Separar repetição no mesmo lugar de novas vistas; controlar tempo | NÃO TESTADO para fusão |
| H-007 | Reconstrução condicionada pode estimar regiões faltantes | Usuário e E3; explorar prior explícito | E3 reduz dispersão na família piramidal simulada | Família geradora coincide com prior; baixo resíduo não identifica forma | Reusar controles E3 e planejar apenas formas/oclusões faltantes | CONFIRMADO PARCIALMENTE, condicionado |
| H-008 | Movimento mais reconstrução pode superar cada técnica isolada | Usuário; combinação | Sem resultado combinado | E3/E4 e E6 não validam a combinação | Comparar componentes separados antes da combinação | NÃO TESTADO |
| H-009 | Outra tecnologia pode oferecer melhor compromisso | Usuário; evitar fechamento prematuro | Comparação ideal densa existe | Benchmark denso não identifica um produto industrial | Pesquisa direcionada e comparação por requisitos do ambiente | NÃO TESTADO |
| H-010 | Referência vazia pode mitigar desvio comum | E4 existente; calibração | Desvio vertical comum cancelou no ensaio ideal | Erro de interpolação e deriva posterior persistiram | Reusar E4; ensaio físico somente com hardware disponível | CONFIRMADO PARCIALMENTE, simulação |
