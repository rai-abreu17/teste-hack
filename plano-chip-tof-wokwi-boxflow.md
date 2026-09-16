# BoxFlow — Plano de construção do sensor ToF simulado no Wokwi

**Objetivo:** criar, dentro do Wokwi, um componente que substitua o VL53L5CX (ToF multizona 8×8) para demonstrar o protótipo completo — circuito, firmware ESP32 e dashboard — antes de ter o sensor físico em mãos.

**Data:** setembro de 2026
**Autor:** Raí Abreu Machado

---

## 1. O que a pesquisa confirmou

### 1.1. Não existe LiDAR/ToF no Wokwi — nem pronto, nem feito pela comunidade

Varredura feita na documentação oficial, na lista de chips de exemplo, no índice de repositórios do GitHub e nos projetos públicos do Wokwi. Resultado:

- O único sensor de distância nativo é o `wokwi-hc-sr04` (ultrassônico, com slider de 2 a 400 cm).
- A lista oficial de custom chips de sensores tem: LM75A (I2C), DS18B20 (OneWire), teclado I2C e PCA9685 (PWM).
- **Nenhum chip ToF ou LiDAR existe**, nem oficial nem da comunidade.

> Isso não é um obstáculo — é argumento de apresentação. Você vai construir o primeiro.

### 1.2. Emular o VL53L5CX "de verdade" é inviável (e isso é tecnicamente defensável)

O VL53L5CX exige **upload de um firmware de ~84 KB via I2C a cada power-on**, e o protocolo interno (ULD — Ultra Lite Driver da ST) é opaco, sem mapa de registradores público. Reimplementar isso seria engenharia reversa de firmware proprietário, não simulação.

**Consequência de projeto:** o chip simulado terá **contrato próprio e documentado**, deixando explícito que aproxima o comportamento das zonas sem reproduzir a eletrônica nem o protocolo interno do sensor real.

### 1.3. A API de Custom Chips do Wokwi dá tudo que é necessário

Gratuita e disponível direto no editor do navegador: botão **"+"** no diagrama → **Custom Chip** → linguagem **C**.

Isso gera dois arquivos no projeto:

- `<nome>.chip.json` — pinagem, sliders e display
- `<nome>.chip.c` — a lógica do chip (compilada para WebAssembly)

No `diagram.json`, o componente aparece como `"type": "chip-<nome>"`.

**Recursos disponíveis na API:**

| Recurso | Uso no BoxFlow |
|---|---|
| GPIO (`pin_init`, `pin_write`) | Pino `INT` de data-ready |
| Dispositivo I2C escravo (`i2c_init`) | Callbacks `connect` / `read` / `write` / `disconnect` |
| Timers (`timer_init`, `timer_start`) | Taxa de ranging (15 Hz) |
| Atributos + `controls` | Sliders interativos durante a simulação |
| **Framebuffer RGBA** | **Heatmap 8×8 desenhado na tela do próprio chip** |
| `printf()` | Log na aba "Chips Console" |

O framebuffer é o achado mais valioso para a demonstração: o componente pode desenhar o mapa de zonas em tempo real dentro do diagrama.

### 1.4. Limitações que moldam o design

- `pin_init`, `i2c_init`, `timer_init`, `attr_init` e `framebuffer_init` **só podem ser chamados dentro de `chip_init()`**.
- O único tipo de controle disponível é `"range"` (slider) — não há botão, dropdown ou campo de texto.
  → **A cena precisa ser 100% paramétrica.**

---

## 2. Plano de execução

### Etapa 1 — Fechar o contrato antes de escrever código

Nomear o chip de forma que já denuncie a natureza dele: **`boxflow-tof-sim`**.

Escrever meia página definindo:

- Resolução: 8×8 zonas
- Unidade: milímetros
- Taxa: 15 Hz
- Endereço I2C: `0x29` (o mesmo do VL53L5CX, para o driver real cair no mesmo endereço depois)
- `WHO_AM_I` com valor **próprio** (ex.: `0xBF`) — **não** o da ST

> Esse documento é o que protege você na banca: "não clonei o sensor, especifiquei um substituto".

---

### Etapa 2 — Modelo geométrico da cena

É aqui que mora o valor real. O chip **não** devolve número aleatório: resolve a geometria.

**Configuração:**

- Sensor no topo, olhando para baixo, altura `H` (default 600 mm)
- FoV de 45°
- Cena de 600 × 600 mm (maquete de bancada)

**Para cada zona (i, j) do grid 8×8:**

1. Calcular o ângulo `θ` do raio central da zona
2. Projetar o raio no plano do chão
3. Verificar se o ponto cai dentro do retângulo da carga (largura × profundidade, posição x,y, altura h)
4. Distância:
   - acerta a carga → `(H − h_carga) / cos(θ)`
   - acerta o chão → `H / cos(θ)`
5. Somar ruído gaussiano configurável (±σ mm)
6. Marcar status por zona (válido / alvo fora de alcance)

> O fator `cos(θ)` é um detalhe pequeno que impressiona: mostra que você entendeu que zonas periféricas medem distâncias maiores que zonas centrais mesmo sobre um chão perfeitamente plano.

---

### Etapa 3 — Mapa de registradores

Padrão simples com auto-incremento de ponteiro ("escreve endereço → lê N bytes"):

| Registrador | Conteúdo |
|---|---|
| `0x00` | `WHO_AM_I` → `0xBF` |
| `0x01` | STATUS / data-ready |
| `0x02` | RESOLUTION (4×4 / 8×8) |
| `0x03` | START / STOP ranging |
| `0x10`–`0x8F` | 64 distâncias, `uint16` little-endian |
| `0x90`–`0xCF` | Status por zona |

