**BOXFLOW**

# **Relatório técnico da visita à COPI**

## *Consolidação da operação observada e validação de informações públicas para o projeto BoxFlow*

| Identificação | Informação |
| ----- | ----- |
| Local | Terminal Alfandegado COPI Porto, Porto do Itaqui, São Luís, MA |
| Finalidade | Organizar a visita técnica e converter os achados em requisitos verificáveis para o protótipo |
| Data do relatório | 11 de setembro de 2026 |
| Versão | 1.0 |

*Documento preparado a partir da transcrição integral da visita e de fontes públicas da COPI, do Porto do Itaqui e de fornecedores técnicos.*

# **1 Síntese técnica**

A visita confirma que o BoxFlow deve funcionar como uma camada independente de medição do estoque. O sistema precisa medir a geometria das pilhas, converter volume em toneladas com a densidade aparente de cada produto e reconciliar o resultado com as balanças existentes. A instalação deve ser não invasiva, suportar poeira, considerar a ausência de Wi-Fi no armazém e continuar útil mesmo quando os dados dos sistemas atuais apresentarem divergências.

As fontes públicas confirmam a estrutura central relatada na visita: o terminal alfandegado possui capacidade estática de 70 mil toneladas dividida em 10 boxes independentes. A descarga do navio ocorre pelo berço 101, com guindastes móveis, moega, correias transportadoras e balanças de fluxo automatizadas. A expedição ocorre pelos modais rodoviário e ferroviário.

# **2 Níveis de evidência**

Os dados abaixo preservam a diferença entre o que foi observado ou informado durante a visita e o que está publicado por fontes institucionais. Essa separação evita que um trecho incerto da gravação seja tratado como especificação definitiva.

| Classificação | Uso no relatório |
| ----- | ----- |
| Confirmado | A informação coincide com publicação institucional ou técnica identificável. |
| Relato consistente | A informação veio da visita e apresenta coerência geométrica ou operacional, mas não consta com o mesmo detalhamento em fonte pública. |
| Relato a confirmar | A informação veio da visita e precisa de validação direta com a COPI antes de orientar uma decisão de engenharia. |
| Correção de termo | A forma ouvida na gravação foi substituída pelo termo técnico sustentado pelas fontes consultadas. |

# **3 Informações institucionais confirmadas**

| Tema | Informação consolidada | Situação |
| ----- | ----- | ----- |
| Atuação | Descarga, transporte e armazenagem de fertilizantes e outros granéis de importação no Porto do Itaqui. | Confirmado |
| Armazenagem | Capacidade estática de 70 mil toneladas distribuída em 10 boxes independentes. | Confirmado |
| Descarga | Até 1.250 t/h no berço 101, com pesagem em balanças de fluxo automatizadas. | Confirmado |
| Expedição rodoviária | Capacidade pública de até 700 t/h para carregamento de caminhões. | Confirmado |
| Expedição ferroviária | Capacidade indicada pela COPI de 1.000 t/h. Em 2022, o Porto do Itaqui registrou desempenho de 733 t/h nos primeiros carregamentos. | Confirmado |
| Regimes aduaneiros | Entreposto aduaneiro, modelo de consumo e descarga direta com despacho antecipado. | Confirmado |
| Corredor ferroviário | Ligação do Porto do Itaqui ao Terminal Integrador de Palmeirante, no Tocantins, em parceria com a VLI. | Confirmado |

# **4 Configuração física dos boxes**

A divisão em sete boxes maiores e três menores foi informada na visita. A quantidade de três boxes menores resulta da diferença entre os 10 boxes confirmados publicamente e os sete boxes maiores mencionados na gravação.

| Parâmetro | Boxes maiores | Boxes menores | Validação |
| ----- | ----- | ----- | ----- |
| Quantidade | 7 | 3 | Relato e inferência |
| Capacidade relatada | Cerca de 7.500 t por box | Entre 4.000 t e 6.000 t por box | Relato consistente |
| Altura | 16 m | 16 m | Relato a confirmar |
| Largura | 17,5 m | 11,5 m | Relato a confirmar |
| Comprimento | 47,63 m estimados | 47,62 m | Cálculo e relato |
| Área de piso | 833,45 m² | 547,70 m² | Relato consistente |
| Regime citado | Despacho antecipado | Entreposto aduaneiro | Vínculo por box a confirmar |

A área do box maior permite estimar o comprimento em 47,63 m pela divisão de 833,45 m² por 17,5 m. No box menor, 11,5 m multiplicados por 47,62 m resultam em 547,63 m², diferença de apenas 0,07 m² em relação à área anotada. A distribuição de capacidade também é compatível com o total público: sete boxes de 7.500 t somam 52.500 t, deixando 17.500 t para os três menores, média de aproximadamente 5.833 t por box.

O fragmento anotado como “7,8, 10 m²” não foi incorporado às dimensões. A unidade, a grandeza e o elemento físico ao qual o número se refere precisam ser confirmados no local ou na planta do armazém.

# **5 Fluxo operacional consolidado**

## **5 1 Recebimento marítimo**

