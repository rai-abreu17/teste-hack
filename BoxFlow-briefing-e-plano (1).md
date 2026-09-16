# BoxFlow — Briefing técnico e plano de execução

**Atualizado:** 13/09/2026 · **Escopo:** MVP de medição de volume por sensor ToF multizona, em maquete de bancada
**Para quem continuar o trabalho** — este documento é autossuficiente. Não depende de nenhuma conversa anterior.

---

## 0. Resumo em uma página

**O que existe e funciona.** Um pacote completo e verificado: mock geométrico do sensor rodando como custom chip no Wokwi (WASM compilado), firmware ESP32 com protocolo I²C próprio e CRC, receptor HTTP em Python puro com SQLite, dashboard, 24 testes automatizados. Tudo foi executado de forma independente: os 24 testes passam, o WASM roda, os volumes das 17 amostras reproduzem dígito a dígito, o dashboard renderiza no navegador.

**O que estava quebrado.** A estimativa de volume errava **+17,50%** na cena principal, com o problema real sendo a **instabilidade**: deslocar a pilha 2 cm fazia o erro variar de **+1,39% a +17,50%**; mudar a altura do sensor de 30 para 36 cm variava de **+2,42% a +18,36%**. A cobertura era quantizada, saltando entre 49/64/81/100% com milímetros de diferença.

**A causa.** Não é ruído nem bug: é **aliasing entre a grade de 64 zonas e as bordas do objeto** (formalizado como *Zitterbewegung* na teoria de amostragem de Cavalieri), com superestimação sistemática por *mixed pixels* nas descontinuidades de profundidade.

**A descoberta desta rodada — existe mitigação, e ela é barata.** Testamos a proposta do usuário de montar o sensor num suporte móvel (pan-tilt). O mecanismo **não** funciona pela razão intuitiva (reduzir ponto cego) — funciona por **anti-aliasing**: tirar N leituras com a grade angularmente deslocada (dithering) e mediar colapsa o termo oscilante. Resultado medido:

| Configuração | Dispersão na varredura de posição |
| --- | ---: |
| 1 pose (estado anterior) | 14,5–16,1 pts |
| 3 poses uniformes | 1,2 pts |
| **6 poses uniformes** | **0,4 pts** |

Isso **ultrapassa** a meta que tínhamos estabelecido (dispersão < 5 pts). Mas vem com uma condição rígida: **o erro de posicionamento do atuador precisa ficar abaixo de ~0,25°**, e a distinção entre *exatidão* (calibrável) e *repetibilidade* (não calibrável) do atuador é o que decide se isso é viável ou não em hardware — ver seção 5.

**O que ainda não foi resolvido.** Implementar isso em hardware real, e provar — com metodologia reconhecida, não só um número — que o resultado é confiável. Esta rodada de pesquisa trouxe o método para essa prova (seção 6).

**Nunca perder de vista:** todos os números de dispersão acima vêm de uma simulação com ray-casting ideal, sem ruído óptico, sem física de servo real. Eles provam a **arquitetura**, não a **precisão em hardware**. O plano de execução (seção 7) existe para fechar essa distância com rigor, não para assumi-la fechada.

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
| Proposta em avaliação | Suporte móvel (pan-tilt) para dithering angular — ver seção 5 |

### Óptica — esta parte está resolvida

