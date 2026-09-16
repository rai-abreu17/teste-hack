## 1. O que os mapas sustentam

**Empate metrológico.** As 5 variantes produzem o mesmo placar: 2/9 dentro de 5%, 2/9 acima, 5/9 indefinidos. Nenhum critério separa mediana fixed de trim2 lower aimed no nível de cena. Diferenças pontuais (center 17,499% → 15,646%; ramp 10,808% → 10,909%) são de sinal inconsistente e não reduzem o gap até 5%.

**Correlação espacial ≠ causa.** A banda transição/sombra concentra ~84–92% do erro em 14–35% da área (11–31x densidade). Isso é consistente com causa de aresta, mas também com colocação de massa: em two_stacks a banda contém 100% da verdade, tornando a concentração tautológica. A banda é definida *por construção* a partir de arestas verdadeiras e de um teste de sombra parcial (segmento centro→AABB, sem LoS/auto-oclusão), logo é uma anotação, não um mecanismo medido.

**Evidência negativa útil.** Em h=0,075 m: FoV ideal 324/400, bins ocupados 64 (fixed) / 136 (aimed), TIN 256/400 em ambos. Aimed zera a sombra comum de viga e mesmo assim o TIN permanece incompleto e idêntico. Isto falsifica a oclusão como explicação suficiente da cobertura ausente e aponta a perda entre FoV→bins→TIN (densidade amostral, agregação, suporte de triangulação) como suspeito principal — ainda não provado.

## 2. Não há candidato único defensável para R007

Escolher agora seria selecionar por 4 cenas definidas e por domínio parcial em mapas espaciais. Recomendo **não abrir R007 de candidato**; abrir primeiro um desenvolvimento de decomposição.

## 3. Próximo passo falsificável (pré-registrar antes de rodar)

**D1 — Ablação por estágio, protocolo R006 congelado, mesmos hashes de frame.**
- *Braço A (oráculo de amostragem):* injetar alturas verdadeiras nas mesmas posições/células amostradas, mantendo binning+TIN+integração idênticos. Isola erro de interpolação/suporte.
- *Braço B (oráculo de reconstrução):* integrar as amostras medidas contra referência exata, sem TIN. Isola erro de aquisição/amostragem.

**Predições que matam hipóteses:**
- Se A reduzir pyramid_center e ramp para <5% (ou <1/3 do erro atual), a interpolação domina; aquisição sai do caminho crítico.
- Se A permanecer >10%, interpolação **não** é dominante — a hipótese de banda cai e o trabalho vai para amostragem/geometria.
- *Contrafactual de banda:* substituir só a banda de 0,015 m por verdade. Se center não cair abaixo de ~5%, o erro é distribuído, não de aresta. **Excluir two_stacks deste teste** (100% de verdade na banda ⇒ não informativo); declarar a exclusão antes de medir.

**Condições de utilidade:** resultado só conta se pré-registrado, com critério numérico fixo, sem reajuste às nove cenas, e replicável nos 54 frames e 18000 registros já hasheados.

## 4. Bloqueio a resolver antes

5/9 cenas têm |Vest−Vtrue|/Vtrue indefinido. Peça ao usuário um critério para volume verdadeiro nulo/parcial (ex.: tolerância absoluta em litros — 2,43 L sem suporte é ordem de grandeza relevante). Decidir entre 5 métodos com 4 cenas é vazio. Intervalo de atualização segue não especificado; não o estou inventando nem tratando como requisito.

## 5. Aquisição, se for buscada

"Sensor mais alto amplia footprint" é hipótese não medida e pertence ao braço B, avaliada em cenas que não a geraram. Não alego resultado de aquisição, física externa, nem uso de arquivos.
