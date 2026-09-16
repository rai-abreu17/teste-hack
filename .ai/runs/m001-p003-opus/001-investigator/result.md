# Revisão P-003 — Diagnóstico geométrico, veredito e próxima ablação

## 0. Escopo e disciplina de evidência

Trabalho apenas com o texto fornecido. Todo número abaixo é (a) citado do relatório, ou (b) derivado por aritmética explícita dos números citados — marcado como **[derivado]**. Não há acesso a frames, código, nuvens, truth ou execuções. Nenhuma quantidade nova foi medida.

---

## 1. Veredito em uma linha

A hipótese está **mecanicamente correta num regime e falsa como regra global**: seleção dura por `compactness` é um bom rejeitor de contaminação de suporte em descontinuidades, e um mau estimador em superfícies contínuas com relevo real. A REPROVAÇÃO no gate congelado está correta e deve ser mantida. A regra **não deve ser promovida**; deve ser reformulada de *seleção* para *triagem + agregação*.

---

## 2. O que `compactness` mede de fato (geometria)

O critério é: por célula, escolher a vista cujo **maior comprimento de aresta 3D** entre os triângulos locais que suportam a célula é mínimo. Para uma câmera pinhole ideal, o comprimento de uma aresta 3D entre dois pixels vizinhos é, em primeira ordem:

```
|e|  ≈  (Δθ · R) / cos(i)      (superfície contínua)
|e|  ≈  ΔZ                     (aresta que atravessa uma descontinuidade)
```

com `Δθ` o passo angular, `R` o alcance, `i` a incidência local e `ΔZ` o salto de profundidade. Reescrevendo para o campo de altura reconstruído, com espaçamento horizontal `s` e gradiente aparente `g`:

```
|e|  ≈  s · sqrt(1 + g²)
```

Disso decorre o ponto central do diagnóstico: **`compactness` é um escalar único que confunde três causas físicas distintas**:

1. **Alcance/obliquidade** — vista distante ou rasante ⇒ arestas longas (proxy razoável de qualidade).
2. **Relevo verdadeiro** — rampa, face de prisma, face de pirâmide ⇒ arestas longas *porque a superfície realmente sobe* (proxy enganoso).
3. **Ponte sobre oclusão/salto** — triângulo que interpola através de uma borda de profundidade, gerando superfície-fantasma ("véu") ⇒ arestas longas por artefato (proxy excelente).

O `argmin` sobre esse escalar é, portanto, matematicamente equivalente a **"escolher a vista que exibe o menor relevo aparente por unidade de área de solo"**. Isso é exatamente o que se quer quando o relevo excedente é artefato (caso 3) e exatamente o que **não** se quer quando o relevo é real (caso 2). O relatório já sinaliza isso na seção de limitações ("tamanho geométrico do triângulo, não incerteza calibrada nem incidência real"); a análise abaixo mostra que essa confusão é suficiente para explicar todo o padrão de sinais observado.

Observação importante sobre o cap de 0,10 m: triângulos com aresta > 0,10 m já foram eliminados na construção do TIN. Logo, os ganhos do desafiante **não vêm de pontes grosseiras** (essas já morreram no cap), mas de **pontes sub-cap** — saltos e rasâncias cujo comprimento de aresta 3D ainda cabe em 0,10 m. Isso limita a razão máxima entre a pior e a melhor vista numa célula a `0,10 / e_min`, um fato que a ablação proposta na §7 explora diretamente.

---

## 3. Por que ajuda em descontinuidades

Modelo mínimo do erro por vista em uma célula:

- **(a)** ruído quase-simétrico de amostragem/interpolação, parcialmente independente entre vistas;
- **(b)** contaminação grosseira, específica de vista e **unilateral** (sempre puxa a altura para o lado errado do salto): suporte que atravessa uma borda de oclusão, suporte rasante atrás de uma quina, ou suporte que interpola através de um buraco.

