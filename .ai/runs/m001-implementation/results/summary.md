# P-001 — resumo por braço

Métricas são medianas das nove cenas; `total ok` mostra seleções/9, sem ocultar parciais.

| braço | grupo | raios | total ok | bins efetivos | suporte TIN | visibilidade oráculo | erro próprio % | erro comum grupo % |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| baseline_fixed1 | K1_reference | 64 | 4/9 | 16.0% | 84.0% | 94.5% | +4.08 | +4.08 |
| fixed3 | K3 | 192 | 4/9 | 16.0% | 84.0% | 94.5% | +4.08 | +4.08 |
| center_tilt3 | K3 | 192 | 4/9 | 30.0% | 88.0% | 94.5% | +8.40 | +9.73 |
| translated3_level | K3 | 192 | 4/9 | 30.0% | 96.5% | 100.0% | +7.88 | +9.46 |
| translated3_aimed | K3 | 192 | 4/9 | 25.5% | 96.0% | 100.0% | +8.07 | +5.78 |
| fixed4 | K4 | 256 | 4/9 | 16.0% | 84.0% | 94.5% | +4.08 | +3.97 |
| center_angles4 | K4 | 256 | 0/9 | 37.0% | 74.5% | 94.5% | +4.71 | +4.21 |
| translated4_corners_level | K4 | 256 | 0/9 | 28.5% | 49.0% | 100.0% | +3.63 | +2.47 |

`bins efetivos` conta células que contêm pelo menos um retorno utilizável. `suporte TIN` é a união dos suportes interpolados locais por captura. `visibilidade oráculo` testa linha intrínseca e ignora FoV/orientação; não entra no estimador.
