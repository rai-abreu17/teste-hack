# M-001 — Leitura física/geométrica independente

## 0. Declaração de acesso (ler antes de tudo)

**Não tive acesso a nenhum dos artefatos listados.** Não possuo ferramentas, sistema de arquivos, memória ou contexto externo nesta execução. Portanto **não li** `.ai/experiments/m001/protocol.json`, `protocol.sha256`, `m001_estimator.py`, `run_p001.py`, `scene_dump_m001.c`, `.ai/runs/m001-implementation/results/comparisons.json`, `comparisons.csv`, `summary.md`, `command-log.json`, `.ai/decisions/m001-protocol-decision.md`, nem as quatro análises cegas/cruzadas ou a pesquisa.

Consequência direta e importante: **o item (2) do pedido — "interpretação causal sustentada por dados por cena" — não é executável a partir do contexto fornecido.** Recebi apenas *medianas de 9 cenas*. Toda inferência causal abaixo é formulada no nível agregado e marcada como hipótese com o teste que a decidiria. As citações de caminho abaixo são **alvos de auditoria** (o que checar e onde), não leituras verificadas.

O que efetivamente usei: a tabela de medianas, os fatos de execução (`-Wall -Wextra -Werror`, 7/7 testes, 72/72 comparações = 8 braços × 9 cenas, correção de stdout binário no Windows) e as seis restrições de interpretação.

---

## 1. Auditoria metodológica e de código (itens a verificar, com predições)

**A1 — `fixedN` é duplicação exata, não densificação.** `baseline_fixed1`, `fixed3` e `fixed4` são idênticos em *cinco* colunas simultaneamente (4/9, 16.0%, 84.0%, 94.5%, +4.08%) com 64/192/256 raios. Isso só é possível se os N sensores compartilham origem **e** grade de direções, gerando raios duplicados que a mediana por célula absorve idempotentemente. Verificar geração de extrínsecas em `scene_dump_m001.c`. Duas leituras: (i) é um **controle de determinismo excelente** — a igualdade a 0.01 pp exclui qualquer jitter estocástico; (ii) é uma **lacuna de desenho** — não existe controle de vista única com orçamento de raios igualado a 192/256. Sem esse controle, nenhum braço multi-vista está comparado a "mesmo orçamento, uma vista mais densa".

**A2 — `suporte TIN` não pode ser união de domínios por vista.** Adicionando vistas o suporte *cai*: 84.0% (1 vista) → 74.5% (`center_angles4`) → 49.0% (`translated4_corners_level`). União é monotonicamente não decrescente; logo a métrica é (a) interseção/quórum de vistas, ou (b) união com filtro por célula que rejeita discordância entre vistas, ou (c) exige ≥2 amostras para a mediana. Verificar a função de suporte em `m001_estimator.py`. **Isto é decisivo**: sob (a) ou (c), a queda de suporte é *artefato da regra de fusão*, não perda física de observação — e reporta o oposto da premissa do projeto.

**A3 — confusão suporte × erro (o problema mais grave).** Os dois braços de menor suporte têm os menores erros: 74.5% → +4.71%, 49.0% → +3.63%. E *todo* braço do grupo-4 melhora ao ser restrito ao domínio comum (`fixed4` 4.08→3.97; `center_angles4` 4.71→4.21; `corners` 3.63→2.47). Se o domínio comum fosse neutro, as mudanças teriam sinais mistos. Serem **todas** favoráveis prova que o domínio comum do grupo-4 é *mais fácil* que os domínios próprios — o que é geometricamente esperado, pois a interseção de quatro frustos de canto é o **núcleo central** da caixa: alta incidência (perto da normal), pegada de raio compacta, triângulos TIN pequenos. Ou seja, `common_group` **não remove** o confundimento; ele move todos para o núcleo fácil, limitado pelo braço de pior suporte (≤49%). Verificar em `run_p001.py`/`m001_estimator.py` se `common_group`/`common_all` são interseção por cena e se são recomputados por cena (correto) ou sobre medianas (inválido).

**A4 — erro reportado para braços com 0/9 válidos.** `center_angles4` e `translated4_corners_level` têm **total válido 0/9** e ainda assim medianas de erro. Ou "total válido" é um gate distinto do cálculo de erro por célula, ou medianas misturam cenas válidas e inválidas. Nos outros seis braços, 4/9 válidos com mediana "de 9 cenas" significa que o 5º valor ordenado vem de uma cena inválida. Checar o denominador da mediana em `run_p001.py`.

**A5 — sinal digital sugere n par nas medianas.** Predominam valores em .5 (94.5, 96.5, 74.5, 28.5, 25.5). Mediana de 9 (ímpar) devolve um valor *observado*; médias de dois valores centrais indicam **n par** (4 ou 8), isto é, subconjunto válido. Confiança moderada, inferência puramente de padrão de dígitos — verificar diretamente.

