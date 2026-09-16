# Crítica geométrica independente do mecanismo D001 (pré‑pontuação)

**Escopo e limites.** Baseio‑me apenas no texto fornecido. Não li código, não vi resultados de D001 e nada aqui aprova implementação não apresentada. Todos os números abaixo são derivados do enunciado (0,30 m; células 0,015 m; 8×8 raios; FoV 45°; z₀=0,40 m) e estão marcados com a incerteza correspondente.

## 0. Orçamento amostral (a restrição que domina tudo)

Com 8 raios sobre 45° a partir de 0,40 m, o passo angular no piso dá espaçamento entre raios de ≈0,041–0,047 m se os raios ocuparem todo o FoV; o fato relatado de a camada plana render 256/400 células de domínio TIN (≈0,24 m de vão, passo ≈0,034 m) sugere vão efetivo menor. Trabalho com **passo s ≈ 0,035–0,047 m = 2,3–3,1 células**. Consequências que independem de qualquer segmentação:

1. **Nyquist:** feições com largura < ~2s (0,07–0,09 m) não são resolúveis. Nenhum ajuste de planos cria informação abaixo disso.
2. **Localização de quebras:** a posição de uma aresta/degrau só é determinada a ±s/2 ≈ 0,017–0,024 m. Uma única quebra reta atravessando a caixa com desnível Δh gera ΔV ≈ 0,30·0,02·Δh ≈ 0,006·Δh m³. Para Δh=0,05 m em cima de um volume de 0,0045 m³, isso é **≈6,7% — já acima da meta de 5% com um só degrau**. Isto é coerente com o resultado citado de que congelar 1,5 cm de resíduo verdadeiro nas transições não salva a rampa: o erro de transição é de **amostragem**, não de reconstrução.
3. **Cobertura:** 256/400 na camada significa **~36% da área fora do domínio amostrado, mesmo no caso plano**. "Sem extrapolação" ⇒ subestimação estrutural de sinal único, muito maior que 5%. D001 só sai disso declarando um modelo de fronteira (ex.: estender o plano até as paredes da caixa, que é especificação do contêiner, não verdade da cena) — e isso é **prior**, deve ser pré‑registrado e contabilizado como tal.

Previsão falseável: sem modelo de fronteira declarado, camada/pirâmides continuarão *parciais*; e parcial ≠ total aprovado.

## 1. Plano falso cruzando degraus

Suporte mínimo de **4 vértices é quase não falseável**: três pontos definem o plano exatamente; o quarto só precisa cair em 0,002 m. Um plano inclinado pode conter exatamente dois vértices do patamar superior e dois do inferior (ex.: Δz=0,05 m em Δx=0,08 m ⇒ inclinação 32°) com resíduo nulo. Além disso, 4 pontos vizinhos formam base de ~0,04 m; com quantização de 1 mm, a incerteza angular é ~1,4°, que extrapolada por 0,20–0,30 m vira 5–7,5 mm de altura — em 0,09 m², ~10⁻⁴–10⁻³ m³.

Verificações concretas (todas sem verdade):
- Suporte mínimo ≥ 6–8 vértices, **abrangendo ≥2 linhas e ≥2 colunas** da grade de raios, com razão de aspecto em planta ≥ 1:3 (rejeitar suportes quase colineares).
- **Teste de padrão de sinal dos resíduos**: rejeitar plano cujo resíduo tenha uma corrida contígua de mesmo sinal ao longo de ≥2 espaçamentos de raio (assinatura de degrau/curvatura absorvida).
- **Tolerância ortogonal, não vertical**: tolerância vertical de 2 mm equivale a 2·|n_z| mm de distância normal, ou seja, é *mais severa* em planos íngremes e mais frouxa em planos rasos — fragmenta rampas e permite planos rasos falsos. Fixar tolerância na distância ortogonal com termo de inclinação pré‑declarado.
- **Teste de contradição no footprint**: nenhum ponto observado não atribuído pode estar dentro do footprint do plano fora da tolerância.

## 2. Conectividade

Risco: rótulos idênticos atribuídos a componentes espacialmente disjuntos (um plano "atravessando" a sombra da viga ou o vale entre as duas pilhas).
- Exigir componente **conexa na malha de índices de raio** *e* distância 3D entre vizinhos abaixo do limite de aresta (0,10 m) — as duas condições, não a disjunção.
- Tratar **dropout e aresta rejeitada como barreiras rígidas**, nunca como lacuna a interpolar; um plano não pode cruzar uma barreira, só pode existir dos dois lados como duas instâncias independentes.
- Registrar o número de componentes por rótulo; se >1, é bandeira de abstenção, não uma fusão.

## 3. Cascos convexos sobre oclusões e concavidades

O casco convexo é, por definição, **monotonicamente não conservador**: ele preenche vales (duas pilhas), sombras atrás de viga/prisma e reentrâncias. Mesmo rotulado como "suporte de modelo", o rótulo só é útil se propagar para a contabilidade.
- Restringir o footprint a **casco‑alfa** com α ≈ s (ou a células a ≤ s/2 de um vértice de suporte), nunca casco convexo puro.
- **Proibir** células de casco que contenham raio com dropout, que estejam atrás de uma quebra de oclusão (mudança de profundidade > limite entre raios adjacentes) ou que estejam dentro do casco de outro plano com altura discordante > 2 mm.
- Cascos de planos distintos podem se sobrepor: exige‑se regra determinística de desempate **pré‑registrada**; sem ela, o resultado é determinístico mas arbitrário.