O pino `INT` vai a nível **baixo** quando o frame fica pronto e volta ao ser lido — assim o firmware é orientado a interrupção, exatamente como seria com o sensor real.

---

### Etapa 4 — `boxflow-tof-sim.chip.json`

**Pinos:**
```
["VCC", "GND", "SCL", "SDA", "INT", "LPn"]
```

**Controls (sliders manipulados ao vivo na demonstração):**

| id | Faixa sugerida |
|---|---|
| `alturaCarga` | 0 – 500 mm |
| `larguraCarga` | 0 – 600 mm |
| `profundidadeCarga` | 0 – 600 mm |
| `posX` | −300 – 300 mm |
| `posY` | −300 – 300 mm |
| `ruidoMm` | 0 – 30 mm |

**Display:** 96 × 96 px → heatmap 8×8 com 12 px por zona

**Atributos no `diagram.json`** (não interativos): `sensorHeightMm` (600), `fovDeg` (45), `rangingHz` (15), `i2cAddress` (0x29)

---

### Etapa 5 — `boxflow-tof-sim.chip.c`

**Estrutura:**

- `chip_state_t` com: pinos, handles de atributo, framebuffer, buffer de 64 zonas e ponteiro de registrador
- `chip_init()` — inicializa pinos, I2C, timer, framebuffer e atributos (obrigatoriamente tudo aqui)
- **Callback do timer** (a cada 1/15 s): recalcula a cena, pinta o heatmap (azul = longe/chão, vermelho = perto/carga) e baixa o `INT`
- **Callbacks I2C**: `write` grava o ponteiro de registrador, `read` devolve o byte e incrementa o ponteiro

---

### Etapa 6 — Firmware ESP32 com camada de abstração

Esta é a peça que responde à pergunta "e quando o sensor físico chegar?".

Uma interface `ITofSensor` com duas implementações:

- `SimTofSensor` — fala com o chip do Wokwi
- `Vl53l5cxSensor` — usa a biblioteca da SparkFun/ST

Selecionadas por `#ifdef BOXFLOW_SIM`.

Todo o resto do firmware é **idêntico** nos dois casos:

- Cálculo de volume: `Σ (H − d_ij) × área_da_célula`
- Percentual de ocupação
- Serialização JSON e publicação

> Mensagem para os mentores: *"o código de produção já está escrito; o que falta é só trocar o driver."*

**⚠️ Armadilha concreta:** o buffer do `Wire` no ESP32 é de 128 bytes, e as 64 distâncias ocupam exatamente 128 bytes. **Leia em blocos de 32 bytes** para não esbarrar no limite.

---

### Etapa 7 — Caminho até o dashboard

O gateway público do Wokwi permite saída TCP/UDP, mas **não aceita conexão de entrada**. Portanto o fluxo é:

```
ESP32 (Wokwi) → WiFi "Wokwi-GUEST" → publica JSON em broker MQTT público
                                              ↓
                          Dashboard assina via MQTT sobre WebSocket (browser)
```

Conexão no firmware:

```cpp
WiFi.begin("Wokwi-GUEST", "", 6);  // canal 6 economiza ~4s de scan
```

Se preferir um broker local, aí sim é necessário rodar o **Wokwi IoT Gateway privado** na sua máquina.

> ⚠️ Não trafegue dado sensível pelo gateway público — a documentação avisa que o tráfego é monitorado.

---

### Etapa 8 — Verificação antes de apresentar

1. **Compilar o chip localmente** com `wokwi-cli chip compile` (ou `clang --target=wasm32-unknown-wasi`) para pegar erros antes do navegador
2. **Conferir o `WHO_AM_I`** na primeira leitura I2C
3. **Teste que fecha tudo:** comparar o volume calculado pelo firmware com o **volume analítico** da caixa configurada nos sliders
   → se bater dentro de ~5%, a demonstração está honesta e você tem um número concreto para mostrar

---

## 3. Nota sobre a narrativa da apresentação

O ponto forte desta demonstração **não** é "parece um LiDAR". É:

> *"Eu especifiquei um substituto, documentei o contrato, resolvi a geometria e isolei o driver atrás de uma interface."*

Mentor experiente valoriza muito mais isso do que um mock bonito — e é exatamente o oposto de esconder que o sensor ainda não chegou.

---

## 4. Referências

- [Getting Started with the Wokwi Custom Chips C API](https://docs.wokwi.com/chips-api/getting-started)
- [Custom Chip Definition (JSON)](https://docs.wokwi.com/chips-api/chip-json)
- [I2C Device API](https://docs.wokwi.com/chips-api/i2c)
- [GPIO pins API](https://docs.wokwi.com/chips-api/gpio)
- [Time simulation API](https://docs.wokwi.com/chips-api/time)
- [Attributes API](https://docs.wokwi.com/chips-api/attributes)
- [Framebuffer API](https://docs.wokwi.com/chips-api/framebuffer)
- [Compiling custom chips to WASM](https://docs.wokwi.com/guides/custom-chips-to-wasm)
- [ESP32 WiFi Networking](https://docs.wokwi.com/guides/esp32-wifi)
- [wokwi-hc-sr04 Reference](https://docs.wokwi.com/parts/wokwi-hc-sr04)
- [VL53L5CX firmware upload — SparkFun Community](https://community.sparkfun.com/t/vl53l5cx-firmware/63818)
