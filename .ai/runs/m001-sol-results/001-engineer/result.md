Conclusão: os dados resumidos sustentam que translação de câmera melhora a linha de visada ideal e pode aumentar o suporte TIN, mas não demonstram que múltiplas vistas melhorem a estimativa de volume nem que alguma configuração esteja pronta para validação física como vencedora. Se for obrigatório escolher uma desafiante, `translated3_aimed` é a opção mecanisticamente mais defensável, sempre comparada a `fixed3` com o mesmo orçamento de 192 raios.

Há uma limitação de auditoria importante: o ambiente bloqueou toda leitura do workspace, inclusive comandos somente-leitura. Portanto, não pude inspecionar linhas de código, recalcular os 72 registros nem conferir hashes. A análise abaixo usa exclusivamente os fatos e a tabela fornecidos; não atribuo números ou linhas não observados.

## 1. Auditoria metodológica, matemática e de código

### Integridade dos registros

A cardinalidade declarada é internamente coerente:

- 8 braços × 9 cenas = 72 comparações.
- Se `total válido` representa a contagem exata por braço, há 24 registros válidos em 72: seis braços com 4/9 e dois com 0/9.
- Nenhum braço é válido na maioria das nove cenas.

Isso não prova que os 72 registros sejam únicos ou completos. Permanecem não verificados em [comparisons.json](</C:/Users/Raí/AppData/Local/Temp/boxflow-agent-m001-sol-results-engineer-eaf96f652314/.ai/runs/m001-implementation/results/comparisons.json>) e [comparisons.csv](</C:/Users/Raí/AppData/Local/Temp/boxflow-agent-m001-sol-results-engineer-eaf96f652314/.ai/runs/m001-implementation/results/comparisons.csv>):

- exatamente nove `scene_id` e oito `arm`;
- unicidade de `(scene_id, arm)`;
- ausência de valores ausentes, não finitos ou fora de faixa;
- paridade JSON–CSV;
- reprodução das medianas e contagens do [summary.md](</C:/Users/Raí/AppData/Local/Temp/boxflow-agent-m001-sol-results-engineer-eaf96f652314/.ai/runs/m001-implementation/results/summary.md>).

Os fatos “7/7 testes” e “72/72 produzidas” são evidência positiva, mas não substituem essas verificações.

### Congelamento e proveniência

Não foi possível conferir se o SHA-256 dos bytes de [protocol.json](</C:/Users/Raí/AppData/Local/Temp/boxflow-agent-m001-sol-results-engineer-eaf96f652314/.ai/experiments/m001/protocol.json>) coincide com `protocol.sha256`, nem se o mesmo digest aparece no [command-log.json](</C:/Users/Raí/AppData/Local/Temp/boxflow-agent-m001-sol-results-engineer-eaf96f652314/.ai/runs/m001-implementation/command-log.json>). Assim, “protocolo congelado” é um fato informado, não independentemente confirmado.

O ajuste de stdout binário no Windows é metodologicamente necessário para quadros binários. Ainda seria preciso confirmar no log ou por hash que:

- a quantidade de bytes por quadro é a esperada;
- não houve CRLF residual;
- o consumidor rejeita quadros curtos ou longos;
- todas as cenas usaram o mesmo executável e protocolo.

### Domínios e cálculos

As interpretações corretas são:

- `erro domínio próprio` não serve para ranquear braços: cada braço pode ser avaliado numa região diferente, criando viés de seleção por cobertura.
- `common_group` permite comparação somente entre braços pertencentes ao mesmo grupo.
- Uma classificação global dos oito braços exige `common_all`, que não aparece na tabela fornecida.
- Baixo erro com pouco suporte não implica boa reconstrução global. Esse é precisamente o risco de `translated4_corners_level`: erro próprio de 3,63% e `common_group` de 2,47%, mas somente 49% de suporte e 0/9 válidos.
- As medianas marginais não preservam pareamento: a cena que determina a mediana de suporte pode não ser a que determina a mediana de erro.

