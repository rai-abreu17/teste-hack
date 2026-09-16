# Montagem do MVP — 30 × 30 cm

**Para o hackathon, recomendamos uma placa VL53L5CX com ESP32 e maquete de 30 × 30 cm.** Essa dimensão é uma escolha prática de projeto. Não foi encontrada na documentação consultada uma especificação de que 30 × 30 cm seja ideal ou obrigatória.

A [biblioteca Arduino da SparkFun](https://github.com/sparkfun/SparkFun_VL53L5CX_Arduino_Library) é aberta e adaptável. Ela facilita a aquisição; não altera os limites ópticos. O [datasheet da ST, tabela 2](https://www.st.com/resource/en/datasheet/vl53l5cx.pdf) informa campos nominais de 45° horizontal/vertical e 65° diagonal. O campo efetivo depende das condições/configuração. A ST classifica o componente como grau industrial na [página oficial](https://www.st.com/en/imaging-and-photonics-solutions/vl53l5cx.html); isso não equivale a um equipamento completo para mapear um armazém.

| Parte | Medida interna do modelo |
| --- | --- |
| Piso | 30 × 30 cm |
| Paredes laterais e de fundo | 15 cm, frente aberta |
| Bases inclinadas | 1 cm de largura e altura |
| Sensor | Centralizado, voltado para baixo, a **40 cm do piso** |
| Acima das paredes | 25 cm |
| Suporte sugerido | Ajustável, aproximadamente 35–50 cm do piso |
| Pilha central | Base de 15 × 15 cm; alturas 2,5, 5, 7,5 e 10 cm |

Acrescente espessuras de paredes/pés ao cortar a estrutura. Se o piso físico for plano, sem as bases inclinadas, ou tiver outra geometria, cadastre e calibre a referência correspondente.

## Campo observado

Cálculo geométrico de planejamento, não medição óptica: `lado ≈ 2 × distância ao plano × tan(22,5°) ≈ 0,8284 × distância`.

| Plano com sensor a 40 cm | Distância | Campo nominal aproximado |
| --- | ---: | ---: |
| Piso | 40 cm | 33,1 × 33,1 cm |
| Superfície a 5 cm | 35 cm | 29,0 × 29,0 cm |
| Superfície a 10 cm | 30 cm | 24,9 × 24,9 cm |

A pilha central de 15 × 15 cm cabe nesse campo nominal. Uma camada alta sobre toda a base exige outro tratamento de cobertura. Os centros das zonas externas ficam dentro da extensão total do campo. Na projeção ideal, cada zona tem cerca de 4,1 cm de lado no piso; `30/8=3,75 cm` só vale se o campo coincidir exatamente com a base.

Diminuir a maquete permite trabalhar mais perto e representar detalhes menores em centímetros. Se tudo diminuir proporcionalmente, continuam existindo as mesmas 64 zonas sobre a forma relativa. Isso não garante menor erro percentual de volume.

## Altura versus suporte na simulação

| Sensor acima do piso | Vazio | Pirâmide central de 7,5 cm | Camada de 7,5 cm |
| --- | ---: | ---: | ---: |
| 35 cm | 64% | 64% | 49% |
| **40 cm** | **100%** | **100%** | 64% |
| 45 cm | 64% | 64% | 81% |
| 50 cm | 81% | 81% | 49% |

Dados do modelo ideal. Subir não garante suporte maior: algumas zonas atingem paredes/exterior e são descartadas, e o algoritmo não extrapola. A configuração de 40 cm é o ponto inicial para vazio e pilhas centrais; não garante qualquer distribuição nem foi otimizada para minimizar erro. Reproduza com `python tools/check_mounting.py`.

## Ensaio físico

1. Escolha uma placa VL53L5CX compatível com os níveis elétricos do ESP32 e siga a pinagem/alimentação documentadas para ela. O circuito Wokwi é do mock.
2. Fixe o sensor no centro a 40 cm do piso. Comece em ambiente interno com iluminação estável e suporte imóvel após calibração.
3. Integre o driver real, configure 8×8 e confira leituras/validade. Mova um objeto pelos quatro cantos para mapear a orientação das zonas. O sketch do mock não inicializa o sensor físico.
4. Capture repetidamente o vazio para validar referência e pose. Use objetos rígidos de dimensões conhecidas antes de material granular.
5. Demonstre entrada, redistribuição, retirada e oclusão, mantendo indicação de parcial quando houver lacunas. Compare volume conhecido com estimado nas condições da apresentação.

Na cena principal, referência de 0,5625 L e estimativa simulada de 0,660934 L resultam em +17,50%. Isso caracteriza este modelo ideal, não a precisão esperada do hardware. Em toda a base, 1 mm de desvio comum da referência equivale aproximadamente a 0,09 L quando suporte/truncamento não mudam. Mais leituras não removem automaticamente um erro sistemático.

O cálculo e a API permanecem em m³: 1 L = 0,001 m³. A maquete é adequada ao experimento do MVP; a meta de 5% ainda não foi demonstrada.
