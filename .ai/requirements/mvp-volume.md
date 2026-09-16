# Critério de volume do MVP

Fonte: usuário informou nesta execução: «0,05 é o erro esperado pela empresa no valor do volume medido para o real».

Interpretação comunicada ao usuário: erro relativo absoluto de volume **até 5%**, isto é, `abs(V_estimado - V_real) / V_real <= 0.05`, para `V_real > 0`. O valor 0,05 não foi interpretado como litros ou metros cúbicos.

O critério aplica-se a volume total estimado. Um volume parcial só pode ser comparado à verdade daquele domínio e deve continuar identificado como parcial; não passa a meta de volume total. Resultados precisam informar quantas cenas têm total elegível, quantas atendem aos 5%, quantas excedem e quantas têm abstenção.

Em vazio, o erro relativo é indefinido. Relatar erro absoluto em litros; a tolerância específica para vazio ainda não foi definida. O intervalo de atualização também não foi especificado. Nenhum desses valores será inventado para aprovar o MVP.

As regras de 1 ponto percentual de melhoria, 7/9 vitórias e regressão máxima de 2 pontos percentuais pertencem aos experimentos históricos. Não substituem a meta empresarial de 5% nem devem ser alteradas retroativamente.

Validação reservada e ensaio físico devem declarar antes da execução as condições de uso, a comparação primária, os casos em que o sistema pode abster-se e a referência de volume. Aprovação simulada não certifica o sensor real.
