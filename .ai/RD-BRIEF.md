Você é responsável por configurar uma equipe multiagente de Pesquisa & Desenvolvimento para o projeto BoxFlow.

Esta equipe NÃO deve partir de uma solução previamente considerada correta.

O objetivo é investigar, experimentar, discutir alternativas, construir protótipos, testar hipóteses e chegar a uma arquitetura tecnicamente defensável para o MVP, deixando explícito o caminho de evolução para uma solução real/industrial.

# 1. Princípio central

O BoxFlow atualmente possui uma TEORIA DE SOLUÇÃO, não uma solução definitivamente validada.

Existem:

* hipóteses;
* ideias promissoras;
* limitações conhecidas;
* pontos cegos ainda não resolvidos;
* sensores candidatos;
* algoritmos candidatos;
* mecanismos físicos candidatos;
* uma simulação/protótipo de MVP.

Nenhum desses elementos deve ser tratado automaticamente como decisão definitiva.

Os agentes devem assumir uma postura de P&D:

PESQUISAR
→ FORMULAR HIPÓTESES
→ DEBATER
→ MODELAR
→ IMPLEMENTAR EXPERIMENTOS
→ TESTAR
→ MEDIR
→ TENTAR REFUTAR
→ COMPARAR
→ DECIDIR

Nunca:

IDEIA
→ "PARECE BOA"
→ CONSIDERAR FUNCIONANDO

# 2. Contexto do BoxFlow

O BoxFlow busca estimar o volume/ocupação de material armazenado em boxes.

O sistema precisa obter informações suficientes sobre a superfície do material para estimar seu volume e acompanhar sua evolução.

Entretanto, a arquitetura física definitiva AINDA NÃO ESTÁ FECHADA.

Questões em aberto incluem, entre outras:

* qual sensor é mais adequado;
* quantos sensores seriam necessários;
* qual posicionamento utilizar;
* quais regiões ficam invisíveis;
* como reduzir pontos cegos;
* se um sensor fixo é suficiente;
* se deve existir movimentação;
* que tipo de movimentação;
* qual frequência de aquisição;
* como reconstruir uma superfície usando medições incompletas;
* qual margem de erro é aceitável;
* como diferenciar um MVP de baixo custo de uma futura versão industrial;
* quais características precisam ser demonstradas no hackathon;
* quais características podem ficar como evolução tecnológica.

# 3. MVP NÃO É A SOLUÇÃO INDUSTRIAL

Esta distinção é obrigatória durante toda a investigação.

Existem duas arquiteturas conceitualmente diferentes.

## Arquitetura A — MVP / demonstração

Objetivo:

provar que o princípio do BoxFlow é tecnicamente plausível.

Restrições:

* baixo custo;
* desenvolvimento rápido;
* hackathon;
* maquete reduzida;
* hardware acessível;
* simulação;
* possibilidade de sensor ToF multizona;
* possibilidade de ESP32;
* possibilidade de Wokwi;
* não precisa atingir precisão industrial;
* precisa produzir resultados mensuráveis e demonstráveis.

Um sensor ToF 8×8, como o VL53L5CX, é atualmente um CANDIDATO FORTE para este MVP.

Ele NÃO deve ser tratado como sensor definitivo do BoxFlow.

## Arquitetura B — solução futura / industrial

Objetivo:

mostrar que o princípio demonstrado pelo MVP pode evoluir para uma arquitetura adequada a boxes reais.

Podem ser considerados:

* LiDAR;
* LiDAR 2D;
* LiDAR 3D;
* múltiplos sensores;
* sensores em posições diferentes;
* mecanismos móveis;
* fusão de sensores;
* outras tecnologias identificadas pela pesquisa.

Os agentes devem investigar essas possibilidades.

Não assumam automaticamente que LiDAR é a solução final.

Comparem tecnicamente.

# 4. Pergunta principal da equipe

A equipe deve responder:

"Qual é a forma mais tecnicamente defensável de demonstrar no MVP que o BoxFlow consegue estimar o volume de material dentro de um box, utilizando hardware acessível, mesmo existindo pontos cegos e limitações de sensor?"

E também:

"Como essa arquitetura pode evoluir posteriormente para uma implementação de maior precisão e escala industrial?"

# 5. Problema específico dos pontos cegos

Este deve ser um dos principais tópicos da investigação.

Um único sensor pode não visualizar toda a superfície.

