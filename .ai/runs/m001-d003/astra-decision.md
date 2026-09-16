# Arbitragem técnica Astra — M001-D003

Data: 2026-09-16. Escopo: decisão baseada nos artefatos existentes; nenhuma captura, alteração de estimador ou nova pontuação executada nesta arbitragem.

## Decisão

**Não promover D003. Manter R007 reservada e R005 como controle experimental.** O critério empresarial continua sendo erro relativo absoluto do **volume total <=5%**. Um resultado parcial nunca passa, mesmo quando seu erro no domínio suportado é pequeno ou a verdade do simulador informa que as células ausentes estão vazias.

Os nove candidatos em `results/results.json` têm `total_selection.selected=false`, `whole_box=null` e `company_5pct_total_only=null`. São **0/9 totais elegíveis e 9/9 parciais**. Não existe ambiguidade a ser resolvida por votação entre revisores. O `passed=true` de `validation.json` atesta a validação da execução; o mesmo arquivo registra `all_nine_gate_passed=false` e não autoriza aprovação empresarial.

## Evidências determinantes

| Evidência | Consequência |
| --- | --- |
| Sete cenas D003 suportam 196/400 células; as duas camadas suportam 324/400. | Faltam 204 ou 76 células para totalidade. |
| Nas cinco formas localizadas sem viga, 144 pontos aceitos delimitam XY aproximadamente `[0,037800; 0,262200] m`. | O casco contém somente 14 × 14 centros da grade de 20 × 20. |
| Nas camadas, os extremos são aproximadamente `[0,015810; 0,284190] m`. | O casco contém somente 18 × 18 centros; a primeira e a última linha/coluna continuam ausentes. |
| Nas cenas com viga/dropout, D003 recupera 24, 36 e 45 células frente ao controle. | A triangulação entre vistas recupera suporte interno, mas termina no mesmo perímetro das cenas correspondentes sem obstáculo. |
| Na camada, o volume verdadeiro não suportado é 0,0012825 m³ = 1,2825 L = 19% do total. | O erro líquido próprio de 0,181% não demonstra precisão do volume total. |
| Prisma: +45,713% líquido e 45,801% espacial; rampa: +40,331% líquido e 40,716% espacial, nos domínios próprios. | Há um segundo bloqueio de reconstrução, além da ausência de bordas. |

As máscaras e pontos de `results/details.json` confirmam o diagnóstico antes da aplicação da verdade. As quatro poses decodificadas usam x/y de 0,10 ou 0,20 m, z de 0,40 m e rotação zero. Não há quadros inválidos, vistas indisponíveis, conflitos de merge, pontos omitidos em `coplanar` ou erro Qhull. A revisão Sol registra 48/48 hashes conferidos; `validation.json` registra 8/8 testes, 36 quadros reutilizados e nenhuma captura nova. Esta arbitragem leu os resultados e detalhes, mas não repetiu testes nem a auditoria de hashes.

**Causa dominante da ausência de totalidade: o casco dos retornos aceitos da aquisição K4 não alcança os centros periféricos da grade.** A combinação de posição lateral, projeção dos centros de zona e rejeição de retornos em paredes/exterior deixa uma borda sem amostras. A regra conservadora de não extrapolar torna essa insuficiência explícita. Um FoV nominal maior que a base não garante que os retornos discretos aceitos sustentem seus 400 centros.

Não há evidência de que elevar o sensor resolva isso: `docs/MONTAGEM_30CM.md` já registra o ensaio 35/40/45/50 cm, incluindo suporte de 81% para pirâmide e 49% para camada a 50 cm. D002 permanece suspensa. Também não cabe preencher a borda com zero usando conhecimento da cena. No prisma e na rampa, completar apenas a região ausente sem mudar as alturas atuais preservaria o excesso já medido; uma nova aquisição poderá mudar a triangulação, mas seu benefício precisa ser medido.

Os ganhos de D003 são diagnósticos: erro espacial menor em 8/9 cenas e recuperação de lacunas internas. Eles não demonstram visibilidade direta em cada célula interpolada. As razões de cancelamento de 8,29, 20,77 e 11,45 nas pirâmides central, com viga e com dropout também impedem interpretar erro líquido baixo como fidelidade espacial.

## Único próximo experimento proposto: D004 — reposicionamento XY com cinco vistas e altura fixa

**Hipótese falsificável:** a fase espacial dos raios periféricos, e não apenas o número de vistas, explica parte importante da borda perdida. Reposicionar as quatro vistas diagonais para mais perto do centro, mantendo uma quinta vista central comum, deve ampliar o casco aceito na camada sem perder o suporte periférico disponível no piso.

Registrar e congelar este protocolo antes de capturar ou pontuar:

1. **Dois braços, cinco vistas cada, mesma reconstrução D003 congelada.** Controle: K4 original `(0,10; 0,10)`, `(0,20; 0,10)`, `(0,10; 0,20)`, `(0,20; 0,20)` m, mais centro `(0,15; 0,15)`. Candidato: `(0,1225; 0,1225)`, `(0,1775; 0,1225)`, `(0,1225; 0,1775)`, `(0,1775; 0,1775)` m, mais o mesmo centro. Todas as vistas em z=0,40 m, yaw/tilt/roll=0. A única diferença entre braços é o XY das quatro vistas diagonais.
2. **Justificativa geométrica anterior ao resultado:** no modelo de centros de zona documentado, o raio externo tem componente lateral `0,875 × tan(22,5°)`. Sobre um plano a 7,5 cm, seu deslocamento lateral ideal é aproximadamente 0,11779 m. As novas poses projetam os extremos em aproximadamente 0,00471 e 0,29529 m, envolvendo os centros periféricos 0,0075 e 0,2925 m. Isso é uma previsão geométrica para desenvolvimento, não garantia de retorno aceito, suporte TIN ou precisão. A vista central é comum aos braços porque o ensaio existente já mostra sua utilidade para piso/pilha a 40 cm.
3. **Dados e orçamento:** usar exatamente as nove cenas de desenvolvimento D003, sem selecionar vencedoras. Reutilizar os 36 quadros K4 e os nove quadros centrais de sequência 101 já arquivados em `baseline_fixed1`/`fixed3`, conferindo identidade e hashes. Gerar somente os 36 quadros das quatro novas poses. Associar as diagonais às sequências 201–204 na mesma ordem do protocolo P-001; manter todos os demais parâmetros de cena/dropout idênticos. Não usar R007. O centro deve ser o mesmo quadro binário nos dois braços.
4. **Congelamento:** preservar o estimador e os parâmetros D003, inclusive merge, limite de aresta, filtros e critérios de elegibilidade. Registrar hashes dos códigos, protocolo, cenas, quadros reutilizados e executável do simulador antes da execução. O protocolo deve identificar os dois braços como novas aquisições com cinco entradas; a D003 K4 original permanece intacta. Nenhuma busca de poses ou ajuste de tolerância após observar resultados.
5. **Desfecho primário de cobertura:** candidato com 400/400 células e todos os demais critérios de total elegível em 9/9 cenas. Publicar também a diferença pareada de suporte, células ganhas/perdidas, casco XY, retornos rejeitados e conflitos. Separar células fora do casco das células dentro dele rejeitadas pelo estimador: envolver o domínio é necessário, mas não suficiente.
6. **Gate empresarial separado:** calcular erro de volume total somente para totais elegíveis. Exigir 9/9 totais com erro relativo absoluto <=5% para considerar o candidato apto a preparar validação reservada. Qualquer parcial ou cena acima de 5% reprova esse gate. Reportar erro espacial e cancelamento nos domínios próprio/comum, além de contagem de quadros e tempo descritivo. Ganhar cobertura sem passar volume será evidência diagnóstica, nunca aprovação.

Esta é uma única comparação de aquisição com orçamento igual e estimador fixo; não é varredura de altura nem teste simultâneo de um novo reconstrutor. As coordenadas foram escolhidas com conhecimento das cenas de desenvolvimento, portanto nem um eventual 9/9 substituirá validação independente ou ensaio físico.

**Próximo passo concreto:** o engenheiro Sol deve materializar `protocol_d004.json` e um executor de comparação pareada com os dois braços acima; revisão independente deve conferir isolamento da verdade, reuso dos quadros e congelamento antes da execução. Esta decisão propõe o experimento e não declara que ele foi executado ou aprovado.

## Relação com o plano do MVP

O plano original trata também de chip, abstração do sensor e demonstração ESP32/rede/dashboard. `.ai/REPORT.md` e `.ai/STATE.md` registram essas pendências e a suspensão da D002; ainda não incorporavam D003 na versão lida. A decisão aqui é restrita à linha volumétrica e não dá essas entregas por concluídas. Todos os resultados permanecem simulados, sem evidência de precisão do hardware.

Fontes locais principais: `REPORT.md`, `results/results.json`, `results/details.json`, `sol-review.md`, `validation.json`, `.ai/ORCHESTRATION.md`, `.ai/REPORT.md`, `.ai/STATE.md`, `plano-chip-tof-wokwi-boxflow.md` e `docs/MONTAGEM_30CM.md`. Para fixar a proposta foram lidos também `.ai/experiments/m001/protocol.json`, `protocol_d003.json` e `tools/check_mounting.py`.