1\.  O navio atraca no berço 101 com o lote de fertilizante ou outro granel de importação.

2\.  Guindastes móveis transferem o material para a moega. O termo ouvido como “amoeba” ou “moeca” corresponde a moega.

3\.  As correias transportadoras levam o material da área do berço ao armazém. Balanças de fluxo automatizadas registram a massa recebida.

4\.  O operador autoriza o início do despejo no box. O ponto de descarga é central e forma uma pilha com geometria variável.

## **5 2 Armazenagem e transição entre lotes**

* A capacidade efetiva de cada box varia com o produto, sua densidade aparente, granulometria, umidade, compactação e forma da pilha.  
* Segundo a visita, o enchimento não utiliza toda a altura de 16 m e preserva aproximadamente 1 m a 2 m de folga. O limite operacional exato precisa ser confirmado.  
* Os produtos são cobertos com lonas, conforme relatado, o que pode ocultar parte da superfície e alterar a leitura óptica.  
* A limpeza ocorre entre lotes. Parte do processo é mecanizada e o acabamento é manual para reduzir resíduos do produto anterior.  
* Pode existir sobreposição entre a retirada do lote anterior e o início da entrada de outro produto. O sistema precisa distinguir estoque, recebimento, expedição e limpeza.

## **5 3 Expedição rodoviária**

1\.  O caminhão entra em uma área separada dos boxes e se posiciona na balança rodoviária.

2\.  O operador libera o carregamento e dois funis despejam o produto no veículo, conforme observado na visita.

3\.  A pesagem acompanha o limite de carga do caminhão. O fluxo deve ser interrompido antes de ultrapassar a capacidade autorizada.

4\.  A COPI divulga capacidade de expedição rodoviária de até 700 t/h.

## **5 4 Expedição ferroviária**

O trecho da transcrição que menciona saída por “navios” é incompatível com o fluxo institucional publicado. No Terminal COPI Porto, o fertilizante chega por navio e sai por caminhões ou composições ferroviárias. A palavra ouvida como “roupa” provavelmente corresponde a tulha, estrutura citada pela própria COPI na implantação do sistema ferroviário.

O Porto do Itaqui informou que o sistema ferroviário utiliza correias transportadoras e registrou, em 2022, 733 t/h nos primeiros carregamentos. A infraestrutura conecta São Luís ao terminal de Palmeirante.

# **6 Sistemas automação e dados**

| Termo da transcrição | Identificação consolidada | Uso e observação |
| ----- | ----- | ----- |
| iCOP ou iPOSH | SICOPI | Sistema de acompanhamento de descarga desenvolvido pela Blue Marble em parceria com a COPI. Não há evidência pública suficiente de um segundo sistema chamado iPOSH. |
| Elipse | Plataforma de supervisão industrial | O nome da família está correto. Elipse E3 é uma plataforma HMI e SCADA com integração a equipamentos, bancos de dados e sistemas de gestão; o produto e a versão instalados na COPI precisam ser confirmados. |
| Encoder | Sensor de posição ou velocidade | É um componente de automação, não um sistema completo. Pode medir rotação e velocidade de correia, mas sua aplicação exata na tentativa anterior da COPI deve ser detalhada. |
| Domínio próprio | Hospedagem ou domínio corporativo | Relato da visita. É necessário separar domínio de internet, servidor interno, banco de dados e infraestrutura de automação. |

A integração com SICOPI ou com a plataforma Elipse pode fornecer identificação do lote, produto, box, início e fim da operação, dados de balança e estados dos equipamentos. Esses dados devem enriquecer o BoxFlow, mas não substituir sua medição independente. A equipe relatou situações em que valores do sistema existente estavam incorretos; por isso, a arquitetura deve preservar a origem, o horário e a qualidade de cada medida.

# **7 Restrições do ambiente**

| Restrição | Efeito no protótipo | Diretriz |
| ----- | ----- | ----- |
| Sem Wi-Fi no armazém | O ESP32 não pode depender de uma rede sem fio convencional para telemetria contínua. | Prever processamento local e saída cabeada ou gateway industrial. Confirmar a alternativa de comunicação citada na visita. |
| Proibição de furar vigas e paredes | A montagem não pode alterar a estrutura civil sem autorização. | Usar suportes não invasivos, estruturas independentes ou pontos aprovados pela empresa responsável pela instalação. |
| Ponto central de despejo | A moega e o fluxo de material ocupam a região superior central e criam oclusões. | Posicionar sensores nas laterais e testar mais de um ponto de vista. |
| Poeira e limpeza | Partículas podem degradar lentes, conectores e medições. | Selecionar invólucro industrial, proteção de lente e procedimento de limpeza e inspeção. |
| Lonas sobre o produto | A lona pode esconder a superfície e produzir geometrias artificiais. | Registrar estado com e sem lona e bloquear ou qualificar leituras quando a superfície estiver coberta. |
| Operações simultâneas | Entrada e saída próximas no tempo podem gerar variações rápidas e ambíguas. | Modelar estados operacionais e registrar eventos de transição por box. |