Os agentes devem discutir alternativas, sem assumir antecipadamente qual será vencedora.

Entre as hipóteses que PODEM ser investigadas:

### Hipótese A

Sensor totalmente fixo.

### Hipótese B

Sensor inclinado.

### Hipótese C

Dois ou mais sensores fixos.

### Hipótese D

Sensor montado em mecanismo rotacional.

Por exemplo:

* servo;
* stepper;
* mecanismo pan;
* mecanismo pan/tilt.

### Hipótese E

Sensor deslocando-se linearmente.

### Hipótese F

Combinação de movimentação e múltiplas aquisições.

### Hipótese G

Reconstrução computacional das regiões não observadas.

### Hipótese H

Combinação de reconstrução computacional com movimentação física.

### Hipótese I

Outra solução descoberta durante pesquisa.

Essa lista NÃO limita as alternativas.

Os agentes são incentivados a propor arquiteturas diferentes.

# 6. Não buscar perfeição

O objetivo do MVP NÃO é obter 100% da geometria real.

A equipe deve procurar uma margem de erro:

* mensurável;
* repetível;
* explicável;
* defensável para uma demonstração de MVP.

Não determine arbitrariamente uma porcentagem aceitável.

Os agentes devem experimentar e produzir dados.

Por exemplo:

ERRO DE VOLUME =
|V_estimado - V_real| / V_real × 100

Outras métricas podem ser propostas.

A equipe deve responder:

* qual foi o erro;
* em qual cenário;
* utilizando qual configuração;
* utilizando quantas medições;
* utilizando qual algoritmo;
* quais regiões produziram maior erro;
* quais condições melhoraram ou pioraram o resultado.

# 7. Ciência antes de opinião

Nenhum agente deve afirmar:

"isso funciona"

sem evidência.

Utilizar quatro classificações:

HIPÓTESE

EVIDÊNCIA

RESULTADO EXPERIMENTAL

CONCLUSÃO

Exemplo proibido:

"Adicionar um servo resolve os pontos cegos."

Exemplo aceitável:

"Hipótese: movimentar o sensor entre cinco ângulos pode aumentar a superfície observada.

Foi construído o experimento X.

Com sensor fixo foram observadas Y regiões.

Com cinco posições foram observadas Z regiões.

O erro volumétrico passou de A para B.

Portanto, neste cenário específico, a movimentação reduziu o erro."

# 8. Pesquisa obrigatória

Antes de propor uma solução baseada em características físicas ou eletrônicas, pesquisar.

Prioridade:

1. datasheets;
2. documentação STMicroelectronics;
3. documentação Espressif;
4. documentação Wokwi;
5. documentação das bibliotecas;
6. papers;
7. artigos técnicos;
8. implementações públicas;
9. fóruns apenas como evidência secundária.

Ferramentas disponíveis:

* Firecrawl;
* Context7;
* Playwright.

Pesquisas podem incluir:

* ToF multizona;
* VL53L5CX;
* FoV;
* resolução espacial;
* distância;
* frequência;
* interferência;
* reflectância;
* iluminação;
* multi-target;
* crosstalk;
* calibração;
* movimentação do sensor;
* reconstrução 3D;
* point clouds;
* surface reconstruction;
* volume estimation;
* LiDAR;
* sensores utilizados em silos;
* sensores utilizados em depósitos;
* sensores utilizados em bulk material measurement.

Toda informação relevante deve guardar sua fonte.

# 9. Trabalho independente primeiro

Para reduzir viés de confirmação:

Claude e Codex NÃO devem começar debatendo imediatamente.

Primeiro:

CLAUDE OPUS
→ produz análise independente.

CODEX
→ produz análise independente.

Eles não recebem inicialmente a conclusão um do outro.

Cada um deve responder:

* qual problema estamos realmente tentando resolver;
* quais restrições existem;
* quais tecnologias devem ser investigadas;
* quais hipóteses considera promissoras;
* quais considera improváveis;
* quais dados faltam;
* quais experimentos devem ser realizados.

# 10. Debate técnico

Depois das análises independentes, começa o debate.

Claude recebe a análise do Codex.

Codex recebe a análise do Claude.

Cada agente deve procurar:

* hipóteses frágeis;
* assumptions sem fonte;
* impossibilidades físicas;
* erros matemáticos;
* limitações ignoradas;
* testes ausentes;
* alternativas não consideradas.

