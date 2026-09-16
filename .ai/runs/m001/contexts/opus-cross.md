# M-001 — primeira análise independente

Problema: estimar volume de material em maquete de box com hardware acessível, cobertura incompleta e oclusões; distinguir demonstração MVP e evolução industrial. Nenhum sensor, movimento ou prior está escolhido definitivamente. Não procure consenso antes de responder.

## Evidência prévia (SIMULADO, não repetir)

Pacote existente: box 30x30 cm, paredes15cm, sensor central a40cm do piso. Mock8x8 representa64 raios centrais com FoV45 graus por eixo e primeira interseção de raios com triângulos; distâncias quantizadas a1mm. Não simula mistura de retornos por zona, ruído óptico, reflexões, interferência ou driver físico VL53L5CX. Protocolo próprio0x42, quadro704bytes. ToF é candidato, não produto industrial escolhido.

O estimador atual triangula alturas relativas ao vazio e integra400 células de1,5cm; 400células não são400medidas. Total só publicado com suporte em todas; caso parcial mantém total nulo. Ground truth fica somente no avaliador.

Resultados existentes em docs/EXPERIMENTOS_64_ZONAS.md e build/experiments/: TIN pirâmide central verdade0,5625L, estimado0,660934L (+17,50%). Em21 posições amplitude16,11pp. Modelo piramidal condicionado à forma reduziu amplitude para0,98pp e2,32pp em60casos reservados da mesma família. Isso não valida forma arbitrária. Recortes e gates de inclinação não solucionaram erro do total. Vazio medido removeu desvio vertical comum, mas não interpolação ou deriva posterior. Camada7,5cm coberta64% a40cm,81% a45cm,100% a48cm,73% a49cm e49% a50cm; elevar não é monotônico por paredes/retornos. Com viga TIN parcial70%; perfil ideal denso75%, logo aumentar densidade não remove todos os pontos cegos.

## Código reaproveitável

wokwi/boxflow-lidar.chip.c contém Scene com origin/yaw/tilt e gerador geométrico; tools/scene_dump.c harness C exporta os mesmos quadros binários. Atualmente CLI aceita fill,shape,centerX,obstacle,dropout,range,seq,yaw,tilt,sensorZ; ainda não originX/Y. experiments/truth.py tem volume analítico e recorte exato por célula independente do estimador. server/geometry.py decodifica quadro com pose; experiments/estimators.py tem TIN e ajuste condicionado. Famílias existentes: pirâmide,duas pilhas,prisma,rampa,camada; viga e perdas configuráveis. E0–E4 já executados; rotação,múltiplas vistas,fusão ainda não comparadas quantitativamente. Wokwi ponta a ponta/hardware físicos pendentes.

## Tarefa nesta rodada

Apresente análise independente de até900palavras em português: problema observável, restrições, mecanismos candidatos, hipóteses improváveis, lacunas de evidência e até3experimentos discriminantes. Priorize comparação justa de sensor fixo, rotação com mesmo centro óptico,centros ópticos distintos e reconstrução. Distinguir ganho por número de capturas de ganho por ponto de vista. O experimento deve preservar verdade fora do estimador e comparar total e domínio parcial corretamente; não transformar extrapolação em cobertura medida. Nenhum percentual de aceitação novo arbitrário.

Proponha uma rodada pequena e reprodutível usando o código existente, sem repetir E0–E4 nem alterar dashboard ou firmware produtivo. Evidência física externa não fornecida deve ser marcada como lacuna ou hipótese, nunca inventada. Não use ferramentas nesta análise textual; a pesquisa documental e a implementação são tarefas separadas. Não receba respostas de outros agentes nesta primeira rodada.


TAREFA CRÍTICA CRUZADA: tente refutar a análise do outro especialista abaixo. Não faça votação nem procure concordar. Use o código fornecido para corrigir mecanismo causal, métricas e controles. Até600palavras em português. Concentre-se no experimento de3capturas: fixa repetida, tilts(-10,0,+10) mesmo centro, centros x(.10,.15,.20)y.15z.40 sem tilt, centros apontados ao centro. Mesmos192raios/cena, baseline64. Fusão proposta: mediana por célula dos TINs locais, união de suportes; não criar Delaunay global e não chamar célula interpolada de área medida. Ground truth só avaliador. Resultados ainda não existem; isto é revisão de protocolo. Avalie quais conclusões podem ou não ser sustentadas. Distinga margens não suportadas, interpolação ruim, oclusão intrínseca, FoV e perda de retornos. Sem ferramentas nesta chamada.

