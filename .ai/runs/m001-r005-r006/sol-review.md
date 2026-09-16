# Revisão independente R005/R006

Registro de execução: revisão solicitada ao subagente `r005_engineering` com modelo `gpt-5.6-sol` e esforço `high`. Este registro documenta a rota solicitada; não é atestação do provedor sobre a identidade do processo.

## Veredito

**R007 não está pronto.** Nenhuma das cinco variantes é candidato defensável para a meta de erro relativo de volume **total** de no máximo 5%. Cada variante tem o mesmo resultado categórico: 2/9 cenas passam, 2/9 falham e 5/9 não produzem total. As diferenças numéricas entre variantes existem, portanto "empate metrológico" é uma formulação forte demais; o correto é que nenhuma se separa por um critério de seleção válido ou satisfaz o requisito.

## Achados bloqueadores

1. As cinco abstenções não são cenas de volume verdadeiro nulo. São cenas com volume verdadeiro positivo nas quais faltou suporte TIN para emitir um total. Criar uma tolerância de "volume parcial" mudaria o requisito de total e esconderia a falha de cobertura. Esses casos devem permanecer reprovação por abstenção para prontidão do candidato.
2. A concentração de erro em transição/sombra é descritiva, não causal. A partição usa arestas, alturas de alvo e obstáculo da verdade; massa e descontinuidade também se concentram nela. Em `two_stacks`, 100% do volume verdadeiro está na banda. A razão de densidade de erro sustenta localização, mas não identifica aquisição, amostragem ou interpolação como causa.
3. O braço A proposto pelo Opus tem inferência invertida. Substituir valores amostrados por verdade e manter o TIN testa o efeito de corrigir os valores de entrada. Uma melhora não demonstra que a interpolação domina; com o operador de interpolação fixo, ela demonstra sensibilidade aos valores substituídos. No simulador ideal, os retornos já são interseções geométricas exatas, de modo que "altura verdadeira na mesma posição" precisa ser definida ou pode ser identidade/vazamento de verdade celular.
4. O braço B também não é um oráculo definido. Pontos esparsos não têm volume sem pesos de área ou regra de reconstrução. "Integrar amostras sem TIN" exige especificar quadratura, footprints ou tesselação; essa escolha reintroduz reconstrução e impede a atribuição anunciada.

## Verificações

- As quatro partições (`transition/planar`, `shadow/not_shadow`, união/restante e sobreposição em quatro grupos) são exaustivas e disjuntas nos 45 registros. Contagens, área, verdade, erro assinado e erro celular absoluto recompõem o domínio.
- Foram confirmados 45 registros cena-método, 18.000 registros celulares, 54 vistas e todos os hashes do manifesto. O resultado tem quatro totais elegíveis por método: dois passam e dois falham.
- O contrato sem verdade está preservado: `r005_estimator.py` não importa o avaliador; R006 chama a fusão apenas com bytes/configuração e acrescenta os rótulos verdadeiros depois, no avaliador. Nenhum rótulo retorna à fusão.
- R006-C está corretamente pré-registrado e sua álgebra foi recalculada em 36 combinações de linha/domínio. Corrigir perfeitamente apenas as células suportadas da banda de transição leva `pyramid_center` a 2,895%/3,099%, mas deixa `ramp` em 5,146%/5,089%. Portanto, a banda congelada sozinha não basta para fazer as duas cenas atualmente reprovadas atingirem 5%. O contrafactual não preenche lacunas, não é implementável e não prova causa.

## Próxima ação válida

Abrir outra rodada de **desenvolvimento**, separando os fatores por intervenções implementáveis. Primeiro, com aquisição fixa e os frames arquivados, pré-registrar uma regra de reconstrução sem verdade que trate transições e suporte, exigindo 400/400 células e erro total ≤5% nas cenas de desenvolvimento. Se nenhuma regra alcançar suporte total, congelar a reconstrução e executar depois uma comparação pareada de aquisição em dados novos. Somente um candidato implementável, congelado após passar cobertura e erro no desenvolvimento, pode seguir para R007 em geometrias reservadas.