**A6 — integridade dos quadros binários.** A correção de stdout binário no Windows (expansão CRLF) é um risco real de corrupção silenciosa: 0x0A dentro de floats de profundidade viraria 0x0D0A. Confirmar em `.ai/runs/m001-implementation/command-log.json` que a correção precede **todas** as 72 comparações. Note que `protocol.sha256` cobre o protocolo, **não** os quadros — a integridade dos dados pode estar não verificada. Checksum dos quadros seria barato e eliminaria essa dúvida.

**A7 — cobertura de testes.** `-Werror` + 7/7 atesta higiene de compilação, não correção geométrica. 7 testes é fino para TIN + fusão + oráculo. Perguntar se algum cobre: célula vista por exatamente 2 vistas com profundidades discordantes (empate de mediana), incidência rasante, e a definição de suporte (união vs. quórum).

---

## 2. Leitura física e geométrica

**Rotação em torno do centro de projeção não pode alterar oclusão — e os dados confirmam.** Visibilidade do oráculo é **exatamente 94.5%** em `fixed1`, `fixed3`, `fixed4`, `center_tilt3` e `center_angles4`. Oclusão é determinada pela *origem* do raio; girar o centro óptico muda quais direções são amostradas (bins: 16% → 30% → 37%), nunca o que está atrás de um monte. Isto é necessidade geométrica, não achado empírico.

**Translação recupera os 5.5 pp residuais integralmente.** Todos os três braços transladados dão **100.0%**. Fisicamente coerente numa caixa: uma vista de teto central não vê o piso junto à parede próxima nem o lado oposto de um monte; uma base de translação da ordem da altura do monte resolve ambos. Três vistas bastaram.

**Mas a translação, neste pipeline, é informacionalmente truncada.** A restrição "a fusão nunca cria triângulos entre vistas" significa que a paralaxe é usada **só como cobertura**, nunca como vínculo estéreo/consistência multi-vista. O principal ganho informacional da translação está arquiteturalmente descartado. Resposta direta à pergunta do meu papel: *a translação oferece informação observável útil apenas na classe "oclusão" (5.5 pp de visibilidade), e nenhuma em acurácia como está fundida.*

**Por que 3 vistas pioram o erro.** `center_tilt3` +8.40/+9.73 e `translated3_level` +7.88/+9.46 contra baseline +4.08. Mecanismo mais provável: **mediana não ponderada de 3**, onde 2 vistas são oblíquas. A mediana é robusta a *outliers*, não a *viés correlacionado da maioria*. Com 1 vista frontal você obtém a estimativa de melhor incidência; com 3 vistas a mediana é arrastada para o par oblíquo, cujo erro de profundidade projetado na normal escala ~1/cos θ e cuja pegada alongada gera triângulos TIN grandes. Somado a isso, orçamento fixo de 64 raios/vista: espalhar ângulos **dilui densidade** (bins ↑ 16→37 enquanto suporte ↓ 84→74.5). O eixo dominante nos dados é **densidade amostral por área**, não número de pontos de vista.

**Por que `translated3_aimed` foge do padrão.** Único braço que *melhora* do domínio próprio para o comum (8.07 → 5.78). Convergência concentra amostras no alvo central — melhor incidência e densidade exatamente onde o domínio comum vive, ao custo da periferia. História física consistente.

**Viés de sinal único.** Todos os oito erros são **positivos** (+2.47% a +9.73%). Isso é assinatura de viés sistemático de modo comum (interpolação TIN sobre superfície curva, discretização, quantização de células), não de ruído de amostragem. Mediana entre vistas **não remove** viés compartilhado por todas as vistas. Implicação forte: o resíduo de ~4% do baseline provavelmente **não é dominado por oclusão** — nenhum braço com 100% de visibilidade bate +4.08% num domínio genuinamente compartilhado com o baseline.

**O que vejo no grupo-3 que contraria a narrativa de "multi-vista ajuda".** O domínio comum do grupo-3 é limitado pelo pior suporte, ~84% ≈ domínio do `fixed3`. Restritos a ele, os braços multi-vista **pioram** (8.40→9.73, 7.88→9.46) enquanto `fixed3` fica em 4.08. Ou seja: *nas células que a vista única já cobria, adicionar vistas degradou a estimativa em ~+5.4 pp.* Este é o resultado mais robusto contra a premissa do projeto.

---

## 3. Hipóteses

**Confirmadas (dentro da simulação)**
- **H1** Rotação em centro fixo não recupera oclusão. Evidência: 94.5% idêntico em cinco braços + necessidade geométrica. Alta confiança.
- **H2** Translação recupera toda a oclusão residual destas cenas (100.0%, três braços) — sob a definição do oráculo (LoS intrínseca a centros verdadeiros, sem FoV). Alta confiança, escopo estreito.
- **H3** `fixedN` é no-op de duplicação. Alta confiança.
- **H4** Suporte reportado é não monotônico em nº de vistas → não é união. Alta confiança no fato; mecanismo (quórum vs. rejeição por discordância) indeterminado.

**Refutadas**
- **H5** "Mais vistas ⇒ mais acurácia": refutada em 3 vistas, nos dois domínios.
- **H6** "Braços de 4 vistas estão prontos para hardware": refutada por **0/9 totais válidos**.
- **H7** "Visibilidade do oráculo prediz qualidade": refutada — braços a 100% cobrem erros de +2.47% a +9.46%, e o de 100% tem o *menor* suporte (49%).