A mediana de 3 vistas trata (b) apenas se **no máximo uma** das três estiver contaminada; com 2 de 3 contaminadas — situação comum quando duas câmeras estão do mesmo lado de uma viga, pilha ou degrau — a mediana **seleciona** o valor contaminado. Nessas células a mediana não é robusta, é ativamente errada.

Já o `argmin` de aresta é um teste **direto do sintoma geométrico de (b)**: a ponte produz uma aresta anomalamente longa mesmo quando a contaminação é minoritária *ou* majoritária. Ele quebra a dependência do voto: basta **uma** vista limpa para recuperar a célula. Isso explica por que os ganhos são grandes precisamente nas cenas em que o erro de base é grande e concentrado em bordas: `pyramid_center`, `pyramid_beam`, `pyramid_beam_dropout20` (dropout aumenta a área com suporte interpolado ⇒ mais massa de (b) ⇒ maior ganho absoluto: +6,265 pp, o maior da tabela), `two_stacks`, `layer`, `layer_beam`.

Nas cenas quase planas (`layer` 0,196→0,020; `layer_beam` 0,187→0,030) a redução relativa é de ~90% e ~84% **[derivado]**. Isso só é compatível com um erro de base dominado por (b): se o erro fosse ruído (a), trocar mediana por vista única **aumentaria** o erro (§4). Ou seja, essas duas cenas são a evidência mais limpa de que `compactness` carrega sinal real sobre contaminação de suporte.

---

## 4. Por que piora prisma e rampa

Há **dois mecanismos separáveis**, e a aritmética da tabela indica que eles não atuam igualmente nas duas cenas.

### 4.1 Perda pura de agregação (atinge toda superfície contínua)

Trocar mediana-de-3 por vista única destrói o único mecanismo de cancelamento de erro (a). Sob a hipótese (forte, explicitada) de erros por vista aproximadamente gaussianos, de média zero e independentes, a mediana de 3 tem variância ≈ 0,449 σ², e a razão esperada de erro absoluto vista-única/mediana é ≈ **1/√0,449 ≈ 1,49** **[derivado, sob hipótese]**. Esse é o "custo de piso" de qualquer seleção dura em região contínua, **independente de o critério ser bom**.

### 4.2 Viés de seleção correlacionado com o erro (viés de achatamento / ramo errado)

Como `|e| ≈ s·√(1+g²)`, entre duas reconstruções da mesma superfície inclinada o `argmin` prefere sistematicamente aquela com **menor gradiente aparente** — isto é, a mais suavizada/achatada. Em superfície contínua isso não é ruído: é um **viés unilateral coerente no espaço**, que atenua a inclinação da rampa e o degrau do prisma. Além disso, num prisma com faces verticais, os pontos *da parede* formam faixas densas e compactas que caem sobre a banda estreita de células do contorno da planta; o `argmin` pode preferir sistematicamente o ramo "parede" (altura intermediária entre solo e topo) em vez do ramo "topo", produzindo uma faixa de erro coerente ao longo do contorno. A mediana, exigindo concordância de 2 de 3 vistas, resiste melhor a essa troca de ramo.

### 4.3 Diferencial quantitativo entre as duas cenas

Razão desafiante/base **[todas derivadas]**:

| cena | base | desafiante | razão | leitura |
|---|---|---|---|---|
| layer | 0,196 | 0,020 | 0,102 | (b) domina; sem relevo real a perder |
| layer_beam | 0,187 | 0,030 | 0,160 | idem |
| pyramid_shifted_013 | 1,623 | 0,828 | 0,510 | pirâmide, mas base já baixa |
| pyramid_center | 17,266 | 13,497 | 0,782 | ─┐ |
| two_stacks | 5,374 | 4,256 | 0,792 |  ├ agrupamento 0,78–0,83 |
| pyramid_beam | 13,966 | 11,058 | 0,792 |  │ efeito multiplicativo estável |
| pyramid_beam_dropout20 | 37,251 | 30,986 | 0,832 | ─┘ |
| ramp | 10,652 | 13,875 | **1,303** | ≲ 1,49: compatível com §4.1 apenas |
| prism | 3,973 | 7,864 | **1,979** | > 1,49: exige §4.2 além de §4.1 |