## 4. Interseções ambíguas

A linha de interseção de dois planos cai entre raios; qual plano "vence" na faixa de ±s decide o volume e o sinal do viés. Recomendação (substitui ponto por intervalo, sem oráculo):
- Marcar a faixa de ±s em torno de cada interseção como **indeterminada** e calcular os **dois extremos de atribuição** (todo‑plano‑alto e todo‑plano‑baixo). A diferença é um limite superior honesto da ambiguidade de quebra.
- Faces quase verticais (degraus, laterais do prisma) não são observadas e não podem alimentar um campo de altura: planos com |n_z| abaixo de limiar declarado devem ser usados só para delimitar domínio, nunca como fonte de altura. (Isto é restrição de domínio/abstenção, não o "rejeitar por inclinação" já reprovado como filtro de acurácia — não repetir aquele.)
- Integração por célula: recortar os polígonos dos planos contra as células (integral analítica) em vez de amostrar o centro; senão há viés de até meia célula (0,0075 m) ao longo de cada quebra.

## 5. Cobertura perdida

- Manter três contas **disjuntas e explícitas**: (a) volume sobre células com suporte direto; (b) volume sobre células de casco/modelo; (c) faixa ambígua de interseção; (d) células não amostradas (≈36% da área no melhor caso), com o valor atribuído e a justificativa.
- Reportar cobertura como **fração de área**, não só contagem de células TIN, e por quadro. Em `translated3_aimed` os domínios dos três quadros **não são os mesmos**; mediana de totais calculados sobre domínios diferentes não é uma combinação válida. Exigir que a diferença simétrica dos domínios seja reportada; se ultrapassar limiar pré‑registrado, abster de medianar e reportar por quadro.
- Em `fixed3` os três quadros têm a mesma pose: a mediana é degenerada, remove apenas ruído de quantização e **não reduz nenhum viés geométrico** — não deve ser lida como estabilidade.

## 6. Falsa aprovação por cancelamento

Este é o risco mais grave para a meta de 5% do total. Há dois vieses de sinais opostos e magnitudes comparáveis: subestimação de borda (~36% de área sem suporte) e superestimação por casco sobre vales/sombras. Um "≤5%" pode ser coincidência entre contas erradas.

Critério pré‑registrado sugerido (decidido **antes** de ver os números):
> Um total só conta como "aprovado" se |erro relativo| ≤ 5% **e** a soma das magnitudes não resolvidas (b)+(c)+(d), em módulo, for ≤ 5% do total estimado. Caso contrário, o resultado é "dentro de 5% não atribuível ao método" e se reporta como tal.

Complementos: reportar o erro **com sinal** por cena e a decomposição por conta; um padrão de sinais alternados com |erro| pequeno no total e grande nas partes é assinatura de cancelamento. Reportar também o intervalo do item 4 — se a largura do intervalo exceder 5% da estimativa, não há afirmação de total.

## 7. Condições de abstenção (propostas, para congelar antes da pontuação)

A1. Suporte < 6 vértices, ou colinear em planta, ou footprint < 2s de diâmetro → plano descartado.
A2. Rótulo com mais de uma componente conexa → abster para aquele rótulo.
A3. Footprint contendo dropout, sombra de oclusão ou aresta > 0,10 m → sem preenchimento.
A4. Área não amostrada acima do limiar declarado → cena marcada **parcial** (e parcial nunca é total aprovado).
A5. Largura do intervalo de ambiguidade > 5% da estimativa → sem valor pontual.
A6. Desacordo entre quadros no número de planos, suportes ou domínio acima de limiar → abstenção.
A7. Célula reivindicada por ≥2 planos com discordância > 2 mm sem regra de desempate → contribuição como intervalo.

## 8. Higiene de congelamento

- Fixar, antes de rodar: ordem de seleção de sementes, desempate sob quantização de 1 mm, comparação `≤` vs `<` na tolerância, regra de sobreposição de cascos, todos os limiares acima e a política de fronteira. Determinismo de código não é determinismo geométrico se os empates forem frequentes com só 64 pontos.
- Registrar hash do código e dos parâmetros antes de pontuar; qualquer ajuste depois dos nove resultados invalida a rodada (e nove cenas já conhecidas não substituem R007 reservado).
- Nada do estimador pode consultar verdade, tipo de cena ou parâmetros da simulação. O uso das dimensões da caixa (0,30×0,30) é admissível como especificação do contêiner, **mas é prior de fronteira** e deve entrar na conta (b).

## 9. Predições verificáveis desta crítica

(P1) Sem modelo de fronteira declarado, a camada permanece ≈60–70% do volume. (P2) Se o casco puder cruzar o vale, as duas cenas de pilhas mostrarão viés positivo; se não puder, permanecerão parciais. (P3) A rampa continuará >5%, porque seu erro é de localização de quebra/amostragem, não de topologia de superfície. (P4) `fixed3` e `translated3_aimed` divergirão pouco em `fixed3` por construção. Se P1–P3 falharem no sentido de melhora, convém investigar cancelamento antes de comemorar.

**Conclusão.** D001 é uma melhoria de *honestidade* (domínio explícito, rótulo de suporte de modelo, rejeição de interpolação entre superfícies incompatíveis), mas não ataca o limite dominante: 64 raios não localizam quebras melhor que ±2 cm, e ~36% da área não é amostrada. Espero ganho em coerência e em abstenção, não necessariamente em número de cenas ≤5% no total; e qualquer aprovação total obtida deve ser auditada contra cancelamento antes de ser declarada.
