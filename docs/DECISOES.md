# Decisões da revisão 30 cm

A orientação do usuário prioriza um MVP de hackathon com VL53L5CX e maquete de 30 × 30 cm, evitando o custo de um LiDAR de maior porte. Substitui a escala anterior de 60 cm e o mock genérico inicial de 8 × 6 m.

| Decisão | Resultado |
| --- | --- |
| Sensor de referência | VL53L5CX, representado no mock por 64 raios centrais ideais |
| Escala | Piso 30 × 30 cm, paredes 15 cm, sensor central a 40 cm |
| Campo | 45° nominal por eixo conforme tabela 2 da ST; substitui a derivação anterior de 48,50° |
| Protocolo | Mantido formato v2 de 704 bytes; referência geométrica incrementada para v3 |
| Reconstrução | Alturas relativas à base, grade 1,5 cm, aresta máxima 10 cm |
| Cobertura | Total somente com todos os centros suportados |
| Precisão | Mantida meta de 5%; reprovações publicadas, sem ajustar a meta |
| Histórico | Novo banco para impedir mistura das escalas |
| Comparações | Resolução em condições controladas, altura de montagem e referência deslocada independentemente |
| Hardware | Bibliotecas abertas disponíveis; driver e calibração físicos pendentes |

A geometria da carga e as fórmulas analíticas permanecem fora do receptor. Não foram acrescentados massa, densidade, alertas luminosos, IA ou medições fictícias de outros boxes. A comparação densa é um benchmark ideal offline, não um modo real do VL53L5CX.

Fontes consultadas na revisão: [ST, produto](https://www.st.com/en/imaging-and-photonics-solutions/vl53l5cx.html), [datasheet](https://www.st.com/resource/en/datasheet/vl53l5cx.pdf) e [biblioteca SparkFun](https://github.com/sparkfun/SparkFun_VL53L5CX_Arduino_Library). A disponibilidade de biblioteca não torna o protocolo do mock compatível com o hardware.

Os exemplos comunitários de 24C01, PCA9685, ICM42670P e analisador gráfico orientaram o estudo original da API Wokwi; não foram incorporados como drivers físicos. O cabeçalho de compilação e seu aviso MIT permanecem em `third-party/`. As [APIs de chips](https://docs.wokwi.com/chips-api/getting-started), [I²C](https://docs.wokwi.com/chips-api/i2c) e [framebuffer](https://docs.wokwi.com/chips-api/framebuffer) são referências de implementação, não prova de funcionamento óptico.

O usuário confirmou o dashboard v1 em seu navegador. A revisão atual tem testes HTTP/JS e WASM, mas o percurso completo ESP32 → mock → gateway → HTTP ainda precisa ser observado no Wokwi. Não há projeto publicado ou medição física declarados. Veja TESTES, COMPARACAO e MONTAGEM_30CM.
