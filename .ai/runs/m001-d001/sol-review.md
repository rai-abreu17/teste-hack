# Revisão independente D-001

## Escopo e integridade

Revisão somente de leitura do estimador, protocolo congelado e resultados; este arquivo é a única saída criada pelo revisor. D-001 é desenvolvimento sobre nove cenas já inspecionadas, não validação reservada.

- SHA-256 do protocolo: `774f27ef7e547f1939c79f8f43acc93d0f6813e111c0cb0c07c42d3c808070ea`.
- Os 67 itens do manifesto foram recalculados e conferem: 54 quadros, a comparação de origem, protocolo, fontes congeladas e três saídas da rodada.
- Os 36 registros esperados estão presentes e são únicos: 9 cenas × 2 aquisições × 2 métodos.
- Os hashes atuais de `d001_estimator.py`, `test_d001.py` e `run_d001.py` coincidem com os hashes congelados. Seus horários de modificação antecedem o congelamento (`2026-09-14T22:52:49.726448Z`) e a criação dos resultados (`2026-09-14T22:52:53.852766Z`). Não há evidência de ajuste de fonte depois da pontuação.
- Na revisão anterior ao congelamento, 8 testes passaram. A fonte congelada acrescentou o teste de vista indisponível; a suíte final tem 9 testes e todos passaram em nova execução independente.

## Veredito prático

D-001 falhou o gate pré-registrado. Na aquisição primária `fixed3`, as nove cenas ficaram parciais; portanto nenhuma produziu um total elegível, e a exigência de nove totais com erro relativo absoluto menor ou igual a 5% não foi satisfeita. O suporte chegou a 399/400 na rampa, mas parcial não pode ser tratado como total.

Em `translated3_aimed`, sete cenas ficaram parciais. Somente prisma e rampa alcançaram 400/400, ambos como totais baseados em modelo. O prisma passou numericamente com 1,548971%; a rampa falhou com 12,592431% e erro espacial de 35,500284%. Um resultado entre nove abaixo de 5% em uma aquisição secundária não autoriza R007 nem demonstra que a reconstrução resolveu o problema.

## Auditoria do prisma apontado

O resultado do prisma não sustenta uma conclusão de precisão espacial:

- verdade total: `0,001687500 m³`;
- estimativa total: `0,001713639 m³`;
- erro líquido: `+0,000026139 m³`, ou `+1,548971%`;
- erro absoluto integrado por célula: `0,000544283 m³`, ou `32,253801%` da verdade, 20,82 vezes o erro líquido;
- 374 células foram rotuladas como suporte local e 26 como suporte de modelo;
- as 26 células de modelo somaram `0 m³` estimado. Nas 20 células ganhas em relação ao controle havia `0,000067500 m³` de verdade;
- no domínio comum de 380 células, a estimativa excedeu a verdade em `0,000093639 m³` (`+5,780178%`). A verdade omitida fora desse domínio, `0,000067500 m³`, cancelou a maior parte desse excesso e deixou o erro líquido em 1,55%.

Assim, o prisma satisfaz literalmente a métrica corporativa de erro do volume total nesta cena, mas o faz por cancelamento entre erros de sinais opostos. Deve permanecer registrado como `model_based_total`; não é evidência suficiente para aprovar o método.

## Próxima rodada recomendada

Não retunar os limites de D-001 com base nestes resultados. A próxima experiência deve isolar aquisição e cobertura:

1. manter o estimador D-001 congelado;
2. pré-registrar um pequeno conjunto de poses derivadas apenas da geometria do sensor e da caixa;
3. selecionar a aquisição primeiro por critérios sem verdade: 400/400, zero quadro inválido/indisponível, quantidade de suporte de modelo e estabilidade entre vistas;
4. somente depois congelar a pose escolhida e avaliar volume em cenas novas, separando erro líquido, erro espacial e células de modelo.

Se nenhuma pose alcançar cobertura observacional suficiente, a rodada seguinte deve representar explicitamente a ambiguidade de fronteira como intervalo de volume. Preencher cascos e devolver um ponto único repetiria o cancelamento observado no prisma.
