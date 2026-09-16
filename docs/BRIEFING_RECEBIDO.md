# BoxFlow — Briefing técnico e plano de execução

**Data:** 13/09/2026 · **Escopo:** MVP de medição de volume por sensor ToF multizona, em maquete de bancada
**Para quem continuar o trabalho** — este documento é autossuficiente. Não depende de nenhuma conversa anterior.

---

## 0. Resumo em uma página

**O que existe e funciona.** Um pacote completo e verificado: mock geométrico do sensor rodando como custom chip no Wokwi (WASM compilado), firmware ESP32 com protocolo I²C próprio e CRC, receptor HTTP em Python puro com SQLite, dashboard, 24 testes automatizados. Tudo foi executado de forma independente: os 24 testes passam, o WASM roda, os volumes das 17 amostras reproduzem dígito a dígito, o dashboard renderiza no navegador.

**O que está quebrado.** A estimativa de volume erra **+17,50%** na cena principal. Pior: o erro **não é estável**. Deslocar a pilha 2 cm faz o erro variar de **+1,39% a +17,50%**. Mudar a altura do sensor de 30 para 36 cm faz variar de **+2,42% a +18,36%**. A cobertura é quantizada e salta entre 49%, 64%, 81% e 100%, trocando "parcial" por "válida" com milímetros de diferença.

**A descoberta.** O erro não é ruído nem bug: é **aliasing entre a grade de 64 zonas e as bordas do objeto**, com superestimação sistemática causada por *mixed pixels* nas descontinuidades de profundidade. Ambos os fenômenos têm teoria estabelecida e mitigação conhecida. Não estavam sendo tratados.

**O que ainda não foi resolvido.** A mitigação. Sabemos a causa e sabemos o que a indústria faz; falta implementar e medir.

**O erro de leitura mais perigoso deste projeto:** a mediana do erro na varredura de posição já é **+6,78%**. O problema real não é a magnitude — é a **dispersão de 16 pontos percentuais**. Um sistema com viés conhecido e estável se calibra; um sistema cujo erro você não consegue prever, não. **O alvo da próxima etapa é colapsar a dispersão, não perseguir um número bonito.**

---

## 1. Configuração atual

| Item | Valor |
| --- | --- |
| Sensor | VL53L5CX — ToF multizona 8×8, ST |
| Microcontrolador | ESP32 clássico, firmware Arduino/C++ |
| Cena | Maquete de bancada, piso 30 × 30 cm, paredes de 15 cm, frente aberta |
| Bases inclinadas | 1 cm de largura e altura, nas laterais |
| Sensor | Centralizado, apontado para baixo, a 40 cm do piso |
| Pilha de referência | Pirâmide de base 15 × 15 cm, alturas 2,5 / 5 / 7,5 / 10 cm |
| Cena principal | Pirâmide de 7,5 cm → **0,5625 L** (0,0005625 m³) por fórmula analítica |

### Óptica — esta parte está resolvida

