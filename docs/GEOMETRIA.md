# Geometria v3 — maquete de 30 × 30 cm

Piso x/y de 0 a 0,30 m, paredes laterais e de fundo de 0,15 m, frente aberta em y=0. Sensor em (0,15; 0,15; 0,40) m, sem teto. Bases laterais de largura e altura de 0,01 m:

`b(x,y) = max(0; 0,01 − x; x − 0,29)`.

A viga ocupa x de 0,17 a 0,20 m, y de 0 a 0,30 m e z de 0,18 a 0,20 m. A máscara de retorno tem margem de 2 mm; a sombra não é preenchida.

## Zonas e ray-casting

64 zonas, representadas por raios centrais ideais. Campo nominal de 45° horizontal e vertical da tabela 2 do [datasheet da ST](https://www.st.com/resource/en/datasheet/vl53l5cx.pdf). Usa-se `q = tan(22,5°)`. A ST informa também 65° diagonal; os três ângulos nominais não são uma calibração pinhole exata. A versão de 60 cm derivava 48,50° por eixo da diagonal; esta revisão usa 45° por eixo.

`u = normalize(((2(c+0,5)/8−1)q; (2(r+0,5)/8−1)q; −1))`, para c/r entre 0 e 7.

O gerador busca a primeira interseção positiva por Möller–Trumbore contra a malha, e por raio–caixa contra a viga. A distância é arredondada para mm. A extensão real das zonas, múltiplos alvos, histogramas, distorção, refletância, luz e poeira não são simulados. Alcance é um corte induzido.

O receptor calcula `p = t + d Rz(yaw) Ry(tilt) u`, renormalizando as direções codificadas por 32767. Roll não é implementado. A ordem espacial das zonas do mock precisa ser calibrada para o hardware.

## Referências analíticas

`h = 0,10 × fill/100` m. As fórmulas estão somente nas ferramentas de avaliação.

| Forma | Volume de referência |
| --- | --- |
| Pirâmide, base 15 × 15 cm | 0,0225h/3 |
| Duas pirâmides, bases 10 × 10 cm, alturas h e 0,7h | 0,01(h+0,7h)/3 |
| Prisma, base 15 × 15 cm | 0,0225h |
| Rampa, base 15 × 15 cm | 0,0225h/2 |
| Camada sobre toda a referência vazia | 0,09h |

O receptor não recebe forma, `fill`, centro ou volume analítico da carga.

## Integração e lacunas

Excluem-se paredes/exterior com margem de 1 mm, viga e retornos inválidos. Pontos mais de 3 mm abaixo da referência tornam a medição indisponível. É um limite de desenvolvimento, não a precisão do hardware.

Calcula-se a altura relativa `z − b(x,y)` antes da interpolação baricêntrica. São dois triângulos por quadrilátero angular, com arestas 3D de no máximo 0,10 m. Faces verticais não sustentam área horizontal. A grade tem 20×20 células de lado 0,015 m e área 0,000225 m². Integra-se somente em centros suportados. Essa interpolação não aumenta a resolução informacional de 64 zonas.

Só há total com todos os centros suportados e referência aceita. A pirâmide principal tem cobertura completa e erro +17,50%: cobertura não certifica precisão. Lacunas ficam nulas. `unobserved_possible_volume_m3` soma nas lacunas a área vezes a altura disponível até z=0,15 m; não é intervalo de confiança e não inclui o erro da região observada. O observado não é um limite inferior exato.

## Sensibilidade e escala

`estimate(raw, reference_offset_m=...)` desloca somente o piso do estimador em testes offline; os bytes do gerador ficam fixos. A API usa deslocamento zero. Com suporte e truncamento inalterados, `ΔV ≈ −A δh`. Em 0,09 m², 1 mm equivale a 0,00009 m³ (0,09 L). Mais zonas não removem esse erro comum.

A quantização continua em milímetros; margens absolutas não diminuem com a maquete. Diminuir todas as dimensões proporcionalmente não cria novas zonas sobre a mesma forma relativa. Veja [TESTES.md](TESTES.md), [MONTAGEM_30CM.md](MONTAGEM_30CM.md) e a curva de referência.
