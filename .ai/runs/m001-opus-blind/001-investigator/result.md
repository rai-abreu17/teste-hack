# M-001 — Análise independente (rodada 1)

**Legenda de evidência:** [S] simulado/documentado no pacote · [D] dedução geométrica minha a partir dos números do pacote · [H] hipótese · [L] lacuna (não fornecido; não inventar).

## 1. Problema observável

Observável hoje: **erro de volume total** e **amplitude de erro entre poses** em cenas sintéticas com verdade analítica externa ([S]: pirâmide 0,5625 L → 0,660934 L, +17,50 %; 16,11 pp em 21 posições). Não é observável: desempenho óptico real, mistura de retornos por zona, deriva térmica, reflectância do material [L].

Reproduzi os números de cobertura por geometria de raio central com FoV 45°/eixo, 8×8, zonas centradas em ±(k+0,5)·5,625° (máx. 19,69°, tan ≈ 0,3578) e células de 1,5 cm: alcance lateral = 0,3578·(z−7,5); centros de célula até 14,25 cm. Isso dá 16/20 → 64 % (z=40), 18/20 → 81 % (z=45), 20/20 → 100 % (z≥47,3) [D]. Ou seja, **“cobertura” no pacote é o domínio do casco de raios, não densidade de medida**: com 64 raios e 400 células, ≤16 % das células contêm amostra; o resto é interpolação/extrapolação [D]. A queda 73 %/49 % em 49–50 cm não é explicada pelo raio central puro; a explicação compatível é que raios externos passam a cair sobre topo de parede (15 cm) ou fora da área de material, perdendo amostras da camada [H — verificável relendo scene_dump].

## 2. Restrições

(a) Verdade só no avaliador; comparações devem usar `truth.py` com recorte exato por célula. (b) O estimador publica total apenas com suporte completo → **comparar configurações por “erro do total” introduz seleção**: configurações que falham não geram total. (c) 64 amostras por captura; qualquer total exige extrapolação até a borda. (d) A altura útil do sensor depende do enchimento: com camada em 15 cm a distância cai para 25 cm e o rodapé de cobertura encolhe; nenhum z fixo é ótimo para todos os níveis [D]. (e) CLI sem `originX/Y` → centros ópticos distintos ainda não são simuláveis [S].

## 3. Mecanismos candidatos (e o que cada um pode fisicamente resolver)

- **Fixo**: limitado por FoV e por sombra do ponto de vista.
- **Rotação em torno do mesmo centro óptico**: muda apenas o *enquadramento*. O feixe continua saindo de um ponto único; ganha direções novas (mais área e densidade dentro do casco), mas **não altera o conjunto de visibilidade**: qualquer ponto oculto por viga, degrau ou sobreposição permanece oculto [D]. Portanto pode curar cobertura limitada por FoV, nunca oclusão própria.
- **Centros ópticos distintos (translação)**: muda visibilidade e cria paralaxe → único mecanismo capaz de iluminar sombras e de checar consistência geométrica; custo = calibração de pose, cujo erro entra linearmente na altura reconstruída [D].
- **Reconstrução/prior**: o ajuste piramidal (0,98/2,32 pp) troca erro de medida por **risco de modelo**; é prior, não cobertura [S+D].
- **Repetição no mesmo pose**: no mock determinístico, ganho exatamente nulo; com dropout/ruído, ganho ~1/√N. Serve como **controle** para separar “número de capturas” de “ponto de vista”.

## 4. Hipóteses promissoras vs. frágeis

- **H2 (promissora):** o +17,5 % é dominado pela **extrapolação da margem** — células fora do casco recebem altura de amostras de meia-encosta, somando volume inexistente. Prevê: erro total correlacionado com área extrapolada × altura extrapolada média, e erro pequeno/quase não enviesado no domínio medido. Explica também a amplitude de 16,11 pp (depende de onde os raios caem) [H, derivada de [D]].
- **Frágeis:** “aumentar densidade angular elimina pontos cegos” (contradito por perfil denso 75 % [S]); “elevar o sensor resolve” (não monotônico e dependente do nível); “rotação resolve oclusão” (impossível por geometria [D]); “fit piramidal generaliza” (família condicionada [S]); “ToF/servo/LiDAR é a solução” (nenhum tem evidência física aqui).

## 5. Lacunas de evidência [L]

Datasheet e comportamento real do VL53L5CX (cone de zona vs. raio, sigma por status, crosstalk, teto de ambiente, alcance sobre material escuro); BRDF/refletância e granulometria do material; repetibilidade/backlash de servo; tolerância mecânica de montagem e método de verdade física na maquete (deslocamento de água? massa/densidade?); orçamento radiométrico ao elevar o sensor; multipath em cantos de parede. Nada disso deve ser extrapolado do mock de primeira interseção.

## 6. Três experimentos discriminantes (pequenos, sem tocar dashboard/firmware)

**E5 — Decomposição do erro por domínio (sem código novo).** Reaproveitar as 21 posições e famílias existentes; para cada célula classificar *medida* (contém raio) / *interpolada* (dentro do casco) / *extrapolada*; reportar volume e erro assinado por classe contra `truth.py`. Discrimina H2 contra “viés de interpolação convexa” e contra bug do estimador. Nenhum limiar novo: o critério é o **sinal e a decomposição**, não um percentual.

**E6 — Orçamento de raios igualado (requer só expor `originX/originY` no CLI).** Quatro braços com **mesmo total de raios K×64**: (A) fixo 1× (referência), (D) K capturas idênticas (controle: deve dar erro idêntico a A no mock; se não der, há não-determinismo), (B) K rotações puras em torno do centro óptico ladrilhando o FoV, (C) K origens distintas com mesma orientação e baseline b. Cenas: camada (plana), pirâmide, rampa, **viga** (auto-oclusão). Fusão puramente geométrica (pontos → TIN existente), sem prior. Métricas em **domínio comum às quatro** e, separadamente, no total com a contabilidade de E5. Previsão discriminante: B≈C nas cenas sem sombra; C≪B apenas onde há sombra (viga/rampa). Isso separa enquadramento de ponto de vista.

**E7 — Robustez da pose (fator dentro de E6-C).** Injetar erro de translação/rotação em grade e dropout/perda já configurável; medir a curva de degradação do ganho multi-centro. Define o requisito de calibração em vez de pressupor servo.

Crítica cruzada: nesta rodada não recebi análise de outro agente; sem texto, não há refutação a fazer.
