# Revisão independente pós-pontuação — D-003

## Parecer

**Rejeitar a promoção da D-003 para R007 ou para o estimador de produção.** O protocolo exigia total elegível em 9/9 cenas e erro relativo absoluto de volume total `<= 5%` em todas elas. A D-003 ficou parcial em 9/9 cenas; portanto, nenhum erro de domínio próprio pode ser interpretado como aprovação da meta corporativa.

A intervenção ainda é útil como evidência de desenvolvimento: a triangulação global reduz parte do erro espacial nas superfícies inclinadas e recupera suporte interno perdido por viga/dropout. Ela não resolve a cobertura da caixa e preserva um erro de reconstrução muito alto no prisma e na rampa.

## Integridade e contratos

- Os 48 caminhos do `hash-manifest.json` existem e todos os SHA-256 conferem.
- `results.json` contém 18 registros (9 cenas x 2 métodos), `details.json` contém 9 candidatos e foram reutilizados exatamente 36 quadros, sem novas capturas.
- O SHA-256 do protocolo nos resultados é `e2d769b83910d8e4c2954ff6ab36f5afb8f6884a6991e8e688ed9a37a63ff957`, igual ao protocolo congelado.
- Em todos os nove candidatos: zero quadros inválidos, zero vistas indisponíveis, zero conflitos de merge, zero pontos em `Delaunay.coplanar` e nenhum erro do Qhull.
- O controle R005 e a D003 receberam os mesmos quatro quadros `translated4_corners_level` de cada cena. O executor também confirmou a igualdade exata entre as alturas recalculadas pelo R005 e as alturas arquivadas.
- A verdade entra somente no avaliador, após a execução dos estimadores. Suporte e elegibilidade são propriedades dos resultados truth-free; não há evidência de defeito no avaliador que explique os parciais.

## Critério de nove cenas

O resultado agregado é:

- totais D003 elegíveis: **0/9**;
- totais D003 avaliados contra 5%: **0/9**;
- cenas parciais: **9/9**;
- gate `all-nine`: **falhou**.

Sete erros líquidos no domínio próprio ficaram abaixo de 5%, mas isso não atende ao protocolo. Prisma (`45,713%`) e rampa (`40,331%`) também falham por ampla margem mesmo no domínio suportado.

## Suporte e causa geométrica

As poses registradas estão corretas e são as quatro combinações XY `(0,10; 0,10)`, `(0,20; 0,10)`, `(0,10; 0,20)` e `(0,20; 0,20)` m, todas em `z = 0,40 m`, com yaw, tilt e roll iguais a zero.

Nas cinco formas localizadas sem viga, cada vista forneceu 36 retornos aceitos, totalizando 144 pontos distintos. A envoltória XY desses pontos é `[0,037800; 0,262200] m` nos dois eixos. Ela contém apenas os centros das colunas e linhas 3 a 16 da grade: `14 x 14 = 196` células. Como o algoritmo declara qualquer ponto fora da envoltória convexa como não suportado, as 204 células restantes não podem receber estimativa.

Na camada, a superfície elevada muda a interseção dos raios e cada vista fornece 49 retornos. A envoltória passa a `[0,015810; 0,284190] m`, contendo linhas e colunas 1 a 18: `18 x 18 = 324` células. Permanecem 76 células externas sem suporte. O volume verdadeiro ausente é `0,0012825 m3`, ou **19%** do volume total da camada; por isso o erro próprio de `0,181%` não representa o erro total.

Esse padrão também aparece diretamente nas máscaras truth-free de `details.json`, antes do cálculo dos volumes verdadeiros. Logo, 196/324 resulta da geometria de aquisição e da regra sem extrapolação, não de uma máscara ou falha do avaliador.

## Comparação com R005

| Cena | Suporte R005 | Suporte D003 | Delta | Erro líquido próprio R005 -> D003 | Erro espacial próprio R005 -> D003 |
|---|---:|---:|---:|---:|---:|
| pyramid_center | 196 | 196 | 0 | 8,633% -> 0,890% | 20,698% -> 7,379% |
| pyramid_shifted_013 | 196 | 196 | 0 | 1,570% -> 4,821% | 21,461% -> 8,337% |
| two_stacks | 196 | 196 | 0 | 7,275% -> 4,038% | 28,924% -> 9,471% |
| prism | 196 | 196 | 0 | 43,851% -> 45,713% | 44,165% -> 45,801% |
| ramp | 196 | 196 | 0 | 40,207% -> 40,331% | 45,214% -> 40,716% |
| layer | 324 | 324 | 0 | 0,214% -> 0,181% | 0,240% -> 0,230% |
| pyramid_beam | 172 | 196 | +24 | 7,791% -> 0,489% | 20,076% -> 10,152% |
| layer_beam | 288 | 324 | +36 | 0,215% -> 0,194% | 0,244% -> 0,238% |
| pyramid_beam_dropout20 | 151 | 196 | +45 | 3,627% -> 1,052% | 19,172% -> 12,047% |

Nas três cenas em que o suporte mudou, a comparação justa é a interseção comum. Nela, a D003 apresenta respectivamente erro líquido/espacial de `0,302%/10,721%`, `0,190%/0,235%` e `1,543%/12,374%`; os controles permanecem `7,791%/20,076%`, `0,215%/0,244%` e `3,627%/19,172%`. Portanto, o ganho não é apenas efeito de avaliar células adicionais, embora continue restrito ao domínio parcial.

A D003 leva as cenas com viga/dropout até a mesma envoltória máxima da cena correspondente sem obstáculo: 120, 168 e apenas 95 pontos brutos ainda produzem 196, 324 e 196 células. Isso mostra que o Delaunay global preenche lacunas internas por triângulos entre vistas. É suporte interpolado, não área diretamente observada, e o protocolo já advertia que tais triângulos podem atravessar descontinuidades ou oclusões.

## Cancelamento e interpretação

O erro espacial melhorou em 8/9 cenas e piorou no prisma. O erro líquido melhorou em 6/9 e piorou na pirâmide deslocada, prisma e rampa. Resultados líquidos baixos não bastam para declarar precisão local:

- `pyramid_center`: razão de cancelamento D003 `8,29`;
- `pyramid_beam`: `20,77` no domínio próprio;
- `pyramid_beam_dropout20`: `11,45` no domínio próprio.

Assim, parte relevante dos erros positivos e negativos se anula na integração. O prisma quase não tem cancelamento (`~1,00`) e continua com erro espacial/líquido próximo de 46%, uma falha direta de reconstrução. A rampa também permanece próxima de 41%. Esses dois casos mostram que ampliar cobertura, isoladamente, não levaria este estimador à meta.

## Recomendação para a próxima rodada

Preservar a D003 apenas como resultado diagnóstico. A próxima hipótese deve ser congelada antes de nova pontuação e tratar separadamente os dois bloqueios observados:

1. aquisição/FoV capaz de colocar os 400 centros de célula dentro da envoltória de retornos aceitos, sem preencher bordas como zero;
2. reconstrução que detecte descontinuidades a partir das observações e evite ligar piso e topo através das bordas do prisma/rampa.

Não há justificativa para ajustar, após estes resultados, o quantum de merge, o limite de 3 mm ou o limite de aresta da D003. Qualquer nova variante deve receber outro identificador e protocolo, e seus erros parciais não devem ser promovidos como volumes totais.
