## O que sobrevive

1. **O controle 2x2 com aquisição fixa é a única comparação interpretável aqui**, e ele muda a leitura. Recalculando das colunas da tabela:
 - P003 contra a mediana da *mesma* aquisição: 7/9, mediana ≈ +0,860 pp, pior regressão 3,213 pp (prism −2,250; ramp −3,213). Quase idêntico ao resultado contra fixed3 (0,795 / 3,891 pp) ⇒ **o efeito de P003 vem da regra de fusão, não do braço de aquisição**.
 - P004 contra a mesma aquisição: 5 ganhos, 4 empates exatos, **zero regressões**, mediana ≈ +0,045 pp. Logo a regressão de 0,503 pp observada contra fixed3 é atribuível à **aquisição**, não à mediana inferior/trim.
2. **A mediana inferior é o componente ativo de P004**; trim só disparou em prism (8 células no grid inteiro).
3. Suporte completo em 4/9 significa apenas cobertura da interpolação — não verdade física nem exatidão.
4. O gate histórico continua falhando; mantê-lo como registro, não como requisito de produto.

## O que retirar

- **"Trimming conteve regressões em rampa/viga/dropout"**: falso — não removeu vistas nessas cenas. Retirar a alegação de mecanismo.
- **Prism como evidência a favor do trim**: é a única cena com trim ativo *e* mediana inferior ativa; efeito confundido, não decomponível com os dados presentes.
- **Ganhos de +0,021 / +0,028 / +0,045 pp como "vitórias"**: estão na ordem do ruído de implementação (arredondamento, desempate, ordem de soma). Contabilizá-los como 2 das vitórias de P004 infla a contagem.
- **Qualquer inferência de acurácia a partir de dropout20 (+1,903 pp)**: a máscara cobre 16,3% do volume verdadeiro; o indicador integra alturas e depois normaliza, permitindo cancelamento espacial. Ganho em máscara pequena ≠ ganho de volume.
- **P003 como evidência de que "menor aresta máxima indica melhor interpolação local"**: o código pontua um triângulo e devolve a **altura média da TIN da vista**. Métrica e estimador estão desacoplados. Note o padrão: as duas únicas perdas são prism e ramp — superfícies inclinadas, onde média da vista ≠ altura local. A hipótese mais simples é que o resultado de P003 mede um viés de média global, não seleção local.

## Ordem das próximas rodadas

1. **Sanear o contrato avaliador/estimador** (altura, suporte e métrica de qualidade do mesmo triângulo/conjunto; validade de quadro/vista uniforme; `all(... is not None)` alinhado ao P001).
2. **Re-executar o controle 2x2 após o saneamento.** Isto falta no plano: os números de P003 acima provavelmente são um artefato do próprio bug que a etapa 1 corrige, então a tabela atual não é linha de base válida pós-correção. Verificar também se os quatro "0" de P004 são identidade genuína (n ímpar) e não artefato de log.
3. **Diagnóstico alcance/FoV/oclusão vs. interpolação por célula**, com regra de decisão e saídas declaradas *antes* de rodar; saída esperada é uma hipótese de mecanismo, não um ranking.
4. **Especificar o critério MVP** (volume/erro/custo) antes de escolher candidato — sem isso, a seleção continua mirando um alvo indefinido.
5. Só então: **um candidato, código e parâmetros congelados, conjunto reservado**.

## Críticas ao desenho proposto

- **Poder e validade externa**: nove cenas determinísticas não têm barra de erro; a incerteza é de *amostragem de cenas*, não estatística. Não importar linguagem de significância; declarar antecipadamente quantas cenas novas e quais famílias, e aceitar que diferenças abaixo de ~0,1 pp são indecidíveis.
- **Multiplicidade**: o holdout só é válido com uma comparação primária pré-registrada; "comparar aquisição isolada e fusão isolada" cria três leituras — declare qual decide.
- **Métrica**: proibir erro relativo de volume como manchete quando a máscara cobre parte do volume; reportar litros absolutos *junto* da cobertura por cena (196/132/254/45 de 400 não são agregáveis).
- **Reuso**: os 27 frames já foram usados para diagnóstico; não podem sustentar seleção.
- Sem reivindicação de acesso a arquivos, hardware ou aprovações.