CÓDIGO REAL rasterizador:
    verts = [points[k] for k in indices]
    if any(v is None for v in verts):
        return
    a, b, c = verts
    # Local adjacency plus a maximum 3D edge; never bridge arbitrary distant points.
    if any(math.dist(p,q) > MAX_EDGE_M for p,q in ((a,b),(b,c),(c,a))):
        return
    den = (b[1]-c[1])*(a[0]-c[0]) + (c[0]-b[0])*(a[1]-c[1])
    if abs(den) < 1e-9:  # Vertical faces do not have horizontal integration area.
        return
    ix0 = max(0, math.ceil(min(v[0] for v in verts)/CELL-0.5))
    ix1 = min(NX-1, math.floor(max(v[0] for v in verts)/CELL-0.5))
    iy0 = max(0, math.ceil(min(v[1] for v in verts)/CELL-0.5))
    iy1 = min(NY-1, math.floor(max(v[1] for v in verts)/CELL-0.5))
    for iy in range(iy0, iy1+1):
        y = (iy+0.5)*CELL
        for ix in range(ix0, ix1+1):
            x = (ix+0.5)*CELL
            wa = ((b[1]-c[1])*(x-c[0]) + (c[0]-b[0])*(y-c[1]))/den
            wb = ((c[1]-a[1])*(x-c[0]) + (a[0]-c[0])*(y-c[1]))/den
            wc = 1-wa-wb
            if min(wa,wb,wc) < -1e-7:
                continue
            height = sum(w*(v[2]-base(v[0],v[1])-reference_offset_m) for w,v in ((wa,a),(wb,b),(wc,c)))
            if height < -BELOW_REFERENCE_TOLERANCE_M:
                continue
            k = iy*NX+ix
            sums[k] += max(0, height)
            counts[k] += 1


