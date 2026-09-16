Plano de investigação, sem executar os cálculos nem delegar tarefas.

**Hipóteses:** base interna quadrada com lado \(L=30\,\text{cm}\); material com altura uniforme \(H=12\,\text{cm}\); distância sensor–superfície \(h=20\,\text{cm}\); campo de visão completo \(\theta=60^\circ\) em cada eixo. A projeção é quadrada, centralizada e alinhada à base.

**Atribuições propostas:**

- **Engenheiro:** calcular o volume por \(V=L^2H\), em \(\text{cm}^3\), e converter usando \(1\,\text{L}=1000\,\text{cm}^3\). Calcular o lado projetado por \(w=2h\tan(\theta/2)\), em centímetros. Determinar a cobertura pela interseção entre projeção e base: \(f=\min(w,L)^2/L^2\), válida para o alinhamento e a centralização dados.
- **Investigador:** analisar separadamente mudança de enquadramento e visibilidade geométrica. Examinar se uma rotação com centro óptico fixo altera o segmento entre esse centro e um ponto da superfície, e verificar se um obstáculo continuaria interceptando esse segmento.
- **Pesquisador:** revisar, exclusivamente pelo contexto, a interpretação de FoV completo, os dois eixos ortogonais, as unidades e a distinção entre cobertura projetada e superfície visível.

**Critérios de decisão:** volume em litros; largura em centímetros; cobertura adimensional entre 0 e 1, também expressável em porcentagem; justificativa geométrica para a questão da oclusão. Nenhum resultado deve ser tratado como validação de servo ou arquitetura real.

**Incertezas e limitação:** os dados bastam para os cálculos ideais. Não há geometria específica de obstáculos para quantificar oclusão. A idealização exclui distorção e ruído, portanto não demonstra desempenho de um sensor real.