Duas leituras estruturais:

- A `ramp` piora por um fator **abaixo** do piso teórico de perda de agregação. Não é necessário postular nenhum mecanismo extra para ela: o regime é "erro (a) domina, (b) quase ausente, agregação é o que estava funcionando". Possivelmente há até um pequeno ganho de (b) nas quebras superior/inferior, parcialmente compensando.
- O `prism` piora por ≈ 2,0×, **acima** do piso. Isso é assinatura de um viés adicional, coerente e espacialmente estruturado — consistente com achatamento do degrau e/ou seleção do ramo "parede" na banda do contorno. O prisma é a cena que mais informa sobre o defeito do critério.
- O agrupamento apertado 0,78–0,83 em quatro cenas de topologia semelhante, com erros de base variando de 5,4 a 37,3 pp, indica um efeito **multiplicativo** (fração fixa de células contaminadas sendo corrigida), não um efeito idiossincrático ou ruído de execução.

**Síntese**: o sinal de Δ é previsto pela razão (b)/(a) da cena, isto é, pela proporção entre erro de contaminação em bordas e erro difuso em superfície. Descontinuidades ⇒ (b) domina ⇒ seleção vence. Relevo contínuo grande ⇒ (a) domina e o critério passa a estar *anticorrelacionado* com a verdade ⇒ seleção perde duas vezes.

---

## 5. Consistência interna e integridade

- Reprodução exata da mediana em todas as cenas + suporte preservado exatamente ⇒ o desenho é **pareado e determinístico**, e os Δ são atribuíveis exclusivamente à regra de fusão. Validade interna alta.
- Recomputei todas as 9 diferenças **[derivado]**: 7 batem exatamente. Duas divergem em 0,001 pp: `ramp` (13,875 − 10,652 = 3,223 vs. −3,224 reportado) e `layer_beam` (0,187 − 0,030 = 0,157 vs. +0,156 reportado). Compatível com arredondamento dos valores subjacentes; registro como nota de consistência, **sem** implicação para o veredito.
- Agregados batem: mediana das 9 reduções = 0,795 pp; 7/9 vitórias; regressão máxima 3,891 pp **[derivado]**.
- Critérios do gate: mediana 0,795 < 1 pp ✗; vitórias 7/9 ✓; regressão máxima 3,891 > 2 ✗; suporte 96% ≥ 84% ✓; total 4/9 ≥ 4 ✓; domínio 9/9 ✓. **Duas falhas**, não uma.

### 5.1 Achado estrutural sobre o gate (importante)

O critério "redução mediana ≥ 1 pp" sobre 9 cenas exige **pelo menos 5 cenas com redução ≥ 1 pp** **[derivado]**. Mas `layer` e `layer_beam` têm erro de base 0,196 e 0,187 pp: a redução máxima fisicamente possível nelas é < 0,2 pp. Logo, apenas 7 cenas são elegíveis e é preciso que 5 dessas 7 atinjam ≥ 1 pp. Hoje são 4 (`pyramid_center`, `two_stacks`, `pyramid_beam`, `dropout20`). Consequência direta e verificável:

> **Mesmo que uma variante zere completamente as regressões de `prism` e `ramp`, a mediana permanece 0,795 pp e o gate continua reprovando.** **[derivado]**

Para passar, é obrigatório que `prism` ou `ramp` virem **ganho ≥ 1 pp**, ou que `pyramid_shifted_013` suba de 0,795 para ≥ 1,0 pp. Isso deve ser escalado a quem congelou o gate: não estou propondo alterá-lo aqui, mas qualquer roadmap que ignore essa restrição desperdiçará iterações.

---

## 6. Veredito sobre a hipótese