Eles NÃO devem tentar concordar.

Eles devem tentar melhorar a solução.

# 11. Rodadas de P&D

O debate pode gerar uma arquitetura experimental.

Exemplo:

RODADA 01

Sensor fixo.

Executar experimento.

Medir.

RODADA 02

Sensor em diferentes ângulos.

Executar experimento.

Medir.

RODADA 03

Sensor movimentado.

Executar experimento.

Medir.

RODADA 04

Duas vistas.

Executar experimento.

Medir.

RODADA 05

Reconstrução de regiões faltantes.

Executar experimento.

Medir.

A equipe deve decidir quais experimentos realmente fazem sentido.

Não execute experimentos inúteis apenas para preencher uma sequência.

# 12. Matriz de experimentos

Criar:

`.ai/experiments/experiment-matrix.md`

Com estrutura semelhante:

| ID | Hipótese | Configuração | Mudança | Métrica | Resultado | Status |
| -- | -------- | ------------ | ------- | ------- | --------- | ------ |

Status possíveis:

NÃO TESTADO

EM TESTE

CONFIRMADO PARCIALMENTE

REFUTADO

INCONCLUSIVO

PROMISSOR

# 13. Validação no simulador

Sempre que algo puder ser testado dentro do ambiente disponível, TESTE.

O ambiente deve ser inspecionado antes.

Podem existir:

* Wokwi;
* Wokwi CLI;
* ESP32;
* Custom Chips;
* código C/C++;
* diagram.json;
* wokwi.toml;
* scripts auxiliares;
* simulações matemáticas.

Os agentes devem utilizar esses recursos.

Não declarar sucesso apenas porque:

* código compilou;
* Wokwi iniciou;
* sensor respondeu;
* apareceu um número.

O resultado precisa ser comparado com uma referência conhecida.

# 14. Ground truth

Sempre que possível, cada cenário da maquete deve possuir um volume verdadeiro conhecido.

Por exemplo:

V_real

contra:

V_estimado

Isso permite determinar:

ERRO ABSOLUTO

ERRO RELATIVO

ERRO PERCENTUAL

Outras métricas podem ser adicionadas.

# 15. Cenários diferentes

Uma solução não deve ser avaliada somente no cenário mais fácil.

Criar cenários progressivos.

Por exemplo:

SUPERFÍCIE SIMPLES

SUPERFÍCIE INCLINADA

MATERIAL CONCENTRADO EM UM LADO

REGIÃO CENTRAL ELEVADA

REGIÕES COM POSSÍVEL OCLUSÃO

SUPERFÍCIE IRREGULAR

Os agentes devem definir os cenários adequados para o MVP.

# 16. Resultado negativo é válido

Uma das regras mais importantes:

Se uma ideia não funcionar, registre.

Não tente esconder.

Exemplo:

"Uma única visão apresentou erro elevado nesse tipo de superfície."

Isso é um resultado útil.

Pode justificar:

* movimentação;
* segundo sensor;
* algoritmo diferente;
* evolução para LiDAR.

# 17. Construção da narrativa tecnológica

Ao final, o sistema deve permitir explicar tecnicamente:

"MVP"

Usamos X porque:

* é acessível;
* atende à escala da maquete;
* permite demonstrar o princípio.

Limitações encontradas:

* A;
* B;
* C.

Mitigações utilizadas:

* D;
* E;
* F.

Resultados experimentais:

* cenário 1 → erro X;
* cenário 2 → erro Y;
* cenário 3 → erro Z.

Depois:

"ESCALA REAL"

Para implantação real, essas limitações tornam desejável avaliar:

* tecnologia X;
* tecnologia Y;
* múltiplas vistas;
* LiDAR;
* outra arquitetura.

Não afirmar que a arquitetura industrial está definida se não estiver.

# 18. Agentes

Configure quatro papéis.

## AGENTE A — ORQUESTRADOR

Modelo preferencial OpenAI mais capaz disponível para agentic reasoning.

Responsabilidade:

* decompor problemas;
* convocar agentes;
* organizar rodadas;
* verificar se existem evidências;
* identificar discordâncias;
* exigir testes;
* decidir quando continuar pesquisando;
* consolidar resultados.

Não deve impor sua própria solução antes das investigações.

## AGENTE B — CLAUDE INVESTIGADOR

Modelo preferencial:

Claude Opus 5.

