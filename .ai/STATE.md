CURRENT_RUN: m001
CURRENT_PHASE: R007_PREREGISTRATION_BEFORE_OPENING

ACTIVE_HYPOTHESES:
- Meta empresarial: erro relativo absoluto do volume TOTAL <=0.05; resultado parcial nunca passa.
- D004 confirmou no desenvolvimento simulado que quatro diagonais internas + centro, z=0.40 m, podem produzir 400/400 e erro total ≤5% nas nove cenas conhecidas.
- R007 deve testar generalização sem alterar candidato, estimador, executor, avaliador ou gate após abertura.
- Erro espacial e cancelamento continuam riscos materiais mesmo se o volume total passar.

COMPLETED_TASKS:
- Auditoria do plano anexado concluída em .ai/PLAN_GAP_AUDIT.md; trabalho existente foi reutilizado.
- Ensaio anterior de montagem 35/40/45/50 cm recuperado; D002 suspensa antes de capturas para não repetir essa varredura.
- R005/R006 concluídas: cinco variantes tiveram 2/9 totais <=5%, 2/9 totais >5% e 5/9 parciais; R007 preservada.
- D001 reprovada: fixed3 9/9 parciais; aimed 1 total <=5%, 1 acima e 7 parciais; prisma baixo por cancelamento.
- D003 implementada e congelada; 36 quadros existentes reutilizados, 8/8 testes e 48/48 hashes verificados. Resultado: 0/9 totais, 9/9 parciais; candidato não promovido.
- Arbitragem Astra atribuiu a parcialidade dominante ao casco dos retornos e definiu uma única D004 pareada com cinco vistas, sem repetir altura.
- `ITofSensor` e `SimTofSensor` implementados; `BOXFLOW_SIM=0` falha explicitamente até existir backend físico.
- Firmware ESP32 compilado com Arduino CLI 1.2.0/Arduino-ESP32 3.3.0: 1.066.159 bytes de programa e 48.684 bytes globais.
- Suíte completa: 26/26 testes aprovados; testes D003: 8/8.
- Duas tentativas no editor Wokwi falharam antes da simulação por conectividade e HTTP 524 da fila remota.
- D004 pré-registrada, adquirida e pontuada: 36 capturas novas; candidato 9/9 total e 9/9 ≤5%; controle 7/9 total e 4/9 ≤5%.
- Auditoria pós-score D004: 120/120 hashes, 18/18 reconstruções reproduzidas e métricas recalculadas; PASS aceito somente como desenvolvimento simulado.

PENDING_TASKS:
- Congelar e revisar protocolo, aquisição, scorer e avaliador R007 antes de gerar qualquer quadro reservado.
- Após liberação independente, executar R007 uma única vez, sem seleção de cenas nem ajuste pós-abertura.
- Executar ESP32 emulado → chip customizado → gateway → HTTP → dashboard. Wokwi CLI 0.26.1 está instalada, mas `WOKWI_CLI_TOKEN` não está definido; o editor remoto falhou na compilação.
- Implementar backend VL53L5CX físico, calibração e ensaio de hardware.
- R007 permanece reservada até existir candidato que passe os gates de desenvolvimento.

FAILED_OR_BLOCKED_TASKS:
- Wokwi browser: uma tentativa falhou por rede/resolução; outra recebeu HTTP 524 por tempo de compilação.
- Wokwi CLI: não executável sem `WOKWI_CLI_TOKEN`.
- Hardware físico: não disponível/testado.
- Arbitragem Astra D004: execução real falhou por limite de uso do provedor; nenhum parecer foi atribuído.

NEXT_ACTION: concluir e revisar o pré-registro R007 antes de abrir as 12 cenas novas; executar uma única vez com o candidato D004 congelado. Em paralelo, preservar o firmware compilado e não declarar integração Wokwi ou hardware completa.