def estimate(data, reference_offset_m=0.0):
    decoded = decode_frame(data, reference_offset_m)
    points, cols, rows = decoded["points_by_ray"], decoded["columns"], decoded["rows"]
    sums, counts = [0.0]*(NX*NY), [0]*(NX*NY)
    for row in range(rows-1):
        for col in range(cols-1):
            a = row*cols+col
            raster_triangle(points,(a,a+1,a+cols+1),sums,counts,reference_offset_m)
            raster_triangle(points,(a,a+cols+1,a+cols),sums,counts,reference_offset_m)
    heights = [s/n if n else None for s,n in zip(sums,counts)]
    covered = sum(h is not None for h in heights)
    coverage = covered/(NX*NY)
    observed = sum(h for h in heights if h is not None)*CELL*CELL if covered else None
    # Ambiguity from missing cells only. This is not an uncertainty interval.
    missing_max = sum(max(0,HEIGHT-base((k%NX+0.5)*CELL,(k//NX+0.5)*CELL)-reference_offset_m)*CELL*CELL
                      for k,h in enumerate(heights) if h is None)
    state = "valid" if covered == NX*NY else "partial" if covered else "unavailable"
    reason = ("Todas as células têm suporte local; validade restrita ao modelo simulado." if state == "valid" else
              "Há células sem observação; o volume mostrado cobre somente a região reconstruída." if covered else
              "Não há superfície suficiente para calcular volume.")
    if decoded["excluded"]["below_reference"]:
        state = "unavailable"
        reason = "Pontos abaixo da referência; verificar pose e calibração."
    total = observed if state == "valid" else None
    public = {k:v for k,v in decoded.items() if k not in ("points_by_ray","readings")}
    public.update({"algorithm_id": ALGORITHM_ID, "precision_status":"not_validated", "measurement_state": state, "reason": reason,

RAIOS E DROPOUT REAIS:
    int i=row*s.cols+col;
    // IDEAL pinhole zone centers, nominal 45 degrees on each axis (ST Table 2).
    // Finite zone response, histograms and optical distortion are not simulated.
    float half=tanf(22.5f*BF_PI/180);
    float sx=(2*((float)col+.5f)/8-1)*half,sy=(2*((float)row+.5f)/8-1)*half;
    Vec u=unit(vec(sx,sy,-1)),d=rotate(u,s.yaw,s.tilt);
    float t=INFINITY;
    for(int k=0;k<m.count;k++)t=fminf(t,intersect_triangle(s.origin,d,m.triangles[k]));
    if(s.obstacle)t=fminf(t,intersect_beam(s.origin,d));
    uint8_t status=isfinite(t)?(t<=s.range?1:2):0;
    if(hash32((uint32_t)i^(seq*2654435761u))%10000 < (uint32_t)(s.dropout*100))status=0;
    uint8_t *r=frame+BF_HEADER+i*BF_RECORD;
    put16(r,status==1?(uint16_t)lroundf(t*1000):0);
    put16(r+2,(uint16_t)(int16_t)lroundf(u.x*32767));
    put16(r+4,(uint16_t)(int16_t)lroundf(u.y*32767));
    put16(r+6,(uint16_t)(int16_t)lroundf(u.z*32767));r[8]=status;


ANÁLISE SOL A CONTESTAR:
A grandeza desejada — volume total — não é diretamente observável com 64 primeiras interseções. Os quadros observam distâncias ao longo de raios; alturas, superfícies entre raios e regiões ocultas são inferências. Portanto, é necessário separar três domínios: pontos efetivamente retornados, células preenchidas por interpolação e células estimadas por extrapolação. Somente o primeiro constitui cobertura medida.

**Restrições e mecanismos candidatos**

- Sensor fixo: fornece uma única perspectiva, sujeita a discretização angular, oclusões e paredes. Repetir a captura pode reduzir ruído físico, mas no simulador determinístico atual tende apenas a duplicar retornos.
- Rotação no mesmo centro óptico: desloca a malha angular sobre a cena e pode melhorar amostragem/interpolação. Entretanto, não cria linhas de visada capazes de contornar uma oclusão geométrica. Seu benefício esperado é densificação angular, não observação independente de superfícies escondidas.
- Centros ópticos distintos: podem revelar regiões ocultas e aumentar cobertura geométrica real. Exigem registrar corretamente cada pose antes da fusão.
- Reconstrução: TIN é reutilizável e não presume uma família específica, mas interpola entre amostras e pode atravessar descontinuidades. O ajuste piramidal deve permanecer apenas como comparador condicionado à forma; o resultado reservado conhecido não sustenta seu uso geral.
- Fusão deve operar sobre retornos transformados para um referencial comum. Duplicatas ou múltiplos raios sobre a mesma região não devem ser contados como novas células cobertas.

É improvável que apenas aumentar capturas fixas, densidade angular ou altura resolva o total: os resultados existentes já mostram pontos cegos geométricos, não monotonicidade com altura e erro sistemático de interpolação. Também é improvável que rotação pura no mesmo centro recupere superfícies totalmente ocultas. Essas são previsões geométricas, não resultados ainda medidos.

**Lacunas de evidência**

Não há comparação quantitativa entre repetição, rotação, translação e fusão. Também faltam mistura de retornos por zona, ruído, reflexões, interferência, deriva e comportamento físico do VL53L5CX. Logo, o experimento proposto testa apenas geometria simulada e reconstrução; não qualifica hardware nem desempenho industrial. Persistem ainda dúvidas sobre registro de pose, rejeição de raios por parede/faixa e sensibilidade a pequenas perturbações de posição.

**Rodada pequena e reprodutível**

1. **Separar número de capturas de ponto de vista.** Para cada cenário reservado, gerar quatro condições com o mesmo número \(K=4\) de quadros: pose fixa repetida; quatro yaws no mesmo centro; quatro centros distintos sem rotação; quatro centros distintos com orientação dirigida ao box. Incluir também a referência de um quadro fixo. Usar as mesmas cenas, quantização, sensorZ, dropout e range em todas as condições. Como o CLI ainda não expõe `originX/Y`, a única alteração proposta é adicioná-los ao harness `scene_dump.c`, reutilizando `Scene`; não tocar em firmware ou dashboard.

2. **Comparar cobertura antes da reconstrução.** Transformar cada retorno válido pelo `server/geometry.py`, fundir por pose e calcular: retornos válidos, rejeições por motivo, células com suporte de observação e cobertura sobre as mesmas 400 células. A união de suportes mede ganho de ponto de vista; duplicatas da pose fixa medem apenas ganho por capturas. Relatar também sobreposição entre quadros. Interpolação TIN não aumenta essa cobertura.

3. **Avaliar reconstrução em domínios explícitos.** Executar o mesmo TIN em todas as condições. No domínio suportado, comparar volume estimado parcial com o recorte exato por célula de `truth.py`, informando erro absoluto, erro relativo somente quando a verdade parcial for não nula, cobertura e rejeições. Para o domínio total, manter resultado nulo enquanto faltar suporte, conforme o contrato atual. Se uma variante experimental produzir total por preenchimento de lacunas, rotulá-lo explicitamente como extrapolado e avaliá-lo separadamente contra a verdade total, sem reclassificar suas células como cobertas.

A matriz pode usar poucas instâncias já geráveis das famílias pirâmide, duas pilhas, prisma, rampa e camada, incluindo viga e uma condição de perdas, com sementes e poses fixadas em manifesto. Cada configuração deve receber exatamente as mesmas cenas e poses. A hipótese discriminante é: repetição fixa não altera geometria; yaw melhora amostragem, mas pouco a oclusão; centros distintos aumentam suporte onde há novas linhas de visada. Qualquer redução de erro sem aumento de cobertura deverá ser atribuída à reconstrução, não ao sensor.

Esta é uma especificação; nenhum experimento foi executado nesta rodada.
