O gate foi aplicado corretamente e a reprovação é inequívoca, assumindo que seus critérios são conjuntivos.

- Melhora mediana: `0,795 pp`, abaixo de `1 pp`.
- Vitórias: `7/9`, exatamente o mínimo exigido.
- Maior regressão: `3,891 pp` no prisma, acima de `2 pp`; a rampa também viola com `3,224 pp`.
- Suporte: `96%`, aprovado.
- Total: `4/9`, aprovado conforme informado, embora a definição desse indicador não tenha sido fornecida para recálculo independente.
- Domínio: `9/9`, aprovado.

A mediana confere: ordenando as reduções, o quinto valor é `0,795`. Portanto, dois critérios falham: ganho central e segurança de cauda.

O padrão é assimétrico: a regra melhora todas as cenas piramidais, as duas cenas `layer` e `two_stacks`, mas falha fortemente em `prism` e `ramp`. Como suporte, frames e domínio não mudaram, isso isola a fusão como causa; não é efeito de cobertura.

A explicação compatível com os dados é que o menor máximo de aresta mede densidade/escala local da triangulação, mas não o viés da estimativa. Em superfícies inclinadas ou em transições entre faces, um triângulo pequeno ainda pode ter geometria desfavorável ou erro sistemático dependente da vista. O `argmin` transforma esse proxy incompleto em uma decisão dura e pode selecionar sistematicamente a vista errada. Entretanto, sem mapas por célula, valores por vista ou incidência, não é possível afirmar se esse foi especificamente o mecanismo no prisma e na rampa.

Veredito: rejeitar a hipótese forte de que “menor aresta máxima é um substituto seguro da mediana”. A hipótese mais fraca — compactness contém algum sinal direcional útil — continua plausível pelos `7/9` ganhos, mas não está validada como estimativa de incerteza.

A próxima ablação mínima que proponho é uma fusão convexa fixa, sem limiar e sem truth. Para cada célula \(c\):

\[
m_c=\operatorname{mediana}_i z_{i,c},\qquad
s_c=z_{j,c},\quad
j=\arg\min_i(q_{i,c},i)
\]

\[
\boxed{\hat z_c=\frac{m_c+s_c}{2}}
\]

Aqui \(q_{i,c}\) é exatamente a compactness já usada; o índice mantém o desempate atual. Nada além da regra final de fusão muda. Essa ablação testa isoladamente se compactness acerta a direção, mas se o seletor duro exagera a magnitude.

Se o erro reportado for a média do erro absoluto por célula sobre o mesmo suporte e normalização, vale:

\[
\left|\hat z_c-y_c\right|
\leq
\frac{|m_c-y_c|+|s_c-y_c|}{2}.
\]

Logo, usando os resultados existentes, a previsão falsificável é:

- `prism` terá erro no máximo `5,9185`, isto é, regressão máxima de `1,9455 pp`;
- `ramp` terá erro no máximo `12,2635`, regressão máxima de `1,6115 pp`;
- as sete cenas atualmente vencedoras continuarão vencendo;
- suporte e domínio permanecerão exatamente iguais.

Assim, a cláusula de regressão deve passar. Não é possível prometer o gate completo: os agregados fornecidos só garantem melhora mediana de pelo menos `0,3975 pp`, não `1 pp`. Se qualquer limite acima for violado, isso falsifica a previsão e indica que “erro absoluto” não é agregado linearmente no mesmo conjunto de células ou que a implementação alterou algo além da fusão.