1. **Rejeitada como substituta da mediana.** Reprovação correta; dois critérios falhados, não um limítrofe.
2. **Sustentada como detector.** `compactness` carrega informação real e não-trivial sobre contaminação de suporte, disponível ao estimador e sem truth. As evidências mais fortes são `layer`/`layer_beam` (reduções de 90%/84%, incompatíveis com acaso ou com perda de agregação) e a consistência multiplicativa 0,78–0,83 na família pirâmide.
3. **O defeito é o operador, não o sinal.** `argmin` tem ponto de ruptura zero em relação a erros do próprio critério e descarta integralmente a agregação. O sinal deve entrar como **triagem** (excluir vistas manifestamente piores) preservando **agregação** entre as sobreviventes.
4. **Ressalva de calibração mantida.** Aresta 3D ≠ incerteza calibrada. Em pinhole ideal a aresta é quase inteiramente geometria; com hardware real (ruído dependente de alcance, multipath, saturação, calibração) a relação aresta↔erro pode mudar de forma e até de monotonicidade. Nenhuma conclusão aqui deve ser transportada para hardware sem revalidação.

---

## 7. Próxima ablação mínima (uma só)

**Nome**: `trimmed3_kappa2` — mediana aparada por razão de compactness.

**Regra** (usa apenas informação já disponível ao estimador: aresta 3D máxima por vista/célula, já computada em P-003; índice de captura; geometria decodificada; nenhum truth, nenhum parâmetro por cena):

Para cada célula `c` com conjunto de vistas de suporte `V(c)`:
1. `e_min(c) = min_{v∈V(c)} maxedge_v(c)`
2. `S(c) = { v : maxedge_v(c) ≤ κ · e_min(c) }`, com **κ = 2,0 fixo a priori**
3. Se `|S(c)| ≥ 2`: altura = mediana inferior de `{z_v(c) : v∈S(c)}` (mediana inferior para determinismo com cardinalidade par)
4. Se `|S(c)| = 1`: altura dessa vista
5. Empates de qualquer natureza: menor índice de captura (mesma convenção de P-003)

Tudo o mais congelado: frames P-001 `translated3_aimed`, TIN aresta máxima 0,10 m, domínio `common_all` original, suporte, métrica, 9 cenas, protocolo SHA-256. Suporte **deve** permanecer exatamente igual (a regra nunca remove a vista de `e_min`, logo `|S(c)| ≥ 1` sempre). Verificar isso é pré-condição de validade da corrida.

**Por que esta e não outra**: é a menor modificação que separa as duas funções que P-003 fundiu indevidamente — *rejeição de contaminação* (mantida) e *agregação* (restaurada). Reusa os frames e o escalar já calculado; custo marginal ≈ zero. κ = 2,0 é fixado antes da corrida, não ajustado sobre estas 9 cenas; qualquer varredura de κ posterior é diagnóstico, não promoção (risco de seleção sobre o conjunto de avaliação).

### 7.1 Previsão falsificável (registrar antes de rodar)

**P1 — regressões contidas.** `prism` ≤ **5,973** pp e `ramp` ≤ **12,652** pp (isto é, regressão ≤ 2 pp; limiares derivados do gate congelado, não inventados).
**P2 — ganhos preservados.** Retenção ≥ 50% do ganho da seleção dura nas três maiores: `pyramid_center` ≥ **+1,885** pp, `pyramid_beam` ≥ **+1,454** pp, `dropout20` ≥ **+3,133** pp **[derivados de 3,769 / 2,908 / 6,265]**.
**P3 — invariantes.** Suporte idêntico ao baseline; domínio 9/9; mediana reproduz P-001 quando `κ → ∞`.

**Condições de falsificação e o que cada uma implica:**

- **P1 falha** (prisma/rampa continuam regredindo > 2 pp): a contaminação sub-cap **não** é separável por razão de aresta; o critério está anticorrelacionado com o erro de forma graduada, não em cauda. Implicação: abandonar a família `compactness` como critério de fusão e passar a um critério que separe relevo real de artefato (ex.: consistência **entre vistas** do valor decodificado, não tamanho de triângulo intra-vista).
- **P2 falha** (ganhos < 50%): os ganhos de P-003 dependiam de **compromisso total com uma vista**, ou seja, em muitas células ≥ 2 de 3 vistas estavam contaminadas e nenhuma aparagem mediana pode salvar. Implicação: o problema é de **configuração de vistas** (3 câmeras `translated3_aimed` é insuficiente perto de vigas/pilhas), e a próxima alavanca é geometria de aquisição, não regra de fusão.
- **P1 e P2 passam mas o gate ainda reprova**: esperado e já previsto em §5.1 — confirma que a barreira restante é estrutural (mediana ≥ 1 pp inatingível sem converter `prism`/`ramp` em ganho ou elevar `pyramid_shifted_013`), e a decisão sai do domínio técnico para o de escopo do gate.