A ST especifica o FoV do VL53L5CX **por lado: 45° × 45°** (os 65° citados são a diagonal) — [AN5894](https://www.st.com/resource/en/application_note/an5894-description-of-the-fields-of-view-of-stmicroelectronics-timeofflight-sensors-stmicroelectronics.pdf). Com o sensor a 40 cm:

- campo no piso: **33,1 × 33,1 cm** (cobre a maquete de 30 cm)
- zona central no piso: **3,94 cm**
- raio de canto: 26,8° fora do eixo, distância percorrida **448 mm**

Os limites do datasheet em 8×8 sob 5 klx são 1000 mm (branco 88%, canto) e 650 mm (cinza 17%, canto). Com 448 mm há folga confortável **mesmo com material escuro sob luz forte**. A redução de escala resolveu o problema óptico. O gargalo agora é inteiramente numérico.

---

## 2. O problema, medido

Todos os números abaixo foram obtidos executando o pacote atual. São reproduzíveis.

### 2.1 Varredura de posição da pilha (sensor fixo a 40 cm)

| Centro da pilha | Erro | | Centro | Erro |
| ---: | ---: | --- | ---: | ---: |
| 13,0 cm | +1,86% | | 15,2 cm | +15,85% |
| 13,4 cm | **+1,39%** | | 15,6 cm | +10,30% |
| 13,8 cm | +3,44% | | 16,0 cm | +5,20% |
| 14,2 cm | +8,02% | | 16,4 cm | +1,97% |
| 14,6 cm | +12,53% | | 16,6 cm | **+1,39%** |
| **15,0 cm** | **+17,50%** | | 17,0 cm | +1,86% |

Faixa: **+1,39% a +17,50%**. Mediana +6,78%, desvio 5,35 pontos. Curva simétrica em torno de 15,0 cm.

**A cena da demonstração está exatamente no pico.** O sensor fica sobre o ápice, e as quatro bordas da pirâmide caem simetricamente entre fronteiras de zona — a pior configuração possível. Foi coincidência, não escolha.

### 2.2 Varredura de altura do sensor (pilha fixa no centro)

| z | Campo | Zona | Erro | Cobertura |
| ---: | ---: | ---: | ---: | ---: |
| 28 cm | 23,2 cm | 2,90 cm | +2,95% | 49% |
| 30 cm | 24,9 cm | 3,11 cm | +2,42% | 49% |
| 33 cm | 27,3 cm | 3,42 cm | +10,26% | 64% |
| 36 cm | 29,8 cm | 3,73 cm | +18,36% | 81% |
| 40 cm | 33,1 cm | 3,94 cm | +17,50% | 100% |
| 45 cm | 37,3 cm | 4,66 cm | +6,38% | 64% |
| 50 cm | 41,4 cm | 5,18 cm | −2,94% | 81% |

Não é monotônico. Não é físico. É alinhamento.

### 2.3 Cobertura é quantizada

Ela só assume 49%, 64%, 81% ou 100% — (7/10)², (8/10)², (9/10)², (10/10)². O TIN cobre uma região quadrada e a grade de 1,5 cm conta células inteiras. Na cena de camada, subir o sensor de 40 para 45 cm troca "parcial, −36%" por "válida, −0,87%". **Milímetros decidem entre publicar e não publicar um total.**

### 2.4 Sensibilidade à referência do vazio

A altura média da pirâmide sobre o piso é **6,25 mm**. Como o erro de referência entra como área × desvio:

| Desvio da referência | Volume estimado | Erro |
| ---: | ---: | ---: |
| −10 mm | 1,5574 L | +177% |
| 0 | 0,6609 L | +17,5% |
| +10 mm | indisponível (cobertura 16%) | — |

**1 mm de erro de referência = 0,09 L = 16% do volume da cena.** No box industrial de 8 × 6 m o mesmo milímetro valia 0,8%. Encolher a maquete melhorou a óptica e **piorou a metrologia** — porque volume escala com L³ e o erro de referência escala com L².

### 2.5 Duas hipóteses já testadas e descartadas

**Integração por footprint de zona** (área projetada de cada zona × altura medida, em vez de TIN + grade): **pior em todas as cenas** — +25,63% contra +17,50% na principal. A integração em grade horizontal do pacote atual já trata corretamente o peso de área. Não refazer.

**Múltiplas vistas**: ajuda menos do que se esperaria. 2 vistas → +15,77%. 4 vistas em quadrado → +16,42%. 9 vistas → **+5,97%**. O erro não vem principalmente de oclusão.

---

## 3. Por que isso acontece — a teoria

### 3.1 Mixed pixel / flying pixel

Quando um elemento do sensor recebe luz do objeto e do fundo simultaneamente, a profundidade retornada é uma mistura. Ocorre em descontinuidades de profundidade — exatamente a borda da pilha. Formalizado em [Vasudevan et al., arXiv:2410.08084](https://arxiv.org/html/2410.08084v1): *"FPs are incorrect depth measurements occurring when light from both a foreground and background object is processed by the same sensor pixel."*

A literatura documenta também a **direção** do erro. [Aerospace 12(3):189](https://www.mdpi.com/2226-4310/12/3/189) atribui erro volumétrico a *"a wider FOV sensor, which makes it difficult to reconstruct sharp edges, **leading to an increase in the estimated volume**"*. Superestimação — o que medimos.

**Mecanismo no nosso caso:** um raio que passa raspando a pilha cai no piso muito além dela. O TIN liga esse ponto do piso ao ponto vizinho na encosta, criando uma rampa fantasma que adiciona volume onde não há material. A banda de erro tem a largura de uma zona ao longo de **todo o perímetro** do objeto.

**Por que é tão grande aqui:** o perímetro da pirâmide é 60 cm; a zona mede 3,94 cm. A área da banda de borda é ~0,024 m², contra 0,0225 m² da base da pirâmide inteira. **A banda de erro é maior que o próprio objeto.**

### 3.2 Zitterbewegung de Cavalieri

O comportamento oscilatório tem formalização. Na amostragem de Cavalieri, a variância do estimador de volume decompõe-se em um termo de extensão, um termo oscilante chamado **Zitterbewegung** — que depende da posição da grade de amostragem relativamente às fronteiras do objeto — e termos de ordem superior ([García-Fiñana & Cruz-Orive, *Image Analysis and Stereology* 19:71–79](https://www.ias-iss.org/ojs/IAS/article/view/626)).

O termo oscilante é desprezível para objetos lisos e **passa a dominar quando a função de medida tem derivadas descontínuas** — quinas, arestas, a transição pilha/piso. É precisamente o nosso caso, e é precisamente o que a varredura de posição mostrou.

**Consequência prática:** qualquer número único de erro é um artefato da configuração em que foi medido.

### 3.3 Pilhas pequenas são o pior caso — universalmente

A revisão [Drones 7(8):537](https://www.mdpi.com/2504-446X/7/8/537) reporta fotogrametria por drone com 0–3% típico, **mas até 23% para pilhas menores que 1 m³**, e o achado transversal: *"smaller surface–volume ratios led to more accurate volume estimations."* O erro percentual é inversamente proporcional à altura da pilha.

Nossa maquete está no regime onde **todo método do mundo** tem erro de dois dígitos. Isso não desculpa o resultado, mas recalibra a expectativa: a meta de 5% não é um patamar trivial que estamos falhando em atingir.

---

## 4. Como a indústria reduz o erro

Levantamento em fabricantes de scanner de silo, volumetria de pátio, scanners em movimento e literatura acadêmica. Resumo do que importa:

**O produto líder opera com ~60 pontos.** O 3DLevelScanner (BinMaster / Rosemount 5708, todos derivados da APM/Emerson) entrega *"data from 60 different points with just one measuring device"*. Temos 64. **Já estamos na mesma classe de densidade de amostragem.** Mais zonas não é a diferença.

**Ninguém reconstrói superfície livre.** A [Blickfeld](https://www.blickfeld.com/applications/volume-monitoring/bulk-solids-measurement/), com LiDAR de milhares de pontos, calcula volume com *"cone-shaped zone definitions"* e *"interpolation and extrapolation where parts of the pile are temporarily hidden"*. A regra clássica de montar o sensor a 1/6 do diâmetro do silo existe porque nessa posição há *"a 1:1 relationship between material volume above and empty space below the measurement point"* — um modelo analítico de cone aplicado a **uma única medida**. Usam prior de forma em todos os níveis de densidade de dados. **Nós, com 64 pontos, estamos usando o estimador mais faminto por dados que existe.**

**O fabricante do nosso sensor descarta as zonas de borda.** A [AN5843 da ST](https://www.st.com/resource/en/application_note/an5843-water-and-liquid-level-measurement-using-vl53l5cx-timeofflight-8x8-multizone-sensor-with-wide-field-of-view-stmicroelectronics.pdf), sobre medição de nível com o VL53L5CX, usa **12 das 64 zonas** — apenas as centrais (19,20,26,27,28,29,34,35,36,37,43,44) — e descarta as externas por serem *"clearly more affected"* por reflexões de parede e da superfície de apoio. Usamos as 64 e interpolamos através justamente das piores.

**Referência é perfil-zero medido, não modelo.** [LASE LaseBVH](https://lase-solutions.com/products/bulk-material/lasebvh): *"During calibration, a so-called 'zero-profile' is generated. During later operation, the 3D image of the stockpile can be compared with this profile."* O [LaseTVM](https://lase-solutions.com/products/bulk-material/lasetvm/lasetvm-3d-s) mede caminhão vazio e cheio e subtrai — ±2%.

**A dimensão barata é o movimento.** O SICK Bulkscan é um telêmetro de ponto único com espelho rotativo; a terceira dimensão vem da velocidade da correia. O [ABB VM3D](https://library.e.abb.com/public/92be71086d0a4d3390c032e1a902531c/DS_VM3D-EN%20Rev%20C.pdf) é um feixe único varrido mecanicamente e entrega *"less than 2% error on volumes greater than 100 m³"*, ao custo de 45 min por varredura. Na academia, LiDAR de ponto único atuado em drone dá **0,8 ± 1,1%**, batendo LiDAR 2D e empatando com 3D ([Drones 6(12):386](https://www.mdpi.com/2504-446X/6/12/386)).

**A cadeia de erro é declarada em três níveis.** Os fabricantes de silo separam: **±15 mm de distância → 3–5% de volume → 5–10% de massa**, contra 8–15% de massa para medição em ponto único. Qualquer alegação nossa precisa dizer em qual nível está.

**A densidade domina a conversão para tonelada.** Mudar a densidade assumida de 1,60 para 1,55 t/m³ numa pilha de 50.000 m³ move **2.500 toneladas — 3,1% a partir de uma única suposição** ([Birdi](https://www.birdi.io/blog-post/how-to-reconcile-stockpile-volumes-a-step-by-step-guide-for-mine-and-quarry-operators)). Balanças de correia certificadas entregam ±0,125% a ±0,5% medindo massa diretamente. **Se a operação decide em toneladas, vale perguntar qual decisão a medida sustenta antes de perseguir precisão volumétrica.**

**Ângulo de repouso com forma restrita.** Literatura de 2025: `tan θc = H/b₀` liga altura ao raio da base; volume por fórmula fechada **sem medir altura**. 95% de acurácia em instalação real a partir de **uma única imagem** ([arXiv:2505.17896](https://arxiv.org/html/2505.17896v1)); 13,7% de superestimação por imagem de satélite ([arXiv:2509.13890](https://arxiv.org/html/2509.13890v1)). Troca dezenas de pontos por **um parâmetro de material**.

---

## 5. Plano de execução

Ordenado por custo. As três primeiras rodam hoje, com as amostras que já existem, sem hardware e sem Wokwi.

### Protocolo obrigatório de avaliação

**Nenhum experimento é avaliado por um número único.** Toda hipótese é medida por uma varredura de posição da pilha de 13,0 a 17,0 cm em passos de 2 mm, reportando:

- **viés** (mediana do erro) — é calibrável
- **dispersão** (amplitude e desvio padrão) — **não** é calibrável e é o alvo principal
- **estabilidade da cobertura** (quantos pontos da varredura mudam de estado)

Linha de base atual: viés **+6,78%**, dispersão **16,1 pontos** (de +1,39% a +17,50%), desvio 5,35.

Construir esse arnês de varredura é a **tarefa zero**. Sem ele, nenhum resultado abaixo significa nada.

---

### E1 — Descartar zonas de borda

**Hipótese:** a maior parte do erro está nas zonas externas, que contêm as bordas do objeto e sofrem reflexão de parede. É o que a ST faz na AN5843.

**Fazer:** recalcular todas as amostras usando apenas as zonas centrais 6×6, depois 4×4. Comparar a área efetivamente medida (o campo encolhe) e renormalizar a comparação — atenção para não comparar volume de regiões diferentes.

**Critério:** dispersão cai abaixo de 8 pontos.

**Decisão:** se cair muito, a borda é o problema dominante e E2 vira prioridade. Se não cair, o problema está no estimador inteiro e E3 assume.

**Custo:** minutos. Uma linha de filtro.

---

### E2 — Filtro de descontinuidade por gradiente

**Hipótese:** o bridging entre encosta e piso cria volume fantasma. O `MAX_EDGE_M` atual corta por comprimento de aresta 3D (10 cm), critério fraco.

**Fazer:** substituir por limiar de **ângulo de incidência entre pontos vizinhos** — a taxonomia de erros ToF em [Sensors 17(1):92](https://www.mdpi.com/1424-8220/17/1/92) usa exatamente isso. Triângulo cujo gradiente vertical excede o ângulo de repouso plausível do material é descartado, não interpolado. A região vira desconhecida.

**Critério:** dispersão < 8 pontos **e** o viés muda de sinal ou some. Atenção: isso vai derrubar a cobertura — é o trade-off correto, e o pacote já sabe reportar "parcial" honestamente.

**Custo:** uma tarde.

---

### E3 — Ajuste paramétrico com ângulo de repouso

**Hipótese:** com 64 pontos, ajustar 3–4 parâmetros de uma forma fisicamente restrita bate reconstruir uma superfície livre com 64 graus de liberdade.

**Fazer:** ajustar cone/pirâmide (centro, base, altura, θ de repouso) aos pontos válidos por mínimos quadrados. Volume por fórmula fechada. Comparar com o TIN na mesma varredura.

**Critério:** dispersão < 5 pontos. A literatura sugere erro de 5–20% — pode ter **viés maior** que o TIN e **dispersão muito menor**, o que é preferível: viés se calibra.

**Ressalva importante:** só vale para material granular que forma pilha com ângulo característico. Não generaliza para carga em blocos ou lonas. Documentar a hipótese de aplicabilidade.

**Custo:** um a dois dias.

---

### E4 — Perfil-zero medido

**Hipótese:** capturar a referência do vazio com o próprio sensor, na mesma pose, cancela o erro comum de pose e calibração. Precedente comercial: LASE.

**Fazer:** no pipeline, substituir a referência analítica `base(x,y)` por uma média de N varreduras do piso vazio. Na simulação, injetar erro de pose e verificar que a subtração o elimina.

**Critério:** o teste de sensibilidade à referência deixa de mostrar 16% por milímetro, passando a depender só da deriva entre as duas capturas.

**Custo:** meio dia. **Alto retorno — este é o único termo de erro que hoje é catastrófico.**

---

### E5 — Fechar o caminho ponta a ponta

**Nunca foi executado.** Todos os testes HTTP usaram o emissor nativo em C (`native-c-test`), não o firmware. A tentativa no editor Wokwi foi interrompida.

**Fazer:** rodar ESP32 emulado → gateway → receptor → dashboard, com o mock atualizado. O gateway público **não** alcança `127.0.0.1`: ou usar gateway privado (plano pago do Wokwi), ou publicar o receptor em endereço acessível.

**Critério:** ver no serial `Varredura N: 64 raios, ... CRC OK` e HTTP 200, com `transport: wokwi-esp32` no painel.

**Custo:** algumas horas, mais o gateway. **É o que a apresentação precisa mostrar.**

---

### E6 — Varredura por servo (opcional, se sobrar tempo)

**Hipótese:** movimento é a dimensão barata. Um VL53L5CX num servo varrendo a cena multiplica a cobertura por poucos reais.

**Fazer:** N poses angulares, fundindo as nuvens. É o que ABB VM3D e SICK Bulkscan fazem.

**Ressalva:** o teste de múltiplas vistas deu ganho modesto (9 vistas → +5,97%), então **este não é o caminho principal**. Só faz sentido depois de E2 e E3, porque varrer mais não corrige erro de borda — só o distribui.

---

## 6. Regras de conduta

1. **Nunca reportar um número único de erro.** Sempre viés, dispersão e faixa da varredura.
2. **Nunca ajustar posição, altura ou parâmetro até o número ficar bom.** Isso é calibrar contra o alias, e a banca não distingue de precisão real. Se uma configuração for escolhida, a escolha precisa ser justificada antes de ver o resultado.
3. **O estimador não pode receber `fill`, forma, centro da pilha nem volume analítico.** Só o quadro, a pose e a referência. Isso está correto no pacote atual — preservar.
4. **Ausência de leitura nunca vira volume zero.** Região sem observação permanece desconhecida; se a observação não sustenta um volume utilizável, o resultado é inconclusivo.
5. **Separar os três níveis de erro:** distância (mm), volume (%), massa (%). Não misturar.
6. **Manter o rótulo de dados simulados** em toda a interface enquanto não houver hardware.
7. **Registrar o que não foi executado**, como o pacote atual já faz. Essa honestidade é o que torna o trabalho defensável.

---

## 7. O que significa "resolvido"

**Meta principal:** dispersão do erro abaixo de **5 pontos percentuais** na varredura de posição, com viés declarado e estável. Um sistema que erra consistentemente +8% é utilizável — calibra-se. Um que erra entre +1% e +18% conforme onde a pilha caiu, não é.

**Meta secundária:** viés mediano ≤ 10% após calibração do fator sistemático.

**Meta de demonstração:** caminho ESP32 → API → dashboard rodando ao vivo, com uma cena de falha (zonas inválidas, publicação interrompida) mostrando tratamento honesto.

**Fora de escopo, e dizer isso explicitamente:** precisão em hardware real, comportamento com poeira, conversão para toneladas, validação industrial. A simulação não sustenta nenhuma dessas afirmações.

---

## 8. Lacuna de pesquisa

A busca não encontrou: nenhum artigo usando VL53L5CX para volume de granel; nenhuma curva publicada de "número de zonas × erro de volume" para ToF multizona; nenhuma demonstração empírica do aliasing grade/borda em volumetria — apesar de a teoria de Cavalieri existir e ser sólida.

A varredura descrita na seção 5 é, portanto, mais que um procedimento interno: é um resultado que ninguém publicou. Vale documentá-la com rigor.

---

## 9. Fontes

**Sensor e fabricante**
[Datasheet VL53L5CX](https://www.st.com/resource/en/datasheet/vl53l5cx.pdf) ·
[AN5894 — campos de visão](https://www.st.com/resource/en/application_note/an5894-description-of-the-fields-of-view-of-stmicroelectronics-timeofflight-sensors-stmicroelectronics.pdf) ·
[AN5843 — nível de líquido, descarte de zonas](https://www.st.com/resource/en/application_note/an5843-water-and-liquid-level-measurement-using-vl53l5cx-timeofflight-8x8-multizone-sensor-with-wide-field-of-view-stmicroelectronics.pdf) ·
[Biblioteca SparkFun](https://github.com/sparkfun/SparkFun_VL53L5CX_Arduino_Library)

**Teoria do erro**
[Zitterbewegung de Cavalieri — García-Fiñana & Cruz-Orive](https://www.ias-iss.org/ojs/IAS/article/view/626) ·
[Mixed/flying pixels — arXiv:2410.08084](https://arxiv.org/html/2410.08084v1) ·
[Superestimação por borda — Aerospace 12(3):189](https://www.mdpi.com/2226-4310/12/3/189) ·
[Taxonomia de erros ToF — Sensors 17(1):92](https://www.mdpi.com/1424-8220/17/1/92) ·
[Caracterização do VL53L5CX — Sensors 26(5):1639](https://www.mdpi.com/1424-8220/26/5/1639)

**Estado da arte industrial**
[BinMaster 3DLevelScanner](https://binmaster.com/3d-details/) ·
[BinMaster — precisão](https://binmaster.com/news/understanding-accuracy.html) ·
[Patente APM US20140208845](https://patents.justia.com/patent/20140208845) ·
[Blickfeld — granel](https://www.blickfeld.com/applications/volume-monitoring/bulk-solids-measurement/) ·
[LASE LaseBVH — perfil-zero](https://lase-solutions.com/products/bulk-material/lasebvh) ·
[LASE LaseTVM — diferencial](https://lase-solutions.com/products/bulk-material/lasetvm/lasetvm-3d-s) ·
[ABB VM3D — feixe único varrido](https://library.e.abb.com/public/92be71086d0a4d3390c032e1a902531c/DS_VM3D-EN%20Rev%20C.pdf) ·
[SICK Bulkscan](https://www.sick.com/media/docs/3/23/823/operating_instructions_bulkscan_en_im0045823.pdf)

**Volumetria e reconciliação**
[Revisão — Drones 7(8):537](https://www.mdpi.com/2504-446X/7/8/537) ·
[LiDAR ponto único atuado — Drones 6(12):386](https://www.mdpi.com/2504-446X/6/12/386) ·
[Ângulo de repouso — arXiv:2505.17896](https://arxiv.org/html/2505.17896v1) ·
[Validação ângulo de repouso — arXiv:2509.13890](https://arxiv.org/html/2509.13890v1) ·
[Propeller — erro da base domina](https://www.propelleraero.com/blog/how-accurate-is-drone-stockpile-measurement/) ·
[Birdi — reconciliação e densidade](https://www.birdi.io/blog-post/how-to-reconcile-stockpile-volumes-a-step-by-step-guide-for-mine-and-quarry-operators) ·
[Thayer Scale — balanças de correia](https://www.thayerscale.com/conveyor-belt-scale-accuracy-engineering-guide/)

---

## Anexo — reprodução dos experimentos

O pacote atual traz `tools/scene_dump.c`, que aceita `fill shape center_x obstacle dropout range seq yaw tilt origin_z`. **Para as varreduras de multivista foi necessário estendê-lo** com dois argumentos adicionais, `origin_x` e `origin_y`, inserindo após a linha do `origin.z`:

```c
if(argc>11)s.origin.x=strtof(argv[11],NULL);
if(argc>12)s.origin.y=strtof(argv[12],NULL);
```

A varredura de posição usa `center_x` de 0,13 a 0,17 em passos de 0,002, com o estimador em `server/geometry.py` chamado via `estimate(raw)`. O envelope de pose aceito pelo estimador é x,y ∈ [0,05; 0,25] e z ∈ [0,2; 0,6]; `center_x` é limitado em [0,10; 0,20] pelo próprio chip.
