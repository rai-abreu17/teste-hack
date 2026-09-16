# M-001 — revisão independente dos resultados P-001

Objetivo: determinar se múltiplas vistas resolvem os pontos cegos na simulação BoxFlow e qual configuração merece o próximo teste físico.

Leia estes artefatos existentes no workspace; não altere arquivos:

- protocolo congelado: `.ai/experiments/m001/protocol.json` e `protocol.sha256`
- implementação: `.ai/experiments/m001/m001_estimator.py`, `run_p001.py`, `scene_dump_m001.c`
- resultados completos: `.ai/runs/m001-implementation/results/comparisons.json`
- tabela: `.ai/runs/m001-implementation/results/comparisons.csv`
- resumo: `.ai/runs/m001-implementation/results/summary.md`
- log real: `.ai/runs/m001-implementation/command-log.json`
- decisão prévia: `.ai/decisions/m001-protocol-decision.md`
- análises cegas e críticas: `.ai/runs/m001-opus-blind/001-investigator/result.md`, `.ai/runs/m001-sol-blind/001-engineer/result.md`, `.ai/runs/m001-opus-cross/001-investigator/result.md`, `.ai/runs/m001-sol-cross/001-engineer/result.md`
- pesquisa: `.ai/runs/m001-sonnet-research/001-researcher/result.md`

Fatos de execução: compilação C com `-Wall -Wextra -Werror`, 7/7 testes passaram, 72/72 comparações produzidas. O harness Windows precisou de stdout binário para impedir expansão CRLF dos quadros.

Restrições de interpretação:

- `suporte TIN` é suporte da interpolação local, não área fisicamente observada.
- o oráculo testa linha de visada intrínseca até centros verdadeiros e ignora FoV/orientação; é somente avaliador.
- cada vista gera sua própria TIN; a fusão usa mediana por célula e nunca cria triângulos entre vistas.
- métricas `common_group` e `common_all` comparam braços no mesmo domínio suportado.
- o simulador é pinhole ideal; não modela resposta finita de zonas, histogramas, distorção óptica, ruído real ou calibração.
- não trate uma mediana de nove cenas como prova de hardware.

Resumo das medianas (9 cenas):

| braço | raios | total válido | bins | suporte TIN | visibilidade oráculo | erro domínio próprio | erro comum grupo |
|---|---:|---:|---:|---:|---:|---:|---:|
| baseline_fixed1 | 64 | 4/9 | 16.0% | 84.0% | 94.5% | +4.08% | +4.08% |
| fixed3 | 192 | 4/9 | 16.0% | 84.0% | 94.5% | +4.08% | +4.08% |
| center_tilt3 | 192 | 4/9 | 30.0% | 88.0% | 94.5% | +8.40% | +9.73% |
| translated3_level | 192 | 4/9 | 30.0% | 96.5% | 100.0% | +7.88% | +9.46% |
| translated3_aimed | 192 | 4/9 | 25.5% | 96.0% | 100.0% | +8.07% | +5.78% |
| fixed4 | 256 | 4/9 | 16.0% | 84.0% | 94.5% | +4.08% | +3.97% |
| center_angles4 | 256 | 0/9 | 37.0% | 74.5% | 94.5% | +4.71% | +4.21% |
| translated4_corners_level | 256 | 0/9 | 28.5% | 49.0% | 100.0% | +3.63% | +2.47% |

Entregue: (1) auditoria metodológica/código, (2) interpretação causal sustentada por dados por cena, (3) hipóteses confirmadas/refutadas/inconclusivas, (4) recomendação concreta e falsificável do próximo passo, (5) limitações. Cite caminhos e campos/linhas usados. Não invente medições.