A ST especifica o FoV do VL53L5CX **por lado: 45° × 45°** (os 65° citados são a diagonal) — [AN5894](https://www.st.com/resource/en/application_note/an5894-description-of-the-fields-of-view-of-stmicroelectronics-timeofflight-sensors-stmicroelectronics.pdf). Com o sensor a 40 cm:

- campo no piso: **33,1 × 33,1 cm** (cobre a maquete de 30 cm)
- zona central no piso: **3,94 cm**
- raio de canto: 26,8° fora do eixo, distância percorrida **448 mm**

Os limites do datasheet em 8×8 sob 5 klx são 1000 mm (branco 88%, canto) e 650 mm (cinza 17%, canto). Com 448 mm há folga confortável **mesmo com material escuro sob luz forte**. A redução de escala resolveu o problema óptico. O gargalo é o aliasing de amostragem — não a óptica, e (com a descoberta da seção 5) não mais o algoritmo de integração sozinho.

---

## 2. O problema, medido

Todos os números abaixo foram obtidos executando o pacote atual, com uma única pose fixa do sensor. São reproduzíveis.

### 2.1 Varredura de posição da pilha (sensor fixo a 40 cm, 1 pose)

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

### 2.2 Varredura de altura do sensor (pilha fixa no centro, 1 pose)

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

### 2.5 Hipóteses já testadas e descartadas (não refazer)

**Integração por footprint de zona** (área projetada de cada zona × altura medida, em vez de TIN + grade): **pior em todas as cenas** — +25,63% contra +17,50% na principal. A integração em grade horizontal do pacote atual já trata corretamente o peso de área.

**Múltiplas vistas por *translação*, sem dithering angular controlado**: ajuda menos do que se esperaria. 2 vistas → +15,77%. 4 vistas em quadrado → +16,42%. 9 vistas → +5,97%. Isso não contradiz a seção 5 — a diferença é que ali as poses foram desenhadas para varrer a fase da grade, e aqui eram só reposicionamentos ad hoc.

**Estimar a pose a partir do piso conhecido**, em vez de confiar no ângulo comandado (uma tentativa de contornar erro de servo por software): implementação simples **piorou** o resultado em vez de melhorar. Fica registrado como linha de pesquisa em aberto, não como solução pronta.

---

## 3. Por que isso acontece — a teoria

### 3.1 Mixed pixel / flying pixel

Quando um elemento do sensor recebe luz do objeto e do fundo simultaneamente, a profundidade retornada é uma mistura. Ocorre em descontinuidades de profundidade — exatamente a borda da pilha. Formalizado em [Vasudevan et al., arXiv:2410.08084](https://arxiv.org/html/2410.08084v1): *"FPs are incorrect depth measurements occurring when light from both a foreground and background object is processed by the same sensor pixel."*

A literatura documenta também a **direção** do erro. [Aerospace 12(3):189](https://www.mdpi.com/2226-4310/12/3/189) atribui erro volumétrico a *"a wider FOV sensor, which makes it difficult to reconstruct sharp edges, **leading to an increase in the estimated volume**"*. Superestimação — o que medimos.

**Mecanismo no nosso caso:** um raio que passa raspando a pilha cai no piso muito além dela. O TIN liga esse ponto do piso ao ponto vizinho na encosta, criando uma rampa fantasma que adiciona volume onde não há material. A banda de erro tem a largura de uma zona ao longo de **todo o perímetro** do objeto.

**Por que é tão grande aqui:** o perímetro da pirâmide é 60 cm; a zona mede 3,94 cm. A área da banda de borda é ~0,024 m², contra 0,0225 m² da base da pirâmide inteira. **A banda de erro é maior que o próprio objeto.**

### 3.2 Zitterbewegung de Cavalieri — e por que o dithering funciona

O comportamento oscilatório tem formalização. Na amostragem de Cavalieri, a variância do estimador de volume decompõe-se em um termo de extensão, um termo oscilante chamado **Zitterbewegung** — que depende da posição da grade de amostragem relativamente às fronteiras do objeto — e termos de ordem superior ([García-Fiñana & Cruz-Orive, *Image Analysis and Stereology* 19:71–79](https://www.ias-iss.org/ojs/IAS/article/view/626)).

O termo oscilante é desprezível para objetos lisos e **passa a dominar quando a função de medida tem derivadas descontínuas** — quinas, arestas, a transição pilha/piso. É precisamente o nosso caso, e é precisamente o que a varredura de posição mostrou.

**Isso também explica por que o dithering funciona e por que translação sozinha ajuda pouco (2.5).** O termo Zitterbewegung é periódico na fase da grade em relação ao objeto. Amostrar em N fases uniformemente distribuídas dentro de um período (o passo de zona) e mediar cancela esse termo por construção — é a mesma matemática por trás de técnicas de anti-aliasing em imagem e de *dithering* em processamento de sinais. Translação desloca a *posição* do objeto na grade sem necessariamente cobrir fases uniformes; rotação em torno do centro óptico faz exatamente isso, de forma controlada.

### 3.3 Pilhas pequenas são o pior caso — universalmente

A revisão [Drones 7(8):537](https://www.mdpi.com/2504-446X/7/8/537) reporta fotogrametria por drone com 0–3% típico, **mas até 23% para pilhas menores que 1 m³**, e o achado transversal: *"smaller surface–volume ratios led to more accurate volume estimations."* O erro percentual é inversamente proporcional à altura da pilha.

Nossa maquete está no regime onde **todo método do mundo** tem erro de dois dígitos. Isso não desculpa o resultado, mas recalibra a expectativa: a meta de 5% não é um patamar trivial que estamos falhando em atingir.

---

## 4. Como a indústria e a academia atacam isso

### 4.1 Scanners e volumetria industrial

**O produto líder opera com ~60 pontos.** O 3DLevelScanner (BinMaster / Rosemount 5708, todos derivados da APM/Emerson) entrega *"data from 60 different points with just one measuring device"*. Temos 64. **Já estamos na mesma classe de densidade de amostragem.** Mais zonas não é a diferença.

**Ninguém reconstrói superfície livre.** A [Blickfeld](https://www.blickfeld.com/applications/volume-monitoring/bulk-solids-measurement/), com LiDAR de milhares de pontos, calcula volume com *"cone-shaped zone definitions"* e *"interpolation and extrapolation where parts of the pile are temporarily hidden"*. A regra clássica de montar o sensor a 1/6 do diâmetro do silo existe porque nessa posição há *"a 1:1 relationship between material volume above and empty space below the measurement point"* — um modelo analítico de cone aplicado a **uma única medida**. Usam prior de forma em todos os níveis de densidade de dados.

**O fabricante do nosso sensor descarta as zonas de borda.** A [AN5843 da ST](https://www.st.com/resource/en/application_note/an5843-water-and-liquid-level-measurement-using-vl53l5cx-timeofflight-8x8-multizone-sensor-with-wide-field-of-view-stmicroelectronics.pdf), sobre medição de nível com o VL53L5CX, usa **12 das 64 zonas** — apenas as centrais (19,20,26,27,28,29,34,35,36,37,43,44) — e descarta as externas por serem *"clearly more affected"* por reflexões de parede e da superfície de apoio.

**Referência é perfil-zero medido, não modelo.** [LASE LaseBVH](https://lase-solutions.com/products/bulk-material/lasebvh): *"During calibration, a so-called 'zero-profile' is generated. During later operation, the 3D image of the stockpile can be compared with this profile."* O [LaseTVM](https://lase-solutions.com/products/bulk-material/lasetvm/lasetvm-3d-s) mede caminhão vazio e cheio e subtrai — ±2%.

**A dimensão barata é o movimento.** O SICK Bulkscan é um telêmetro de ponto único com espelho rotativo; a terceira dimensão vem da velocidade da correia. O [ABB VM3D](https://library.e.abb.com/public/92be71086d0a4d3390c032e1a902531c/DS_VM3D-EN%20Rev%20C.pdf) é um feixe único varrido mecanicamente e entrega *"less than 2% error on volumes greater than 100 m³"*, ao custo de 45 min por varredura. Na academia, LiDAR de ponto único atuado em drone dá **0,8 ± 1,1%** ([Drones 6(12):386](https://www.mdpi.com/2504-446X/6/12/386)).

**A cadeia de erro é declarada em três níveis.** Os fabricantes de silo separam: **±15 mm de distância → 3–5% de volume → 5–10% de massa**. Qualquer alegação nossa precisa dizer em qual nível está. E a densidade domina a conversão para tonelada: mudar a densidade assumida de 1,60 para 1,55 t/m³ numa pilha de 50.000 m³ move **2.500 toneladas — 3,1% a partir de uma única suposição** ([Birdi](https://www.birdi.io/blog-post/how-to-reconcile-stockpile-volumes-a-step-by-step-guide-for-mine-and-quarry-operators)).

**Ângulo de repouso com forma restrita.** `tan θc = H/b₀` liga altura ao raio da base; volume por fórmula fechada **sem medir altura**. 95% de acurácia a partir de **uma única imagem** ([arXiv:2505.17896](https://arxiv.org/html/2505.17896v1)); 13,7% de superestimação por satélite ([arXiv:2509.13890](https://arxiv.org/html/2509.13890v1)).

**Redes de sensores em grade — o análogo acadêmico mais próximo do nosso caso.** [Pozzebon et al., *Measurement* 220:113404 (2023)](https://usiena-air.unisi.it/retrieve/3e554811-070a-4d6d-9acc-d850b5289251/1-s2.0-S0263224123009685-main.pdf) usam de 4 a 6 nós **ultrassônicos** numa grade e somam volumes de subdivisões triangulares — a mesma abordagem geométrica do nosso `geometry.py`. O erro relatado varia de **0,10% a 37,64%** dependendo só de como a superfície cai sobre a grade. É a mesma dispersão por aliasing que medimos na seção 2, documentada de forma independente. Isso não é uma falha do nosso projeto — é uma propriedade da amostragem em grade esparsa.

### 4.2 Visão computacional + ToF: existe, é real, não serve para agora

O trabalho mais direto é **DELTAR** ([ECCV 2022](https://www.ecva.net/papers/eccv_2022/papers_ECCV/papers/136610612.pdf), [código aberto](https://github.com/zju3dv/deltar)) e seu sucessor **CFPNet** ([arXiv:2411.04480](https://arxiv.org/html/2411.04480v1)). A ideia: em vez de usar só a distância média de cada zona do VL53L5CX, usar a **distribuição de profundidade inteira** (o histograma de fótons que o sensor mede internamente) e uma rede neural espalha essa informação sobre uma imagem RGB de alta resolução, produzindo um mapa de profundidade denso.

Funciona (RMSE 0,431 no CFPNet, melhor que ToF puro), mas: **exige GPU** (treino com 4× RTX 2080Ti), a inferência **não é tempo real** (~50 ms só de inferência, sem o resto do pipeline), e o código do CFPNet **ainda não foi liberado** (o DELTAR tem repositório). Nenhum dos dois roda em ESP32.

**Veredicto:** é a tecnologia certa para o problema errado nesta fase. O problema aqui é aliasing em 64 pontos, não falta de densidade de profundidade — trazer uma rede neural para resolver isso é usar uma ferramenta pesada demais para o mecanismo de erro identificado.

### 4.3 Onde a câmera realmente ajuda: como máscara, não como sensor de profundidade

Versão barata da mesma ideia, que ataca diretamente o *mixed pixel* da seção 3.1: uma câmera simples separa **material de piso por cor** (segmentação binária, sem rede neural — o material granular normalmente contrasta com o piso da maquete). Qualquer zona do ToF cuja projeção caia na fronteira dessa máscara é marcada como suspeita e **descartada**, em vez de interpolada — o mesmo princípio da AN5843, só que a decisão de "o que é borda" vem da câmera em vez de uma regra geométrica fixa. Viável com ESP32-CAM ou webcam + limiar de cor, sem GPU.

---

## 5. Suporte móvel (pan-tilt) — resultados medidos

Testamos a proposta do usuário de instalar o sensor num suporte que se move: para cima/baixo, esquerda/direita, e em ângulo. A conclusão central: **funciona, mas por um mecanismo diferente do proposto, e isso muda o projeto mecânico.**

### 5.1 Rotação combate aliasing; translação combate oclusão — não são a mesma coisa

Girar o sensor em torno do próprio centro óptico **não cria nenhum ponto de vista novo** — todos os raios continuam saindo do mesmo ponto no espaço. Se algo está escondido atrás da pilha, continua escondido depois de inclinar o sensor. O que a rotação faz é deslocar a **fase da grade de amostragem** em relação às bordas do objeto (seção 3.2).

| Configuração (varredura de posição, 8 pontos) | Viés (mediana) | Dispersão | Resíduo após calibrar o viés |
| --- | ---: | ---: | ---: |
| 1 pose (linha de base) | +3,78% | 14,5 pts | 11,63% |
| 3 poses uniformes (dither angular) | +8,19% | 1,2 pts | 0,65% |
| 4 poses uniformes | +8,26% | 0,8 pts | 0,42% |
| **6 poses uniformes** | +7,90% | **0,4 pts** | **0,20%** |

O passo de zona do VL53L5CX é 5,625° (45°/8). As poses precisam cobrir **um período de zona completo**, uniformemente — 6 poses = 0,94° entre elas.

Testado também na cena **com oclusão por viga** (onde há ponto cego de verdade):

| Configuração | Erro | Cobertura |
| --- | ---: | ---: |
| Vista única | −25,92% | 70,0% |
| 3 inclinações (rotação) | −17,42% | 75,0% |
| **3 translações de 2 cm** | **−12,98%** | **89,0%** |
| 3 inclinações + 3 translações | −12,38% | 89,0% |

Translação sobe a cobertura de 70% para 89%; rotação quase não mexe. **Confirma a separação teórica: rotação para aliasing, translação para oclusão.** O problema dominante hoje (seção 2) é aliasing — rotação é o remédio certo para a fase atual do projeto.

### 5.2 O risco que quase inviabiliza a ideia: erro de servo

Injetamos erro no ângulo real do atuador (o firmware registra o comando, o mecanismo entrega outro):

| Erro do atuador (±) | Dispersão |
| --- | ---: |
| 0,0° | 1,2 pts |
| **0,25°** | **13,3 pts** |
| 0,5° | 17,1 pts |
| 1,0° | 23,2 pts |

**Um quarto de grau de erro devolve toda a dispersão original.** A conta física: 0,25° a 40 cm são 1,75 mm de deslocamento lateral; numa encosta de inclinação ~1:1, isso é 1,75 mm de erro de altura — 28% da altura média da pilha (6,25 mm).

### 5.3 A distinção que salva o projeto: exatidão não importa, repetibilidade importa

Separamos as duas coisas. Demos ao atuador um **erro fixo de fabricação** (+0,7°, −1,3°, +0,9° nas três poses) e calibramos esses valores uma única vez:

| Situação | Dispersão |
| --- | ---: |
| 3 poses com erro fixo, usando os comandos originais (não calibrados) | 10,7 pts |
| 3 poses **re-miradas após calibrar** os valores reais | 1,4 pts |

O que arruinou o primeiro caso não foi o erro em si — foi que os ângulos reais ficaram **agrupados** (fases 0,57°, 0,70°, 4,65° — duas quase coincidentes), destruindo o cancelamento. Depois de calibrar e recompor os comandos para que os ângulos *reais* caiam uniformemente no período de zona, o resultado volta ao patamar de 1,2–1,4 pts.

**Conclusão de engenharia: exatidão do atuador não importa — calibra-se uma vez. Repetibilidade importa, e não se calibra.**

Confirmado depois com jitter de repetição (variação a cada vez que o atuador vai à mesma posição, além do erro fixo já calibrado):

| Jitter de repetição (±) | Dispersão | Resíduo após calibrar o viés |
| --- | ---: | ---: |
| 0,00° | 10,7 pts | 6,64% |
| 0,10° | 9,9 pts | 5,46% |
| 0,20° | 14,9 pts | 12,19% |
| 0,50° | 8,7 pts | 4,08% |

(Esses números têm ruído estatístico próprio da amostra pequena, mas a ordem de grandeza — jitter de décimos de grau já reintroduz vários pontos de dispersão — se mantém.)

**Consequência de projeto: escolher o atuador pela repetibilidade declarada, não pela exatidão/resolução do datasheet.**

### 5.4 Servo com encoder barato: não resolve. Motor de passo: resolve, e mais simples

Fomos verificar se um encoder magnético comum entrega a exatidão necessária.

**AS5600** (o encoder mais citado para instrumentar servos de hobby): o datasheet declara **INL de ±1°** ([datasheet ams](https://files.seeedstudio.com/wiki/Grove-12-bit-Magnetic-Rotary-Position-Sensor-AS5600/res/Magnetic%20Rotary%20Position%20Sensor%20AS5600%20Datasheet.pdf)) — **quatro vezes pior** que os 0,25° necessários. Resolução nominal de 0,088°/contagem é ótima, mas resolução não é exatidão: lê fino, erra grosso. Instrumentar um servo barato com esse encoder não resolve o problema — ele vira o novo limitante.

**Motor de passo (NEMA17) em malha aberta:** não precisa de encoder. A posição é intrínseca ao próprio passo do motor (1,8°/passo nominal; fabricantes especificam repetibilidade não cumulativa da ordem de 5% do passo, ≈0,09°), **desde que nenhum passo seja perdido** por sobrecarga. É mais preciso que o encoder que se compraria para corrigir um servo, e mecanicamente **mais simples** — sem realimentação, sem calibração de sensor adicional.

**Recomendação de hardware: motor de passo pequeno em malha aberta, não servo de hobby com encoder.**

### 5.5 Respostas diretas às 10 perguntas originais

1. **Reduz ponto cego e melhora a estimativa?** Melhora muito, mas por anti-aliasing — não por redução de ponto cego (isso é o que a translação faz, em menor grau de importância para o problema atual).
2. **Ângulo ou deslocamento?** Ângulo, para o problema de hoje. Deslocamento só se houver oclusão real na cena.
3. **Dois servos (pan-tilt) bastam?** Bastam, e **um só eixo já entrega todo o ganho medido** (a tabela principal usa dither em um único eixo). O segundo eixo é para cenas assimétricas, não testadas aqui.
4. **Como registrar pose?** Não confiar no comando. Calibrar as posições reais uma vez (gabarito, medição direta) e gravar como tabela constante; o firmware manda o índice da pose, o receptor consulta a tabela.
5–6. **Como combinar as leituras / precisa de rotação e translação?** Sim — e a matemática já existe no pacote (`geometry.rotate`, R_z·R_y). A fusão testada monta o TIN dentro de cada varredura separadamente e acumula soma/contagem por célula numa grade compartilhada. Não há passo de "registro" entre nuvens porque a pose calibrada já coloca tudo no mesmo referencial.
7. **Regiões repetidas, ruído, inválidos?** A média por célula é o tratamento correto — é de onde vem o ganho. Zona inválida não conta. Célula sem nenhuma observação permanece desconhecida, nunca zero.
8. **Introduz novos erros?** Sim — jitter de repetição acima de ~0,25° destrói o ganho (seção 5.2–5.3). Vibração é o mesmo problema com outro nome: mover, esperar assentar, só então medir.
9. **Arquitetura mais simples?** Motor de passo no ESP32, alimentação separada da placa. Loop: posiciona (tabela calibrada) → aguarda assentar (~300 ms) → dispara aquisição 8×8 → publica com índice da pose. N=6 poses leva poucos segundos.
10. **Alternativa mais simples para o hackathon?** A mesma proposta, versão de um eixo. Plano B sem nenhum atuador: **quatro suportes fixos** com ângulos pré-medidos por transferidor — zero servo, zero jitter, mesmo ganho de anti-aliasing, ao custo de trocar manualmente entre aquisições.

### 5.6 Duas ressalvas que precisam entrar em qualquer relatório

**O viés não é constante entre formas.** Com 4 poses: pirâmide entre +7,9% e +10,4% conforme o enchimento; prisma de faces verticais **−9,99%**; rampa **+14,42%**. A calibração por escalar único só vale **dentro de uma família de formas** — para material granular (que forma pilha com ângulo de repouso característico), essa família é razoavelmente estreita, mas isso precisa ser dito explicitamente, não assumido.

**Tudo isso é simulação ideal.** Ray-casting rígido, sem ruído óptico, sem física real de servo. Os resíduos de 0,20–0,65% são o **teto** do que a arquitetura permite, não uma previsão de hardware. O que a simulação prova é que a arquitetura é correta e qual é o requisito mecânico (repetibilidade < 0,25°) — que já é um resultado valioso, mas não substitui medir em bancada.

---

## 6. Como provar que os dados são confiáveis — não apenas afirmar um número

Esta seção responde à pergunta "como entregamos dados fiéis", separada de "como reduzimos o erro". São coisas diferentes: a seção 5 reduz o erro; esta seção é sobre como **demonstrar**, de forma que resista a perguntas, que o erro medido é o erro real.

### 6.1 Correlação não prova confiabilidade — Bland-Altman prova

Dois métodos podem ter correlação altíssima (R² próximo de 1) e mesmo assim discordarem sistematicamente — por exemplo, um sempre medindo 20% a mais que o outro em toda a faixa. R²/regressão respondem "os métodos se movem juntos?", não "os métodos concordam?". A prática aceita para validar um instrumento novo contra uma referência é a **análise de Bland-Altman**: plotar a diferença entre os dois métodos contra a média deles, reportar o **viés médio** e os **limites de concordância** (±1,96 desvio-padrão da diferença) ([revisão em Innolitics](https://innolitics.com/articles/bland-altman-analysis-best-practices-faqs-and-examples/)).

Isso é, coincidentemente, o formato que já emergiu naturalmente dos nossos testes — viés + dispersão. Vale adotar o nome e a estatística formal (limites de concordância, não só min/max) no relatório final: fica imediatamente reconhecível como método científico padrão, não como convenção interna do projeto.

### 6.2 Um orçamento de incerteza formal (GUM) organiza o que já temos

A prática internacional de metrologia (JCGM 100:2008, *Guide to the Expression of Uncertainty in Measurement*) não aceita um número de erro solto — exige uma **tabela de contribuições de incerteza**, cada uma tipo A (estatística, por repetição) ou tipo B (por outra evidência, como especificação de fabricante), combinadas em quadratura, com incerteza expandida a k=2 (≈95% de confiança).

Proposta de estrutura para o BoxFlow, usando termos que já medimos:

| Fonte de incerteza | Tipo | Como estimar | Já temos o número? |
| --- | --- | --- | --- |
| Ruído de distância do sensor (por zona) | B | Datasheet / caracterização | Não — precisa de hardware |
| Erro de referência do vazio (perfil-zero) | A | Repetição de N capturas do piso vazio | Seção 2.4 dá a sensibilidade; falta medir a repetição real |
| Aliasing residual (grade × borda) | A | Dispersão pós-dithering na varredura de posição | **Sim — seção 5.1, 0,4–1,2 pts** |
| Repetibilidade do atuador | B ou A | Especificação do motor / medição direta | Seção 5.3 dá a sensibilidade; falta medir o motor real |
| Viés sistemático de integração (TIN + grade) | B | Calibração contra padrão conhecido | Seção 5.6 — depende da forma |

Montar essa tabela com números de hardware real é o entregável que transforma "medimos X%" em algo auditável.

### 6.3 Referência de verdade (ground truth) que não depende do próprio sistema

Para validar contra algo independente, os métodos aceitos para o volume real de uma pilha pequena:

- **Peça impressa em 3D com volume exato de CAD.** Provavelmente o caminho mais forte para vocês: zero incerteza de densidade, zero erro de pesagem, volume certificável a partir do próprio arquivo `.stl` (o slicer/CAD reporta o volume exato da malha). Permite testar exatamente as formas do `boxflow-lidar.chip.c` (pirâmide, prisma, rampa) como sólidos físicos.
- **Densidade aparente (bulk density) por norma**, se o teste for com material granular de verdade: [ASTM D7481](https://store.astm.org/d7481-18.html) (cilindro graduado), [D6683](https://store.astm.org/d6683-01.html), ou [C29](https://store.astm.org/c0029_c0029m-23.html) para agregados. Define como pesar um volume conhecido e calcular densidade — o caminho inverso do que vocês fazem, útil para a etapa de conversão para massa.
- **Deslocamento de água** (princípio de Arquimedes) — só serve se o material for hidrofóbico ou puder ser embalado, o que raramente é o caso de granel; citado por completude, não como recomendação principal aqui.

**Recomendação: peça impressa em 3D como padrão primário de bancada.**

### 6.4 O protocolo de repetibilidade/reprodutibilidade (Gage R&R)

Prática industrial padrão para caracterizar um instrumento de medição antes de confiar nele: repetir a mesma medição várias vezes (repetibilidade — mesmo operador, mesma configuração) e variar o que for razoável variar entre sessões (reprodutibilidade). O critério comum na indústria é que a variação do instrumento consuma uma fração pequena da tolerância do processo — não há um número mágico universal, mas a estrutura (N repetições, decompor variância em repetibilidade vs. reprodutibilidade) é o que confere credibilidade a uma alegação de precisão.

Para o BoxFlow: repetir a varredura de 6 poses N vezes sobre a **mesma** peça de referência, sem mexer em nada, dá a repetibilidade pura do sistema (incluindo ruído do sensor e jitter do atuador). Repetir depois de desmontar e remontar o suporte dá a reprodutibilidade.

### 6.5 Nunca validar e calibrar no mesmo conjunto de dados

Regra simples e frequentemente ignorada: se os parâmetros do estimador (limiares, pesos, correções) forem ajustados olhando para um conjunto de cenas, a precisão relatada **não pode vir desse mesmo conjunto** — é preciso reservar cenas não vistas durante o ajuste (ensaio confirmatório) para reportar o número final. Isso já está implícito na regra 2 do plano de conduta (seção 8), mas vale nomear explicitamente como boa prática de validação, não só como cuidado ad hoc.

### 6.6 Vocabulário de precisão de instrumento, para comparar com o que a indústria declara

Instrumentos comerciais certificados (balanças, scanners de volume "legal for trade") são classificados por **classe de exatidão** — um erro máximo permitido em função da faixa de operação (ex.: OIML R76, NTEP Handbook 44). Declarar "nossa incerteza expandida (k=2) é de X% na faixa de Y a Z litros" é o formato que permite comparação direta com esses padrões, em vez de um número solto sem contexto de faixa ou confiança.

---

## 7. Plano de execução

Ordenado por custo, e **atualizado** para incorporar a descoberta da seção 5. As primeiras rodam hoje, com as amostras que já existem, sem hardware e sem Wokwi.

### Protocolo obrigatório de avaliação

**Nenhum experimento é avaliado por um número único.** Toda hipótese é medida por uma varredura de posição da pilha de 13,0 a 17,0 cm em passos de 2 mm (ou o equivalente de 8 pontos usado na seção 5), reportando:

- **viés** (mediana do erro) — é calibrável
- **dispersão** (amplitude e, preferencialmente, limites de concordância de Bland-Altman — seção 6.1) — **não** é calibrável e é o alvo principal
- **estabilidade da cobertura** (quantos pontos da varredura mudam de estado)

Linha de base sem dithering: viés +3,78% a +6,78% (depende da varredura usada), dispersão 14,5–16,1 pontos.
**Com dithering de 6 poses (simulação ideal): viés +7,90%, dispersão 0,4 pontos.**

---

### E1 — Implementar o dithering angular no firmware e no receptor

**Por quê primeiro agora:** é a única mitigação que, na simulação, já ultrapassou a meta de dispersão. As demais (E2–E4 abaixo) continuam valendo, mas como refinamento sobre esta base, não como alternativa a ela.

**Fazer:**
1. No firmware, adicionar o loop de N poses (seção 5.5, pergunta 9): posicionar → aguardar assentar → adquirir → publicar com índice de pose.
2. No receptor, fundir os N quadros na mesma grade compartilhada (a lógica de `raster_triangle` já serve; o novo passo é acumular `sums`/`counts` entre quadros de poses diferentes, não só entre triângulos do mesmo quadro).
3. Escolher N e os ângulos por **calibração real do atuador**, não pelos comandos nominais (seção 5.3) — os ângulos *efetivos* é que precisam ficar uniformes no período de zona (5,625°).

**Critério:** reproduzir, com o atuador real (não mais só na simulação), dispersão abaixo de 5 pontos na varredura de posição física da peça de referência (seção 6.3/6.4).

**Custo:** um a dois dias, incluindo a montagem mecânica simples (seção 5.4 — motor de passo em malha aberta).

**Risco principal a monitorar:** jitter de repetição do atuador (seção 5.2–5.3). Medir a repetibilidade do motor escolhido **antes** de montar o sistema completo — é o item de maior alavancagem de todo o plano.

---

### E2 — Descartar zonas de borda

**Hipótese:** parte do erro remanescente (mesmo após dithering) está nas zonas externas, que sofrem reflexão de parede — é o que a ST faz na AN5843 (seção 4.1).

**Fazer:** recalcular usando apenas as zonas centrais 6×6, depois 4×4, comparando sobre a mesma varredura de validação.

**Critério:** redução adicional de dispersão ou de viés sobre o resultado de E1.

**Custo:** minutos.

---

### E3 — Filtro de descontinuidade por gradiente

**Hipótese:** o bridging entre encosta e piso ainda cria volume fantasma residual. O `MAX_EDGE_M` atual corta por comprimento de aresta 3D (10 cm), critério fraco.

**Fazer:** substituir por limiar de **ângulo de incidência entre pontos vizinhos** ([Sensors 17(1):92](https://www.mdpi.com/1424-8220/17/1/92)). Triângulo cujo gradiente vertical excede o ângulo de repouso plausível do material é descartado, não interpolado.

**Critério:** melhoria mensurável sobre E1+E2, sem regressão de cobertura em cenas sem oclusão.

**Custo:** uma tarde.

---

### E4 — Câmera como máscara de borda (seção 4.3)

**Hipótese:** segmentação por cor identifica a fronteira real do material, permitindo descartar zonas de borda de forma adaptativa em vez de por regra geométrica fixa.

**Fazer:** ESP32-CAM ou webcam auxiliar + limiar de cor simples; cruzar com a projeção das zonas do ToF no piso.

**Critério:** só prosseguir se E1–E3 não bastarem — é a opção mais cara em integração desta lista.

**Custo:** um dia.

---

### E5 — Ajuste paramétrico com ângulo de repouso (alternativa, não adição)

**Hipótese:** para material que forma pilha com ângulo de repouso característico, ajustar poucos parâmetros de uma forma restrita pode ser mais robusto que reconstrução livre, mesmo com dithering.

**Fazer:** ajustar cone/pirâmide (centro, base, altura, θ) aos pontos válidos por mínimos quadrados; comparar com o TIN+dithering na mesma varredura.

**Ressalva:** só vale para material granular. Não generaliza para carga em blocos ou lonas — documentar a hipótese de aplicabilidade.

**Custo:** um a dois dias. Prioridade menor que E1–E4 porque E1 já entregou o ganho principal.

---

### E6 — Perfil-zero medido

**Hipótese:** capturar a referência do vazio com o próprio sensor, na mesma pose (ou nas mesmas N poses do dithering), cancela o erro comum de pose e calibração — o item de maior sensibilidade isolada (seção 2.4, 16%/mm).

**Fazer:** substituir a referência analítica `base(x,y)` por uma média de M varreduras do piso vazio, nas mesmas N poses do dithering.

**Critério:** o teste de sensibilidade à referência deixa de mostrar 16%/mm, passando a depender só da deriva entre capturas.

**Custo:** meio dia. **Alto retorno, independente do dithering — fazer mesmo que E1 seja adiado.**

---

### E7 — Validação de bancada com ground truth (seção 6)

**Fazer:** imprimir em 3D 2–3 sólidos de volume conhecido (as mesmas formas do `chip.c` — pirâmide, prisma, rampa); rodar o protocolo Gage R&R (seção 6.4); montar a tabela de orçamento de incerteza (seção 6.2); reportar em formato Bland-Altman (seção 6.1).

**Critério:** este é o experimento que produz o número que vai para o relatório final — só depois de E1 (e idealmente E6) estarem implementados.

**Custo:** meio dia de impressão + um dia de medição.

---

### E8 — Fechar o caminho ponta a ponta

**Nunca foi executado.** Todos os testes HTTP usaram o emissor nativo em C (`native-c-test`), não o firmware. A tentativa no editor Wokwi foi interrompida.

**Fazer:** rodar ESP32 emulado → gateway → receptor → dashboard, com o mock atualizado (incluindo o dithering, se já implementado no mock). Gateway público **não** alcança `127.0.0.1`: usar gateway privado (plano pago do Wokwi) ou publicar o receptor em endereço acessível.

**Critério:** ver no serial `Varredura N: 64 raios, ... CRC OK` e HTTP 200, com `transport: wokwi-esp32` no painel.

**Custo:** algumas horas, mais o gateway. **É o que a apresentação precisa mostrar**, independentemente do estágio da precisão.

---

## 8. Regras de conduta

1. **Nunca reportar um número único de erro.** Sempre viés, dispersão e faixa — idealmente como limites de concordância de Bland-Altman (seção 6.1).
2. **Nunca ajustar posição, altura ou parâmetro até o número ficar bom.** Isso é calibrar contra o alias, e a banca não distingue de precisão real. Calibração de atuador é exceção **desde que feita antes e independente** da varredura de validação (nunca calibrar contra a própria peça de teste final — seção 6.5).
3. **O estimador não pode receber `fill`, forma, centro da pilha nem volume analítico.** Só o quadro, a pose e a referência. Preservar.
4. **Ausência de leitura nunca vira volume zero.** Região sem observação permanece desconhecida.
5. **Separar os três níveis de erro:** distância (mm), volume (%), massa (%). Não misturar.
6. **Distinguir sempre exatidão de repetibilidade do atuador** (seção 5.3) — é a diferença entre um problema resolvido por calibração e um problema estrutural.
7. **Manter o rótulo de dados simulados** em toda a interface enquanto não houver hardware.
8. **Registrar o que não foi executado**, como o pacote atual já faz.

---

## 9. O que significa "resolvido"

**Meta principal (revisada):** dispersão do erro abaixo de **5 pontos percentuais** na varredura de posição — **já alcançada em simulação ideal (0,4–1,2 pts) com dithering angular de 4–6 poses.** A meta agora é reproduzir isso com o atuador físico, o que depende inteiramente da repetibilidade real do motor escolhido (seção 5.3).

**Meta secundária:** viés mediano relatado com incerteza expandida (k=2), não como número solto — usando a estrutura da seção 6.2.

**Meta de demonstração:** caminho ESP32 → API → dashboard rodando ao vivo, com uma cena de falha mostrando tratamento honesto, e — se o tempo permitir — o dithering visível ao vivo (a pilha física move, a dispersão medida ao vivo cai).

**Fora de escopo, dizer isso explicitamente:** precisão em hardware industrial, comportamento com poeira, conversão para toneladas, validação certificada (OIML/NTEP). A simulação e mesmo a bancada de hackathon não sustentam essas afirmações.

---

## 10. Lacuna de pesquisa

A busca não encontrou: nenhum artigo usando VL53L5CX para volume de granel; nenhuma curva publicada de "número de zonas × erro de volume" para ToF multizona; nenhuma demonstração empírica do aliasing grade/borda em volumetria, nem do cancelamento por dithering angular em sensor ToF multizona de baixo custo — apesar de a teoria de Cavalieri existir e ser sólida, e de o próprio conceito ser usado (sem essa formalização) em scanners acústicos industriais de silo.

A combinação "aliasing de amostragem angular esparsa + anti-aliasing por dithering controlado, com separação explícita exatidão/repetibilidade do atuador" é, pelo que a pesquisa encontrou, um resultado que ninguém publicou nesta forma. Vale documentá-la com rigor — é potencialmente a contribuição mais citável do projeto.

---

## 11. Fontes

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
[SICK Bulkscan](https://www.sick.com/media/docs/3/23/823/operating_instructions_bulkscan_en_im0045823.pdf) ·
[Rede de sensores em grade — Pozzebon et al., Measurement 220:113404](https://usiena-air.unisi.it/retrieve/3e554811-070a-4d6d-9acc-d850b5289251/1-s2.0-S0263224123009685-main.pdf)

**Volumetria e reconciliação**
[Revisão — Drones 7(8):537](https://www.mdpi.com/2504-446X/7/8/537) ·
[LiDAR ponto único atuado — Drones 6(12):386](https://www.mdpi.com/2504-446X/6/12/386) ·
[Ângulo de repouso — arXiv:2505.17896](https://arxiv.org/html/2505.17896v1) ·
[Validação ângulo de repouso — arXiv:2509.13890](https://arxiv.org/html/2509.13890v1) ·
[Propeller — erro da base domina](https://www.propelleraero.com/blog/how-accurate-is-drone-stockpile-measurement/) ·
[Birdi — reconciliação e densidade](https://www.birdi.io/blog-post/how-to-reconcile-stockpile-volumes-a-step-by-step-guide-for-mine-and-quarry-operators) ·
[Thayer Scale — balanças de correia](https://www.thayerscale.com/conveyor-belt-scale-accuracy-engineering-guide/)

**Visão computacional + ToF**
[DELTAR — ECCV 2022](https://www.ecva.net/papers/eccv_2022/papers_ECCV/papers/136610612.pdf) ·
[DELTAR — código](https://github.com/zju3dv/deltar) ·
[CFPNet — arXiv:2411.04480](https://arxiv.org/html/2411.04480v1)

**Pose e atuadores**
[AS5600 — datasheet, INL ±1°](https://files.seeedstudio.com/wiki/Grove-12-bit-Magnetic-Rotary-Position-Sensor-AS5600/res/Magnetic%20Rotary%20Position%20Sensor%20AS5600%20Datasheet.pdf)

**Metodologia de validação**
[Bland-Altman — revisão em Innolitics](https://innolitics.com/articles/bland-altman-analysis-best-practices-faqs-and-examples/) ·
[ASTM D7481 — densidade aparente por cilindro](https://store.astm.org/d7481-18.html) ·
[ASTM D6683 — densidade de pós e sólidos a granel](https://store.astm.org/d6683-01.html) ·
[ASTM C29 — densidade de agregados](https://store.astm.org/c0029_c0029m-23.html)

---

## Anexo — reprodução dos experimentos

O pacote atual traz `tools/scene_dump.c`, que aceita `fill shape center_x obstacle dropout range seq yaw tilt origin_z`. **Para as varreduras de multivista por translação** foi necessário estendê-lo com dois argumentos adicionais, `origin_x` e `origin_y`, inserindo após a linha do `origin.z`:

```c
if(argc>11)s.origin.x=strtof(argv[11],NULL);
if(argc>12)s.origin.y=strtof(argv[12],NULL);
```

A varredura de posição usa `center_x` de 0,13 a 0,17 em passos de 0,002 (seção 2) ou 8 pontos de 0,006 (seção 5), com o estimador em `server/geometry.py` chamado via `estimate(raw)`. O envelope de pose aceito pelo estimador é x,y ∈ [0,05; 0,25] e z ∈ [0,2; 0,6]; `center_x` é limitado em [0,10; 0,20] pelo próprio chip.

**Para os experimentos de dithering angular (seção 5)**, o quadro gerado por `scene_dump` traz o ângulo comandado; para simular erro de atuador (comando ≠ ângulo real) foi necessário reescrever, após a geração, os campos de pose do cabeçalho binário (`yaw_deg`, `tilt_deg` — offsets 44 e 48 do quadro) com o ângulo *real* simulado, e recalcular o CRC32 (offset 60) sobre o quadro modificado — replicando exatamente o cálculo que `decode_frame` valida em `geometry.py`. Isso permite testar "o firmware registrou X, o mecanismo fez Y" sem precisar simular a dinâmica do motor.

A fusão de N poses agrega `raster_triangle(...)` de cada quadro decodificado separadamente na mesma grade (`sums`/`counts` compartilhados, um TIN por quadro, nunca ligando vértices de poses diferentes) antes de dividir para obter a altura média por célula — a mesma função existente em `geometry.py`, chamada em loop.
