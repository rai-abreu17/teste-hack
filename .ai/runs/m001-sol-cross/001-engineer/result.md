A análise atribui mecanismos que o código não implementa e, por isso, não sustenta sua hipótese principal.

Primeiro, o rasterizador não extrapola alturas até as margens. Ele só preenche centros de células contidos em triângulos formados por raios adjacentes, rejeitando vértices ausentes, arestas acima de `MAX_EDGE_M` e faces sem área horizontal. Fora desses triângulos, a célula permanece `None`; se faltar qualquer célula, `total` é nulo. Logo, o erro de +17,5% não pode ser explicado como “células fora do casco recebendo altura de meia-encosta” sem evidência de outro caminho de código. A hipótese causal mais compatível é erro de interpolação planar dentro do suporte — por exemplo, uma superfície piramidal não alinhada à malha local —, mas isso ainda precisa ser medido.

A “cobertura” também não é o casco dos raios nem área diretamente medida: é a fração de células rasterizadas por TINs locais. Uma célula coberta pode conter apenas altura interpolada; uma margem geometricamente enquadrada pode continuar sem suporte por dropout, range, parede, viga ou aresta excessiva. A classificação proposta em E5 (“medida/interpolada/extrapolada”) não existe nos dados atuais e exigiria instrumentação do avaliador. Além disso, a dedução angular está imprecisa: o código distribui `sx` e `sy` linearmente no plano da imagem, não em passos angulares uniformes de 5,625°. Portanto, os limites derivados não reproduzem rigorosamente o gerador.

A afirmação de ganho exatamente nulo em capturas fixas só vale com mesma cena, pose, `seq` e dropout efetivamente nulo. O hash de dropout depende de `seq`; repetições podem recuperar retornos diferentes. Não há base para ganho `1/√N`: não há ruído contínuo simulado, e perda Bernoulli seguida de triangulação e união de suporte é não linear.

O experimento correto deve ter quatro resultados por cena:

- baseline de uma captura fixa, 64 raios;
- três capturas fixas, 192 raios;
- tilts `(-10, 0, +10)` no mesmo centro, 192 raios;
- origens `x=(.10,.15,.20), y=.15, z=.40`, 192 raios, com orientação ao centro explicitamente calculada.

Há uma ambiguidade a resolver no protocolo: “sem tilt” e “apontados ao centro” precisam ser traduzidos inequivocamente para `yaw/tilt` conforme a convenção do gerador. `originX/Y` também exige a pequena extensão já identificada no CLI/harness.

Cada captura gera seu TIN local. A fusão deve calcular a mediana apenas entre valores suportados por célula e usar a união dos suportes; não se cria Delaunay global. “Cobertura” continua significando suporte interpolado local, jamais área medida.

As métricas necessárias são: cobertura; erro celular assinado e absoluto contra o recorte exato de `truth.py`; volume observado comparado à verdade restrita exatamente ao mesmo suporte; e total somente quando todas as 400 células tiverem suporte. Para comparar reconstrução, usar também a interseção comum dos suportes. Volumes parciais crus não são comparáveis entre braços com domínios diferentes.

O protocolo pode mostrar ganho por repetição, mudança de direções e mudança de centro óptico. Não pode, sozinho, atribuir ganho dos centros exclusivamente à paralaxe: a translação também muda footprint, FoV e incidência. “Oclusão intrínseca” exige rotular, no avaliador, qual triângulo interceptou cada raio; dropout vem do status/hash, margem sem suporte vem dos `None`, e interpolação ruim vem do erro dentro do suporte. Sem esses controles, qualquer conclusão causal seria apenas hipótese. Resultados de desempenho ou margens de aceitação ainda não podem ser anunciados.
