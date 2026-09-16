# M-001 — primeira análise independente

Problema: estimar volume de material em maquete de box com hardware acessível, cobertura incompleta e oclusões; distinguir demonstração MVP e evolução industrial. Nenhum sensor, movimento ou prior está escolhido definitivamente. Não procure consenso antes de responder.

## Evidência prévia (SIMULADO, não repetir)

Pacote existente: box 30x30 cm, paredes15cm, sensor central a40cm do piso. Mock8x8 representa64 raios centrais com FoV45 graus por eixo e primeira interseção de raios com triângulos; distâncias quantizadas a1mm. Não simula mistura de retornos por zona, ruído óptico, reflexões, interferência ou driver físico VL53L5CX. Protocolo próprio0x42, quadro704bytes. ToF é candidato, não produto industrial escolhido.

O estimador atual triangula alturas relativas ao vazio e integra400 células de1,5cm; 400células não são400medidas. Total só publicado com suporte em todas; caso parcial mantém total nulo. Ground truth fica somente no avaliador.

Resultados existentes em docs/EXPERIMENTOS_64_ZONAS.md e build/experiments/: TIN pirâmide central verdade0,5625L, estimado0,660934L (+17,50%). Em21 posições amplitude16,11pp. Modelo piramidal condicionado à forma reduziu amplitude para0,98pp e2,32pp em60casos reservados da mesma família. Isso não valida forma arbitrária. Recortes e gates de inclinação não solucionaram erro do total. Vazio medido removeu desvio vertical comum, mas não interpolação ou deriva posterior. Camada7,5cm coberta64% a40cm,81% a45cm,100% a48cm,73% a49cm e49% a50cm; elevar não é monotônico por paredes/retornos. Com viga TIN parcial70%; perfil ideal denso75%, logo aumentar densidade não remove todos os pontos cegos.

## Código reaproveitável

wokwi/boxflow-lidar.chip.c contém Scene com origin/yaw/tilt e gerador geométrico; tools/scene_dump.c harness C exporta os mesmos quadros binários. Atualmente CLI aceita fill,shape,centerX,obstacle,dropout,range,seq,yaw,tilt,sensorZ; ainda não originX/Y. experiments/truth.py tem volume analítico e recorte exato por célula independente do estimador. server/geometry.py decodifica quadro com pose; experiments/estimators.py tem TIN e ajuste condicionado. Famílias existentes: pirâmide,duas pilhas,prisma,rampa,camada; viga e perdas configuráveis. E0–E4 já executados; rotação,múltiplas vistas,fusão ainda não comparadas quantitativamente. Wokwi ponta a ponta/hardware físicos pendentes.

## Tarefa nesta rodada

Apresente análise independente de até900palavras em português: problema observável, restrições, mecanismos candidatos, hipóteses improváveis, lacunas de evidência e até3experimentos discriminantes. Priorize comparação justa de sensor fixo, rotação com mesmo centro óptico,centros ópticos distintos e reconstrução. Distinguir ganho por número de capturas de ganho por ponto de vista. O experimento deve preservar verdade fora do estimador e comparar total e domínio parcial corretamente; não transformar extrapolação em cobertura medida. Nenhum percentual de aceitação novo arbitrário.

Proponha uma rodada pequena e reprodutível usando o código existente, sem repetir E0–E4 nem alterar dashboard ou firmware produtivo. Evidência física externa não fornecida deve ser marcada como lacuna ou hipótese, nunca inventada. Não use ferramentas nesta análise textual; a pesquisa documental e a implementação são tarefas separadas. Não receba respostas de outros agentes nesta primeira rodada.
