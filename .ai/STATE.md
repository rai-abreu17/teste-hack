CURRENT_RUN: m001
CURRENT_PHASE: D004_PREREGISTRATION_AND_ACQUISITION

ACTIVE_HYPOTHESES:
- Meta empresarial: erro relativo absoluto do volume TOTAL <=0.05; resultado parcial nunca passa.
- D004 testa se reposicionar em XY quatro vistas diagonais, com centro comum e z=0.40 m, amplia o casco até 400/400 sem mudar o estimador D003.
- Mesmo que D004 complete a cobertura, prisma/rampa podem continuar bloqueados por erro de reconstrução.

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

PENDING_TASKS:
- Congelar e revisar D004 antes de pontuar; gerar apenas as 36 novas capturas diagonais previstas e reutilizar K4/centro existentes.
- Executar a comparação D004 com estimador D003 congelado; exigir 9/9 totais <=5% para preparar validação reservada.
- Executar ESP32 emulado → chip customizado → gateway → HTTP → dashboard. Wokwi CLI 0.26.1 está instalada, mas `WOKWI_CLI_TOKEN` não está definido; o editor remoto falhou na compilação.
- Implementar backend VL53L5CX físico, calibração e ensaio de hardware.
- R007 permanece reservada até existir candidato que passe os gates de desenvolvimento.

FAILED_OR_BLOCKED_TASKS:
- Wokwi browser: uma tentativa falhou por rede/resolução; outra recebeu HTTP 524 por tempo de compilação.
- Wokwi CLI: não executável sem `WOKWI_CLI_TOKEN`.
- Hardware físico: não disponível/testado.

NEXT_ACTION: concluir pré-registro e revisão independente da D004, depois pontuar sem ajustes pós-resultado. Em paralelo, preservar o firmware compilado e não declarar integração Wokwi completa.