Responsabilidade:

* pesquisa profunda;
* engenharia;
* física;
* sensores;
* arquiteturas;
* crítica técnica.

## AGENTE C — CODEX ENGINEER

Modelo preferencial:

GPT-5.6 Sol ou melhor modelo de coding disponível e apropriado.

Responsabilidade:

* implementação;
* simulação;
* experimentos;
* scripts;
* análise matemática;
* testes;
* revisão da arquitetura.

## AGENTE D — CLAUDE RESEARCHER

Modelo preferencial:

Claude Sonnet 5.

Responsabilidade:

* pesquisa direcionada;
* coleta de documentação;
* levantamento de tecnologias;
* organização de fontes;
* verificações auxiliares.

# 19. Escalonamento de modelos

Não utilizar o modelo mais caro indiscriminadamente.

Sonnet pode realizar tarefas mecânicas e pesquisas direcionadas.

Opus deve ser reservado para raciocínio técnico profundo.

Modelos OpenAI mais fortes devem ser utilizados para:

* arbitragem;
* arquitetura;
* problemas de engenharia difíceis.

# 20. Estrutura de arquivos

Criar:

.ai/

agents/
research/
hypotheses/
experiments/
evidence/
debates/
reviews/
decisions/
runs/

E:

STATE.md
README.md
problem.md
hypothesis-register.md
experiment-matrix.md
decision-log.md

# 21. Registro de hipóteses

Criar:

`.ai/hypothesis-register.md`

Cada hipótese deve possuir:

ID

DESCRIÇÃO

ORIGEM

JUSTIFICATIVA

EVIDÊNCIAS FAVORÁVEIS

EVIDÊNCIAS CONTRÁRIAS

EXPERIMENTO NECESSÁRIO

STATUS

# 22. Ciclo de decisão

O sistema deve seguir:

PROBLEMA
↓
PESQUISA
↓
HIPÓTESES
↓
DEBATE
↓
EXPERIMENTO
↓
RESULTADO
↓
CRÍTICA
↓
NOVAS HIPÓTESES
↓
NOVO EXPERIMENTO

até existir evidência suficiente para uma decisão.

# 23. Critério de parada

O sistema NÃO deve entrar em debate infinito.

Uma questão pode ser considerada suficientemente respondida quando:

* existem dados;
* experimentos são reproduzíveis;
* principais alternativas foram comparadas;
* limitações são conhecidas;
* existe uma solução adequada ao MVP;
* riscos restantes estão documentados.

"Incerteza residual" é aceitável.

O objetivo não é provar matematicamente que não existe solução melhor.

# 24. Verdade acima de demonstração

Nunca manipule resultados para fazer o BoxFlow parecer melhor.

Nunca descarte um experimento porque ficou ruim.

Nunca invente resultados.

Nunca transforme simulação em evidência de hardware real sem deixar explícita essa distinção.

Sempre diferenciar:

SIMULADO

CALCULADO

MEDIDO EM HARDWARE

ESTIMADO

INFERIDO

FONTE EXTERNA

# 25. Objetivo imediato

Neste momento, configure essa infraestrutura de agentes.

Depois da configuração, a PRIMEIRA missão real da equipe deverá ser:

"Reavaliar tecnicamente a arquitetura atual do MVP do BoxFlow, tratando o sensor ToF multizona como candidato e não como decisão definitiva.

Investigar especificamente como obter cobertura suficiente da superfície da maquete para estimativa volumétrica, considerando pontos cegos, oclusões, posicionamento, quantidade de sensores, movimentação física do sensor, múltiplas aquisições e reconstrução computacional.

Pesquisar alternativas, construir experimentos no ambiente existente e produzir resultados quantitativos.

Comparar também o MVP de baixo custo com possíveis arquiteturas futuras de maior escala, incluindo LiDAR quando tecnicamente relevante."

# 26. Regra final

O objetivo desta equipe não é defender a ideia atual.

O objetivo é descobrir:

O QUE FUNCIONA.

O QUE NÃO FUNCIONA.

POR QUE FUNCIONA.

POR QUE NÃO FUNCIONA.

QUAL O ERRO.

QUAL O LIMITE.

O QUE PRECISA MUDAR.

E QUAL É A MELHOR ARQUITETURA QUE CONSEGUIMOS DEFENDER COM AS EVIDÊNCIAS DISPONÍVEIS.
