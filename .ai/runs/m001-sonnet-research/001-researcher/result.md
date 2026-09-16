# Pesquisa direcionada M-001 — Síntese de evidências documentais

## 1. ST VL53L5CX (fonte primária — datasheet)
**URL:** https://www.st.com/resource/en/datasheet/vl53l5cx.pdf

**Fatos verificados (primário):**
- FoV de detecção: 45°×45° (H×V), 65° diagonal; zona de exclusão do receptor: 55,5°×61°×82° (Tabela 2, seção 2.2).
- **Condição de ensaio explícita:** alvo branco 88% refletância, perpendicular, a 1 m, sem luz ambiente (escuro), resolução 8×8, sharpener 14% (padrão), modo contínuo 15 Hz. Isso é uma condição de laboratório, não garantida em campo.
- Nota do datasheet: "Detection volume depends on the environment and sensor configuration... target distance, reflectance, ambient light level, sensor resolution, sharpener, ranging mode, and integration time" — ou seja, o próprio fabricante limita a validade do número de FoV a essas condições.
- FoI (campo de iluminação do VCSEL): 50°×50° a 75% do sinal máximo; 65°×65° a 10% do sinal máximo (seção 2.3).
- Máquina de estados de energia: LP idle, HP idle, Ranging (Tabela 4) — implica que o sensor precisa estar em HP idle antes de iniciar ranging; não há informação no trecho recuperado sobre comportamento dinâmico (sensor em movimento) nem sobre exigência de calibração por pose.

**Lacuna:** o texto recuperado não cobre re-calibração por ângulo de montagem (offset/tilt compensation), nem multi-zona (zone-based ranging) vs varredura por raio — funcionalidade citada em outras partes do datasheet completo (não presentes neste extrato). **Pesquisa adicional pendente:** seção de "ranging modes" e "zones" do datasheet completo, e nota de aplicação sobre compensação de ângulo de instalação.

**Implicação para BoxFlow:** o VL53L5CX é sensor de multi-zona ToF (8×8 zonas), não um "laser pontual"; a alegação de volume genérico não é suportada pelo trecho disponível — ele mede distância por zona, não topografia 3D nativa. Qualquer estimativa de volume dependeria de processamento adicional (fusão de zonas), não documentado aqui.

## 2. ABB LLT100 (fonte primária — página de produto/dados técnicos)
**URL:** https://new.abb.com/products/measurement-products/level/laser-level-transmitters/llt100

**Fatos (primário, com ressalva de material comercial):**
- Alcance: 0,5–30 m (líquidos), 0,5–100 m (sólidos), 0,5–200 m (posicionamento).
- Resolução 5 mm; acurácia típica ±11 mm.
- Laser 905 nm, Classe 1 (olho seguro), divergência do feixe <0,35° (visão geral) / <0,3° (seção óptica) — pequena inconsistência entre seções da própria página, deve ser tratada como imprecisão editorial, não erro técnico crítico.
- Largura do spot cresce com a distância (tabela): de 0,7 cm a 1 m até 108 cm a 150 m — evidência primária de que o "ponto" laser não é pontual em distâncias maiores.
- Marketing explícito: "No calibration necessary" — trata-se de afirmação comercial sobre o produto acabado (transmissor industrial completo com eletrônica de compensação), não uma prova de que sensores ToF em geral dispensam calibração de pose. **Deve ser separado como claim comercial, não como especificação técnica genérica.**
- MTBF 25 anos, IP66/67, classes de área explosiva (zona 1) — características de hardware industrial robusto, não comparável a MVP com ESP32/breakout.

**Implicação:** o LLT100 é laser de ponto único (single-beam) para nível, não gera topografia/volume por si — ele mede distância a um ponto e calcula volume via geometria do tanque configurada no software ("volume computation" nas features de software), isto é, **volume por modelo geométrico**, não por varredura de superfície. Isso corrobora a instrução de não confundir "volume calculado" com "topografia medida".

## 3. BinMaster 3DLevelScanner (fonte primária — página de marketing técnico)
**URL:** https://binmaster.com/3d-details/

**Alegação comercial a sinalizar explicitamente:** "the only level measurement technology that maps multiple points... to create a 3D representation" — **é claim de exclusividade de marketing**, não deve ser adotada como fato técnico. Não há dados de datasheet (faixa, acurácia, condições de ensaio) no trecho recuperado — apenas material de página de produto/vendas.

**Fatos técnicos parciais (primário, mas sem parâmetros quantitativos):** tecnologia acústica (baixa frequência), três transdutores, atribuição de coordenadas XYZ, software MultiVision para múltiplos bins. Sem números de alcance, resolução, ou condições de teste — **lacuna**: pesquisa adicional necessária no datasheet técnico do 3DLevelScanner (não recuperado nesta rodada) para validar faixa/acurácia/condições antes de qualquer comparação quantitativa com VL53L5CX ou LLT100.

**Distinção conceitual importante:** este é o único dos três equipamentos que mede topografia real por múltiplos pontos (mapeamento), diferente do LLT100 (ponto único + modelo geométrico) e do VL53L5CX (multi-zona ToF de curto alcance, não validado para volume neste extrato).

## Síntese para decisões do BoxFlow
1. **Sensor parado vs em movimento:** nenhuma das três fontes recuperadas trata explicitamente de medição durante movimento do sensor/integração dinâmica — lacuna a escalar ao investigador para teste físico.
2. **Calibração por pose:** claim "no calibration necessary" da ABB é específico do produto industrial acabado; não se aplica genericamente a ToF multi-zona tipo VL53L5CX, cujo próprio datasheet condiciona a leitura de FoV a parâmetros de configuração — sugere que compensação de ângulo/pose provavelmente é necessária em MVP, mas não confirmado nas seções recuperadas.
3. **Zone vs raio:** VL53L5CX = multi-zona (8×8); LLT100 = raio único; BinMaster = múltiplos pontos acústicos mapeados — são categorias tecnicamente distintas, não intercambiáveis para "volume genérico".
4. **MVP vs industrial:** LLT100 e BinMaster são hardware industrial certificado (IP66/67, zona 1, MTBF 25 anos); VL53L5CX é componente MVP (chip ToF), sem dados de robustez ambiental equivalente no trecho fornecido.

**Consultas pendentes (não realizadas):** datasheet técnico completo do BinMaster 3DLevelScanner; seção "ranging modes/zones" completa do VL53L5CX; nota de aplicação ST sobre compensação de ângulo de montagem.
