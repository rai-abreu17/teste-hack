## Refutações ao protocolo de Sol (base no código)

**1. "Repetir pode reduzir ruído físico" é falso neste simulador — e o braço fixo, como descrito, é ou vazio ou confundido.**
O gerador é determinístico: `t` vem de `intersect_triangle`, quantizado a 1 mm; a única fonte estocástica é `hash32(i ^ seq*2654435761u)%10000 < dropout*100`. O hash depende **apenas do índice do raio e de `seq`** — não da pose. Consequências operacionais que Sol não extrai:
- Com `dropout=0`, três capturas fixas são **bit-idênticas**; a mediana por célula é a identidade e a união de suportes é exatamente o suporte de 64 raios. O braço não mede "ganho por número de capturas": mede zero por construção.
- Com `dropout>0` e `seq` variável, o braço fixo **recupera retornos perdidos** e aumenta a união de suportes sem qualquer ganho de ponto de vista. Isso é "perda de retorno", não amostragem.
Portanto o braço fixo precisa das duas sub-condições (`dropout=0` como teste de determinismo/regressão; `dropout>0` com `seq` distintos como eixo puro de nº de capturas). Sem isso, qualquer ganho do braço fixo será mal atribuído.

**2. Tilt ±10° não é "densificação angular" neutra; é troca de footprint com perda líquida.**
Os raios usam `half=tan(22.5°)=0,414`; a 40 cm do piso o footprint é ~33 cm, pouco maior que a caixa de 30 cm. Tilt de 10° desloca o centro do footprint em 0,40·tan10° ≈ 7,0 cm e leva a borda distante a 0,40·tan32,5° ≈ 25,5 cm do nadir (fora da caixa, sobre parede), enquanto a borda próxima recua para ~8,9 cm. Previsão: o braço de tilt **perde células de um lado**, ganha retornos de parede do outro, e aumenta descontinuidades — que o rasterizador descarta via `MAX_EDGE_M` e `|den|<1e-9`. Logo, queda de cobertura no braço de tilt pode ser FoV, não oclusão. Métrica obrigatória: histograma de `status` (0/1/2) e contagem de triângulos rejeitados por `MAX_EDGE` e por `den`, por braço.

**3. O braço de centros distintos está subdimensionado — risco de nulo interpretado como "ponto de vista não importa".**
Baseline de 5 cm (x .10→.20) com obstáculo de 15 cm e sensor a 40 cm: deslocamento de sombra = 5·15/(40−15) = **3 cm ≈ 2 células** de 1,5 cm. É preciso publicar esse deslocamento previsto por cena como poder de projeto; caso contrário o resultado nulo não distingue "sem paralaxe útil" de "oclusão intrínseca".

**4. Braços 3 e 4 não são um fator limpo.** Sem tilt, o centro em x=0,10 cobre x∈[−0,07; 0,27] e perde a faixa distante; com mira ao centro, muda-se **footprint e amostragem angular simultaneamente**. Paralaxe, FoV e densidade de amostragem estão confundidos; só a instrumentação do item 2 permite separá-los.

**5. Métricas e contrato.** `estimate()` devolve `total=None` salvo `covered==400`, e qualquer `below_reference` zera a leitura inteira (`state="unavailable"`) — em vistas oblíquas isso pode matar frames legítimos. A fusão **não pode** consumir `total`; deve operar sobre `heights` (média de triângulos por célula) e ser publicada como outro `algorithm_id`. Sol também omite: `reference_offset_m` é **escalar**; um vazio medido numa pose não corrige geometricamente outra pose — gerar vazio próprio por pose (`fill=0`) ou declarar viés.

**6. Comparação justa.** Domínios de suporte diferem por braço; erro relativo em domínios distintos não é comparável. Exigir **interseção de suportes entre os quatro braços** como domínio pareado, além do domínio próprio, e reportar a fração de massa da verdade contida no suporte.

**7. Correção da dicotomia de Sol.** "Erro menor sem mais cobertura ⇒ reconstrução" é grosseiro: com mesmo conjunto de células, mais retornos *dentro* delas melhoram a interpolação — ganho de amostragem, não de algoritmo. Adicionar: retornos por célula suportada e distância do retorno mais próximo ao centro da célula.

**Minha hipótese corrigida:** eu trataria célula com suporte como medida; o rasterizador preenche por interior de triângulo — 64 raios ⇒ ≤98 triângulos ⇒ até 400 células interpoladas já no baseline.