Invariantes que deveriam ser testados por cena no JSON:

1. `support(common_all) ≤ support(common_group) ≤ support(own)`.
2. Dentro de cada grupo e cena, todos os braços devem usar exatamente a mesma máscara e o mesmo denominador de verdade em `common_group`.
3. Todas as frações de bins, suporte e visibilidade devem pertencer a `[0,1]`.
4. Erro relativo exige denominador verdadeiro estritamente positivo e conversão percentual única.
5. `total_valid` deve ser reproduzível exclusivamente a partir dos limiares congelados.
6. Em simulador determinístico e sem ruído, repetir exatamente a mesma vista deve reproduzir amostras e estimativa, salvo uma regra explicitamente dependente da multiplicidade.

O último invariante é parcialmente refletido nas medianas: `baseline_fixed1`, `fixed3` e `fixed4` têm os mesmos 16% de bins, 84% de suporte, 94,5% de visibilidade, 4,08% de erro próprio e 4/9 válidos. A diferença de `fixed4` em `common_group` — 3,97% — pode decorrer apenas de outro domínio comum; não evidencia melhoria intrínseca.

### Vazamento de verdade

O uso dos centros verdadeiros no oráculo é aceitável somente porque ele é avaliador pós-hoc. A separação precisa ser confirmada em [m001_estimator.py](</C:/Users/Raí/AppData/Local/Temp/boxflow-agent-m001-sol-results-engineer-eaf96f652314/.ai/experiments/m001/m001_estimator.py>) e [run_p001.py](</C:/Users/Raí/AppData/Local/Temp/boxflow-agent-m001-sol-results-engineer-eaf96f652314/.ai/experiments/m001/run_p001.py>):

- verdade de volume, centros verdadeiros e geometria oculta não podem entrar no estimador, na TIN ou na seleção de células;
- a máscara `common_group/common_all` não pode ser filtrada por erro ou visibilidade verdadeira;
- `translated3_aimed` não pode mirar um centro verdadeiro específico da cena. Mirar um ponto fixo, definido no protocolo antes da cena, é aceitável; calcular a orientação a partir do centro verdadeiro é informação privilegiada da aquisição, mesmo que não entre no estimador.

Sem leitura do código, esse último ponto é um risco a verificar, não uma acusação de vazamento.

## 2. Interpretação causal sustentada pelos agregados

Não é possível entregar uma conclusão genuinamente “por cena”: os nove vetores individuais não foram fornecidos e os arquivos ficaram inacessíveis. Os agregados permitem estas inferências limitadas:

- `fixed3` versus `baseline_fixed1`: triplicar raios repetindo a mesma vista não alterou nenhuma mediana relevante. Mais raios nominais sem diversidade geométrica não trouxeram informação nova.
- `center_tilt3` versus `fixed3`, ambos com 192 raios: bins aumentaram 14 pontos percentuais e suporte 4 pp, mas a visibilidade do oráculo permaneceu 94,5%. Isso é coerente com mudança de amostragem/FoV, não resolução de oclusão intrínseca.
- `translated3_level` versus `fixed3`: bins +14 pp, suporte +12,5 pp e oráculo +5,5 pp, chegando a 100%. A translação forneceu linhas de visada que o ponto fixo não possuía.
- `translated3_aimed` versus `translated3_level`: mesmo oráculo, suporte quase igual, 4,5 pp menos bins e erro `common_group` agregado menor, 5,78% contra 9,46%. Isso sugere melhor direcionamento das amostras, mas medianas não provam vantagem pareada.
- `center_angles4`: teve o maior preenchimento de bins, 37%, mas suporte caiu para 74,5% e validade para 0/9. Cobrir mais bins não foi suficiente para formar suporte TIN útil.
- `translated4_corners_level`: alcançou 100% no oráculo e erro baixo na região comum, mas perdeu 35 pp de suporte frente a `fixed4` e caiu de 4/9 para 0/9. O baixo erro é compatível com avaliação numa região pequena e fácil; não compensa a falha de cobertura.