**Inconclusivas**
- **H8** "`translated4_corners_level` é o mais acurado": provavelmente **artefato** — 49% de domínio central fácil + 0/9 válidos. Decidível por A3.
- **H9** "Convergência > paralelo": sugestiva (5.78 vs 9.46), confundida por composição de domínio.
- **H10** "O resíduo de +4% é oclusão": evidência aponta para viés de modo comum do estimador. **Questão aberta de maior valor.**
- **H11** "As mesmas 4 cenas são válidas em todos os braços" (seis braços em exatamente 4/9 sugere gate dirigido pela cena, não pela configuração): **não resolvível por medianas**; exige as linhas por cena de `comparisons.csv`.

**Lacuna do oráculo quantificada.** Otimismo = visibilidade − suporte: `translated3_level` 3.5 pp; `translated3_aimed` 4.0 pp; `center_angles4` 20.0 pp; `translated4_corners_level` **51.0 pp**. O oráculo ignora FoV/orientação; quanto mais a geometria exige FoV largo e incidência rasante (cantos), mais frouxo ele é. `translated3_level` é a configuração onde a promessa é quase realizada.

---

## 4. Recomendação (concreta e falsificável)

**Não avançar para teste físico agora, e não escolher nenhuma configuração de 4 vistas.** Os dois braços de menor erro têm 0/9 válidos e domínio de avaliação de 49%. Rodar quatro ablações de simulação primeiro (barato, decide tudo):

| # | Ablação | Predição | Refutação |
|---|---|---|---|
| A1 | Recalcular suporte como **união** dos domínios TIN por vista | União monotônica; `corners4` ≥ 96% | Se ficar ~49%, o colapso é físico (FoV/incidência), não de regra |
| A3 | Reavaliar todos os braços no **domínio do baseline (84%)**, não no do pior braço | Vantagem de `corners4` cai a ≤1 pp ou inverte; braços-3 seguem ~+5 pp piores | Vantagem ≥2 pp mantida refuta meu confundimento |
| F1 | Mesmas 3 vistas transladadas, trocar mediana por **seleção por melhor incidência** (ou peso 1/área-de-pegada) | `translated3_level` cai de +7.88% para ≤ +4.08% mantendo 100% | Se não cair, o viés é de modo comum → o projeto deve atacar o **estimador**, não o arranjo |
| B1 | Vista única com **192/256 raios genuinamente mais densos** (controle ausente) | Vista única densa bate todos os braços-3 no domínio comum | Se perder, multi-vista se justifica neste orçamento |

**Se A1, A3, F1 e B1 passarem**, o candidato físico é **3 sensores transladados, nivelados (paralelos), base ≈ altura típica do monte, eixo longo da caixa** — porque: 100% de visibilidade do oráculo; maior suporte realizado (96.5%); menor otimismo do oráculo (3.5 pp); **nenhuma regressão de validade** (4/9, igual ao baseline); e seu modo de falha (+7.88%) é atribuído à regra de fusão, corrigível em software. `translated3_aimed` é vice-líder (5.78% comum, 96.0% suporte) e preferível se a mira for mecanicamente gratuita — mas adiciona carga de calibração e concentra ganho no centro.

**Rejeitar explicitamente:** multi-vista de centro fixo (`center_tilt3`, `center_angles4`), por impossibilidade geométrica de recuperar oclusão, com custo de erro medido.

**Critério de sucesso do teste físico, declarado a priori:** erro ≤ baseline no **domínio do baseline** (não no comum), suporte por união ≥ 90%, validade ≥ 4/9, em ≥3 geometrias de monte distintas.

---

## 5. Limitações

1. **Nenhum artefato foi lido.** Toda a auditoria de código é uma lista de checagens, não um achado verificado. Qualquer afirmação minha pode cair ao abrir `m001_estimator.py`.
2. **Sem dados por cena**, sem IQR/min/max, sem semente ou família de cenas. A análise por cena pedida não foi possível.
3. **n efetivo ≤ 4** para a métrica primária (4/9 válidos); 9 cenas não sustentam inferência estável; medianas de 9 cenas **não são prova de hardware**.
4. **Simulador pinhole ideal**: sem resposta finita de zona, histogramas, distorção, ruído ou calibração. Erros reais de multi-vista (extrínsecas, sincronização, deriva térmica) são exatamente os que punem arranjos transladados e estão ausentes — o viés do experimento favorece multi-vista mais do que a realidade favoreceria.
5. **`suporte TIN` ≠ área observada** e **oráculo ≠ modelo de sensor** (ignora FoV/orientação); ambos os limites já se manifestam na lacuna de 51 pp do braço de cantos.
6. Definição do erro relativo (sobre qual quantidade integrada) não foi verificada; o viés positivo universal é interpretado, não demonstrado.
7. A1–A4/F1/B1 são hipóteses minhas; se `comparisons.csv` mostrar que os 4 válidos são cenas *diferentes* entre braços, boa parte da minha leitura precisa ser refeita.
