# Comparação para escolher a configuração do MVP

**Para o hackathon com a maquete de 30 × 30 cm, recomendamos o VL53L5CX.** Há hardware identificado e bibliotecas abertas para integrar com ESP32. O mock genérico anterior era uma ferramenta geométrica, sem equipamento comercial correspondente escolhido para compra.

**Nova comparação de algoritmos, 13/09/2026:** [EXPERIMENTOS_64_ZONAS.md](EXPERIMENTOS_64_ZONAS.md) mede dispersão, recortes, inclinação, ajuste piramidal/cone e referência medida. O ajuste piramidal foi o melhor candidato para essa família simulada; não é uma validação física nem uma mudança automática do dashboard. Os números abaixo continuam descrevendo o TIN original.

| Critério | VL53L5CX na maquete | Mock genérico anterior |
| --- | --- | --- |
| Modelo | 64 raios centrais ideais, 8×8 | 3.185 raios ideais, 65×49 |
| Escala | Piso 30 × 30 cm, sensor a 40 cm | Originalmente piso de 8 × 6 m |
| Campo | 45° nominal horizontal/vertical | 112° × 72° hipotéticos na versão original |
| Hardware para compra | Placa VL53L5CX, ainda a selecionar | Sem modelo comercial definido |
| Integração física | Driver e calibração pendentes | Hardware e driver pendentes |
| Precisão física comprovada | Não | Não |

Os erros originais não são diretamente comparáveis porque as geometrias e campos eram diferentes. Para isolar a amostragem, fizemos a comparação abaixo na mesma maquete de 30 cm.

## Comparação controlada

Mantidos piso, paredes, sólidos, pose (0,15; 0,15; 0,40) m, FOV ideal 45° por eixo, corte 4 m, quantização mm, grade 1,5 cm e aresta máxima 10 cm. Muda somente a distribuição de raios. O denso não é um modo do VL53L5CX nem um LiDAR comercial ensaiado.

| Cena | Referência m³ | 64 zonas: observado m³ | Erro do total | Denso: observado m³ | Erro do total |
| --- | ---: | ---: | ---: | ---: | ---: |
| entrada-25 | 0,000187500 | 0,000208823 | 11,37% | 0,000196075 | 4,57% |
| entrada-50 | 0,000375000 | 0,000433881 | 15,70% | 0,000386353 | 3,03% |
| entrada-75 | 0,000562500 | 0,000660934 | 17,50% | 0,000574418 | 2,12% |
| entrada-100 | 0,000750000 | 0,000905937 | 20,79% | 0,000763794 | 1,84% |
| redistribuicao | 0,000562500 | 0,000590570 | 4,99% | 0,000569239 | 1,20% |
| duas-pilhas | 0,000425000 | 0,000435754 | 2,53% | 0,000431923 | 1,63% |
| oclusao | 0,000562500 | 0,000416720 | Parcial | 0,000449630 | Parcial |
| rampa | 0,000843750 | 0,000934938 | 10,81% | 0,001037945 | 23,02% |

Sete cenas distintas com total em ambos, sem contar repetição na retirada ou cena principal:

| Medida | 64 zonas | 3.185 raios ideais |
| --- | ---: | ---: |
| Até 5% de erro absoluto | 2 de 7 | 6 de 7 |
| Média do erro relativo absoluto | 11,96% | 5,34% |
| Pior erro absoluto | 20,79% | 23,02% |
| Cobertura com viga | 70% | 75% |

A pirâmide central tem erro +17,50% com 64 zonas e +2,12% no denso. Na rampa, o denso é pior: +23,02%, contra +10,81%. Mais raios melhoram a média deste conjunto, mas não resolvem toda limitação da reconstrução. A origem exata do excesso na rampa não foi isolada. A redistribuição de 64 zonas fica em +4,9903%, quase no limite de 5%, sem margem robusta.

São ensaios determinísticos de desenvolvimento, sem ruído óptico, conjunto confirmatório independente ou validação de hardware. Cobertura completa não garante precisão; mais zonas não eliminam erro comum da referência.

## Recomendação

**Use o VL53L5CX para construir e demonstrar o MVP**, começando pelo suporte central a 40 cm e calibração do vazio. O guia MONTAGEM_30CM detalha cobertura e ensaios com objetos aferidos. Não é necessário comprar agora um LiDAR de maior porte para demonstrar essa cadeia.

O denso permanece uma referência de desenvolvimento da matemática. O produto em escala real exige outra etapa de seleção e ensaio de aquisição, sem modelo comercial escolhido neste trabalho. A redução de 60 para 30 cm não prova melhora intrínseca da precisão: também mudaram campo e pose, e a quantização em mm permaneceu.

Fontes: [ST](https://www.st.com/en/imaging-and-photonics-solutions/vl53l5cx.html), [datasheet](https://www.st.com/resource/en/datasheet/vl53l5cx.pdf) e [biblioteca SparkFun](https://github.com/sparkfun/SparkFun_VL53L5CX_Arduino_Library). Não foi encontrada recomendação da ST de base ideal obrigatória de 30 × 30 cm.

Dados: `samples/manifest.json`, `build/resolution-comparison.json` e `build/mounting-comparison.json`. Reproduza com `generate_samples.py`, `compare_resolution.py` e `check_mounting.py`.