Como cada vista produz TIN própria e não existem triângulos entre vistas, esses resultados não demonstram reconstrução multivista geométrica. Demonstram apenas o efeito da união/mediana de estimativas locais.

## 3. Hipóteses

Como os identificadores formais das hipóteses em `protocol.json` não puderam ser lidos, classifico apenas as proposições inferíveis do objetivo:

- **Parcialmente confirmada:** transladar o ponto de vista reduz pontos cegos de linha de visada no simulador ideal. Os dois braços traduzidos de três vistas e o de quatro vistas atingem mediana de 100% no oráculo.
- **Refutada como afirmação geral:** “múltiplas vistas resolvem os pontos cegos”. Vistas repetidas e mudanças angulares no mesmo centro permanecem em 94,5%; somente a translação apresenta o efeito.
- **Refutada:** aumentar o número nominal de raios repetindo a mesma vista melhora o resultado. `fixed1`, `fixed3` e `fixed4` são essencialmente idênticos.
- **Refutada para as configurações testadas:** múltiplas vistas aumentam `total_valid`. O melhor resultado continua 4/9 e duas configurações caem para 0/9.
- **Inconclusiva:** translação melhora a precisão volumétrica. Erros próprios usam domínios diferentes, `common_group` não é necessariamente global e faltam `common_all` e deltas por cena.
- **Inconclusiva:** `translated3_aimed` é superior a `translated3_level`. O agregado comum favorece o aimed, mas suporte, bins e erro próprio são mistos, sem pareamento por cena.
- **Não testada:** superioridade em hardware real.

## 4. Próximo passo concreto e falsificável

A menor correção necessária não é uma nova simulação: é gerar, a partir de `comparisons.json`, um apêndice de auditoria por cena que:

1. valide o produto cartesiano 9 × 8 e a paridade com o CSV;
2. recalcule todas as medianas, contagens e flags;
3. execute os seis invariantes acima;
4. apresente, por cena, `total_valid`, suporte, erro `common_group` e `common_all`;
5. apresente deltas pareados de `translated3_aimed − fixed3`, ambos com 192 raios;
6. registre se a orientação aimed usa alvo fixo ou verdade da cena.

Critério falsificável: `translated3_aimed` só avança se não houver falha de integridade/vazamento, não perder validade frente a `fixed3`, aumentar suporte na maioria das cenas e não aumentar o erro pareado no domínio comum predefinido. Caso contrário, permanece refutado como candidato.

Se um ensaio físico tiver de ser escolhido agora, recomendo um teste A/B pareado — não um teste isolado — de `translated3_aimed` contra `fixed3`, com as mesmas caixas, mesmo orçamento de 192 raios e ordem de aquisição alternada. A escolha de `translated3_aimed` decorre de 96% de suporte, 100% de visibilidade ideal e melhor erro comum entre os dois braços traduzidos de três vistas. Ainda assim, seu 4/9 de validade impede tratá-lo como vencedor.

## 5. Limitações

- Não houve acesso aos artefatos; hashes, código, linhas e dados por cena permanecem não auditados.
- Nove cenas e medianas não fornecem incerteza, dispersão ou robustez.
- Apenas 24/72 registros parecem cumprir `total_valid`.
- `common_group` não autoriza comparações entre grupos; falta a tabela de `common_all`.
- O oráculo ignora FoV e orientação e não é uma capacidade do sistema.
- Suporte TIN é domínio de interpolação, não superfície fisicamente observada.
- O simulador pinhole não modela zonas finitas, histogramas, distorção, calibração, ruído ou repetibilidade.
- Repetições idênticas não testam o possível benefício de média temporal sob ruído real.
- Nenhuma mediana de nove cenas sustenta uma conclusão sobre hardware.
