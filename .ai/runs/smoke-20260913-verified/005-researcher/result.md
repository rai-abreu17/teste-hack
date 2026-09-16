**Fatos fornecidos:** base quadrada interna L = 30 cm; altura do material H = 12 cm; distância sensor–superfície h = 20 cm; FoV completo θ = 60° em cada eixo ortogonal; projeção quadrada, centralizada, alinhada aos lados da caixa; idealização sem distorção/ruído/reflectância/obstáculos.

**(1) Volume:** V = L² · H = 30² × 12 = 8100 × ... = 10 800 cm³ → V = 10 800 / 1000 = **10,8 L**.

**(2) Lado da projeção:** w = 2h·tan(θ/2) = 2×20×tan(30°) = 40×0,5774 ≈ **23,09 cm**.

**(3) Fração coberta:** como w < L, a projeção cabe inteiramente dentro da base; f = w²/L² = 23,09²/900 ≈ 533,3/900 ≈ **0,593 (≈59,3%)**.

**(4) Rotação e oclusão:** manter o centro óptico fixo e girar apenas a orientação do sensor muda a direção do eixo de visada e, portanto, qual região da superfície é enquadrada — mas não altera a posição do centro óptico nem os segmentos retilíneos entre esse centro e pontos fixos da cena. Se um obstáculo intercepta a linha de visada entre o centro e um ponto ocluído específico, essa reta geométrica permanece a mesma independentemente do ângulo de rotação; o obstáculo continua bloqueando esse ponto. Rotação só revela pontos que passam a entrar no novo cone de FoV a partir do mesmo centro, não pontos cuja linha de visada permanece obstruída pelo mesmo objeto.

**Gaps/hipóteses:** assume alinhamento perfeito eixo-a-eixo e ausência de vinheteação; projeção tratada como plana na superfície (sem inclinação). Nenhuma geometria de obstáculo foi fornecida, logo oclusão é tratada apenas conceitualmente. Resultado é puramente geométrico-idealizado; não valida sensor real, servo ou arquitetura do BoxFlow.