### 7.2 Diagnósticos sem truth, sem corrida extra (registrar na mesma execução)

Para discriminar §4.1 de §4.2, que a métrica agregada não separa:

- **D1 — assinatura de achatamento**: média de `|∇z|` sobre as células de `ramp` e sobre a banda do contorno de `prism`, comparando desafiante P-003 vs. mediana baseline. Predição do mecanismo §4.2: `|∇z|_argmin < |∇z|_mediana`. Se **não** se observar, o viés de achatamento está refutado e o excesso do prisma (razão 1,98 vs. piso 1,49) deve ser atribuído a troca de ramo.
- **D2 — assinatura de ramo errado**: histograma de altura nas células da banda do contorno do prisma. Troca de ramo prediz massa **intermediária** entre solo e topo (pontos de parede); achatamento prediz deslocamento **monotônico** das duas populações uma em direção à outra sem moda intermediária.
- **D3 — fração de aparagem**: por cena, fração de células com `|S(c)| < |V(c)|`. Predição: alta em `pyramid_*`/`layer_*`, baixa no interior planar da `ramp`. Se for alta na rampa, κ = 2,0 está capturando diferença de alcance/obliquidade e não contaminação — diagnóstico direto do confundimento da §2.
- **D4 — controle de atribuição**: fração de células em que a vista `argmin` coincide com a de menor índice. Se for muito alta em `layer`/`layer_beam`, parte do ganho dessas cenas é atribuível ao desempate por índice ("usar sempre a captura 0") e não a `compactness`. Este é o principal confundidor não controlado em P-003 e deve ser quantificado antes de creditar o critério.

---

## 8. Limitações e ameaças à validade (explícitas)

- **Simulador pinhole ideal, sem hardware.** Todo o argumento da §2 depende de que aresta 3D ≈ geometria pura. Com sensores reais isso deixa de valer e o sinal pode inverter.
- **N = 9 cenas, 1 configuração de pose, 3 vistas, sem repetições/seeds.** Os Δ são deterministicamente pareados (validade interna forte), mas a variância amostral entre *famílias de cena* e a generalização para outras configurações de captura são desconhecidas. "7/9 vitórias" não é evidência estatística independente: as cenas da família pirâmide são fortemente correlacionadas.
- **O fator 1,49 da §4.1 é heurístico**, válido sob gaussianidade, média zero e independência entre vistas — nenhuma dessas hipóteses foi verificada. Uso-o como régua de ordem de grandeza para separar `ramp` (≤ régua) de `prism` (> régua), não como valor esperado.
- **Atribuição de mecanismo é inferência, não medição.** Achatamento e troca de ramo são hipóteses compatíveis com os agregados; D1/D2 existem justamente porque os dados atuais não as distinguem.
- **Desempate por índice não controlado** (D4): confundidor plausível em cenas planas.
- **Divergências de 0,001 pp** em duas linhas (§5): provável arredondamento; não afetam o veredito, mas convém confirmar a precisão de origem antes de qualquer gate com margens sub-décimo.

---

## 9. Recomendação

Manter **REPROVADO**. Não promover seleção dura. Executar `trimmed3_kappa2` com P1–P3 registrados previamente e D1–D4 coletados na mesma corrida. Em paralelo, escalar o achado de §5.1: o critério de mediana ≥ 1 pp é estruturalmente inatingível para qualquer regra que não converta `prism` ou `ramp` em ganho, porque duas das nove cenas têm erro de base abaixo de 0,2 pp.
