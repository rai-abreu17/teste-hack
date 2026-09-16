# M-001 — decisão de experimento, não escolha final de arquitetura

A arbitragem 009-astra concluiu o smoke. A missão real começou com Opus e Sol em execuções cegas separadas; as críticas seguintes receberam o texto oposto e trechos reais do código.

## Erros corrigidos antes da medição

- O rasterizador produtivo interpola somente dentro de triângulos locais. A hipótese de Opus de preenchimento fora do casco não é sustentada por esse código. O erro existente não deve ser atribuído a esse mecanismo.
- Raios do mock são uniformes no plano tangente, não uniformes em ângulo. Cobertura TIN não é área diretamente medida. Contar células com retorno é apenas um indicador de amostragem.
- Com dropout zero, as distâncias e grids repetidos são iguais; os bytes completos podem mudar por sequência, relógio e CRC. Com dropout positivo, o hash usa sequência e a repetição pode recuperar retornos.
- A viga do código está na faixa z=0,178–0,202 m. Não usar a altura da parede (0,15 m) como altura do obstáculo ao estimar sombras.

## Rodada escolhida

Comparar os mesmos cenários e orçamentos de raios dentro de cada grupo: repetição fixa, orientação com centro óptico fixo e centros ópticos distintos. Fundir grids de TIN local por mediana por célula; preservar lacunas e separar domínio próprio, interseção comum e total. Verdade apenas no avaliador.

Uma linha de vistas em X não resolve necessariamente as bordas em Y. Grupo secundário com quatro centros distribuídos nos dois eixos foi proposto antes dos resultados, acompanhado por controle fixo de quatro capturas e quatro orientações. O protocolo efetivamente congelado pelo engenheiro é a fonte final para a matriz executada.

Não atribuir causalmente ganho de TIN à eliminação de oclusão sem diagnóstico independente de visibilidade. Se disponível, o avaliador testa raios até a superfície verdadeira por célula; essa informação não entra no estimador.

Nenhum novo limite percentual de aprovação. As condições são ideais, sem validação óptica, mecânica ou de hardware. Resultados determinarão a próxima arquitetura candidata, inclusive quando forem negativos.
