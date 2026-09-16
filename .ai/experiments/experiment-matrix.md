# Matriz de experimentos

E0–E6 preservam os identificadores do [relatório existente](../../docs/EXPERIMENTOS_64_ZONAS.md). P-001–P-004 são experimentos posteriores; a reavaliação causal está em [decisão vigente](../decisions/m001-evaluation-next-rounds.md).

| ID | Hipótese | Configuração | Mudança | Métrica | Resultado | Status |
| --- | --- | --- | --- | --- | --- | --- |
| E0 | H-001 | 8×8, 21 posições, pirâmide 7,5 cm | Baseline existente | Erro assinado, amplitude, estado | SIMULADO: mediana 5,20%; amplitude 16,11 pp; 21/21 valid | CONFIRMADO PARCIALMENTE para esse cenário |
| E1 | H-007 | Recortes 6×6 e 4×4 existentes | Seleção de região | Erro no mesmo domínio, área, volume retido | SIMULADO: 6×6 não reduz amplitude; 4×4 conserva só 16% da área; não valida total | REFUTADO como correção do total neste ensaio |
| E2 | H-007 | Gates 35°, 45°, 55° existentes | Filtro por inclinação | Erro e cobertura | SIMULADO: 45° piorou erro; 55° não mudou a varredura principal | REFUTADO como melhoria geral neste ensaio |
| E3 | H-007 | Ajuste piramidal, principal e reservados | Prior geométrico declarado | Erro, amplitude, rejeições | SIMULADO: amplitude 0,98 pp principal e 2,32 pp reservados; condicionado à família | CONFIRMADO PARCIALMENTE |
| E4 | H-010 | Oito vazios; desvios comuns e posteriores | Referência medida no mock | Erro, deriva, cobertura | SIMULADO: cancela desvio vertical comum; não elimina interpolação nem deriva | CONFIRMADO PARCIALMENTE |
| E5 | Integração | ESP32 → Custom Chip → HTTP | Execução Wokwi completa | Integridade ponta a ponta e referência | Relatório anterior registra execução completa pendente | NÃO TESTADO integralmente |
| E6 | H-003/H-004/H-005/H-008 | Movimento e múltiplas vistas | Aquisição alternativa | Cobertura/oclusão/erro/tempo | Não implementado na etapa anterior | NÃO TESTADO |
| P-001 | H-002 a H-006 | 9 cenas × 8 braços | Poses repetidas, giradas e transladadas | Domínios comuns, suporte TIN, LoS ideal, total | SIMULADO: 72 comparações; aimed vence erro absoluto 5/9 contra fixed3; total 4/9 | Sem vencedor |
| P-002 | Limite TIN | 9 cenas × 2 braços × 2 limites | Aresta 0,10/0,07 m | Erro e preservação do domínio | SIMULADO: candidato retém domínio 4/9 e total 2/9; melhora mediana 0,419 pp só nos pares completos | Reprovado |
| P-003 | Seleção por compactness | Mesmos quadros aimed | Mediana/seleção dura | Erro comum, suporte e total | SIMULADO: contra fixed3, ganho 0,795 pp e piora máxima 3,891 pp; contra mediana aimed, 0,860 pp e piora 3,213 pp | Reprovado |
| P-004 | Aparagem e agregador | Mesmos quadros aimed | κ=2 e mediana inferior | Erro comum, suporte e total | SIMULADO: 0,181 pp e 6/9 contra fixed3; sem aparagem em 8/9 cenas | Reprovado; confirmação causal retirada |
| R-005 diagnóstico | Atribuição P-004 | 27 quadros existentes, controle 2×2 | Mediana usual/inferior × com/sem trim | Efeito isolado, erro espacial e domínio | CALCULADO sobre simulação: ganhos sem aparagem; no prisma, aparar piora; históricos preservados | Diagnóstico concluído; saneamento pendente |
| R-005 execução | Contratos e qualidade-altura | 225 quadros/72 braços históricos | Módulo instrumentado sem truth | Equivalência e rejeição de entradas inválidas | 11 testes; mediana convencional idêntica; qualidade/altura coerentes | Concluído |
| R-006 | Localização do erro | 54 quadros, 45 comparações, 18000 células | Diagnóstico por transição/sombra/FoV | Erro espacial, cobertura e volume total | SIMULADO: todas5variantes 2/9 dentro5%,2 acima,5parciais; erro concentrado em transições | Concluído, sem promoção |
| R006-C | Suficiência da faixa de transição | Resultados R006 | Substituição ideal apenas avaliador | Residual fora da faixa com suporte fixo | CALCULADO: center ~3%; ramp5,09–5,15%; lacunas mantidas | Contrafactual, não estimador |
| D001 | Reconstrução por planos | 54 quadros existentes; 36 comparações | Patches com ≥4 vértices, resíduo ≤2 mm e casco explicitamente modelo; aquisição fixa | Total ≤5%, erro espacial, cobertura e suporte de modelo | SIMULADO: fixed3 9 parciais; aimed prisma1,55% por cancelamento, rampa12,59%,7 parciais;9 testes | Reprovado; R005 mantido e R007 não iniciada |
| D003 | Triangulação conjunta K4 | 36 quadros existentes, 4 vistas/cena | Pool de XYZ, merge conservador e uma Delaunay sem extrapolação | Total ≤5%, erro espacial, casco e suporte | SIMULADO: 0/9 totais, 9 parciais; suporte 196/400 ou 324/400; prisma45,71% e rampa40,33% no domínio próprio | Reprovado; ganhos internos diagnósticos |

Cada novo resultado deve indicar CALCULADO, SIMULADO ou MEDIDO EM HARDWARE. Ground truth fica no avaliador. Volume vazio usa erro absoluto; rejeições e lacunas permanecem no relatório. Um novo critério percentual precisa de justificativa experimental.
