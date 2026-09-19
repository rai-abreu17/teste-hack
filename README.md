# BoxFlow — maquete de 30 × 30 cm com perfil VL53L5CX 8×8

Pacote para demonstração no Wokwi com ESP32 clássico, mock geométrico de 64 zonas, I²C, envio HTTP, reconstrução de volume em m³, dashboard e SQLite. Piso de **30 × 30 cm**, paredes de **15 cm**, sensor centralizado a **40 cm do piso**. Referência `bench-vl53-30cm-v3`; protocolo binário v2.

O mock representa cada zona por um raio central ideal com FOV nominal de 45° horizontal × 45° vertical. Não emula os registradores, o firmware interno ou a resposta óptica completa do VL53L5CX. O endereço I²C 0x42 e seu protocolo são próprios. O firmware usa a interface `ITofSensor` e o backend `SimTofSensor`, selecionado por `BOXFLOW_SIM=1`. **Ainda não existe backend para conectar diretamente ao sensor físico:** `BOXFLOW_SIM=0` falha explicitamente na compilação até essa integração ser implementada. O sensor físico, o driver e a calibração exigem ensaios próprios.

Esta é a configuração de 30 cm solicitada para o hackathon. A versão anterior tinha base de 60 cm; o primeiro protótipo simulava um box de 8 × 6 × 6 m. Nenhuma dessas dimensões é uma medição do terminal. Para o MVP, recomendamos o VL53L5CX e esta maquete; consulte [MONTAGEM_30CM.md](docs/MONTAGEM_30CM.md) e [COMPARACAO.md](docs/COMPARACAO.md).

Na pirâmide principal, a referência é 0,0005625 m³ (0,5625 L) e a estimativa simulada é 0,000660934 m³ (+17,50%). Os testes funcionais passam, mas não aprovam precisão de 5%. Resultados completos: [TESTES.md](docs/TESTES.md).

**Atualização de 13/09/2026:** a [comparação experimental dos 64 pontos](docs/EXPERIMENTOS_64_ZONAS.md) executa o plano E0–E4 do briefing. Um ajuste condicionado à forma piramidal reduziu a amplitude do erro de 16,11 para 0,98 ponto percentual na varredura de posição; em 60 casos reservados da mesma família, a amplitude foi 2,32 pontos. Recortes, filtros por inclinação e vazio medido também foram testados, com área e limitações explícitas. São ferramentas offline em `experiments/`; o dashboard continua usando o TIN acima. A execução completa no Wokwi permanece pendente, conforme o relatório.

## Executar o receptor e o dashboard

Requer Python 3.10 ou superior. Extraia o ZIP e abra o terminal na pasta que contém este README:

```bash
python server/app.py
```

Abra http://127.0.0.1:8000 no navegador. Em outro terminal na mesma pasta:

```bash
python tools/replay_demo.py
```

No Windows, pode usar `py -3`; em Linux/macOS, `python3`. Servidor e dashboard usam somente a biblioteca padrão do Python. O replay envia **17 cenas binárias**, e o receptor recalcula os volumes. O transporte aparece como `native-c-test`; não é execução do ESP32. Use `--loop` para repetir. Não execute replay e Wokwi simultaneamente para o mesmo dispositivo.

O banco padrão é `server/boxflow-vl53-30cm-v3.sqlite3`. Use um banco novo para esta referência: os resultados antigos têm outra geometria. O histórico é persistido, e o painel exibe até 80 entradas. Ctrl+C encerra os processos.

## Frontend oficial (boxflow-dashboard) — BOX-03 ao vivo

O dashboard estático em `server/static/` (acima) é só uma referência de depuração dos dados brutos. **O frontend oficial é o projeto Angular irmão `boxflow-dashboard`**, que consome este backend em tempo quase real para o box instrumentado da demonstração, **BOX-03**. Os outros 9 boxes continuam com dados cadastrais/ilustrativos (mock) — só o BOX-03 reflete leituras reais deste backend.

### Como funciona

- O receptor aceita qualquer `X-Box-ID` bem formado (não é mais fixo em `BOX-DEMO-01`); `wokwi/config.h` e `tools/replay_demo.py` já usam `BOX-03` por padrão.
- `/api/latest` aceita um parâmetro opcional `?box_id=BOX-03` para filtrar a última leitura e o histórico daquele box especificamente.
- Cada leitura agora inclui `occupancy_fraction` (0 a 1): o volume observado na maquete normalizado pela capacidade de referência da bancada (`REFERENCE_CAPACITY_M3`, calibrada pela pirâmide central usada nas amostras `entrada-25/50/75/100`). Isso é o que permite ligar a medição em escala de bancada (frações de litro) a uma representação em escala industrial (milhares de m³) no Angular: o `TelemetryService` do dashboard multiplica `occupancy_fraction` pela capacidade cadastrada do box real, então o volume exibido é sempre "volume equivalente da simulação", nunca o volume físico bruto do sensor.
- Também inclui `measurement_profile` (hoje sempre `"bench"`), reservado para, no futuro, distinguir a leitura de bancada de um eventual simulador de cena industrial.

### Testando a medição de volume você mesmo

1. Rode o receptor aqui (se ainda não estiver rodando):
   ```bash
   python server/app.py
   ```
2. Em outro terminal, na pasta `boxflow-dashboard` (repo irmão), instale as dependências (só na primeira vez) e suba o Angular — o `proxy.conf.json` já encaminha `/api/**` para `http://127.0.0.1:8000`:
   ```bash
   npm install
   ng serve
   ```
3. Abra `http://localhost:4200/boxes/b3` (detalhe do BOX-03) ou `http://localhost:4200/dashboard` — os dois já mostram dados reais assim que existirem.
4. Gere leituras. Duas formas:
   - **Progressão limpa de enchimento** (recomendado para ver o efeito visual, evita as cenas de teste como oclusão/redistribuição que fazem o volume "pular"):
     ```bash
     python tools/replay_demo.py --only vazio,entrada-25,entrada-50,entrada-75,entrada-100 --interval 4
     ```
   - **Sequência completa de validação** (17 cenas, inclui casos de borda como oclusão e fora de alcance):
     ```bash
     python tools/replay_demo.py
     ```
   - **Simulação real no Wokwi**: siga "Montar no Wokwi" abaixo; o firmware já envia para `BOX-03` a cada 3 segundos.
5. Observe o card do BOX-03 (Dashboard e lista de Boxes) e a página de detalhe: volume, % de ocupação, cobertura e a pilha na visualização 3D atualizam sozinhos a cada ~2 segundos, sem precisar recarregar a página. Os outros boxes continuam estáticos (mock) — é esperado.

Como o volume de referência (`REFERENCE_CAPACITY_M3`) é calibrado pela forma piramidal usada nas amostras `entrada-*`, a sequência acima produz uma ocupação crescente e suave (aproximadamente 0% → 28% → 58% → 88% → 100%, com alguma variação por causa do erro de reconstrução do TIN, ver [TESTES.md](docs/TESTES.md)). Amostras de outras formas (`prisma`, `rampa`, `camada`) podem saturar em 100% — é o comportamento esperado, não um erro.

## Montar no Wokwi

1. Abra o [modelo ESP32](https://wokwi.com/projects/new/esp32).
2. Em Add a new part, procure Custom Chip, use o nome `boxflow-lidar`, selecione C e crie o chip.
3. Substitua as abas `.chip.c` e `.chip.json` pelos arquivos em `wokwi/`.
4. Substitua `sketch.ino` e `diagram.json`; adicione `config.h`. `libraries.txt` fica vazio porque o mock usa somente bibliotecas do núcleo ESP32.
5. Use o diagrama e os controles atuais, com 8×8 fixo. Configure `API_BASE` e inicie a simulação.
6. Confira a linha `64 zonas, 704 bytes, CRC OK` e HTTP 200. A execução completa ESP32 → mock → gateway → HTTP permanece uma verificação manual pendente.

O fluxo de menus foi observado na versão anterior. Não há projeto publicado nesta entrega, nem componente nativo VL53L5CX presumido. O binário do custom chip está incluído; o editor pode compilá-lo a partir do C.

## Conectar o receptor

O endpoint padrão é `http://host.wokwi.internal:8000`. Para acessá-lo, execute o [Wokwi IoT Gateway](https://github.com/wokwi/wokwi-iot-gateway/releases) no computador do receptor e habilite o gateway privado no editor. O recurso depende do plano Wokwi. O gateway público não acessa o `127.0.0.1` do seu computador. Consulte a [documentação de rede](https://docs.wokwi.com/guides/esp32-wifi).

Também é possível hospedar o receptor ou usar um túnel e configurar a URL acessível em `API_BASE`. Para escutar em interfaces de rede:

```bash
python server/app.py --host 0.0.0.0 --port 8000
```

Para HTTPS, configure TLS na hospedagem/proxy e a CA PEM em `ROOT_CA`. O firmware não desabilita verificação de certificado. O token opcional `BOXFLOW_TOKEN` no servidor deve corresponder a `API_TOKEN`; protege escritas, não consultas. Não há endpoint hospedado incluído.

## Circuito e controles

| ESP32 | Mock | Ligação |
| --- | --- | --- |
| 3V3 | VCC | Alimentação lógica representada |
| GND | GND | Referência comum |
| GPIO 21 | SDA | I²C com pull-up de 4,7 kΩ |
| GPIO 22 | SCL | I²C a 400 kHz com pull-up de 4,7 kΩ |

| Controle | Função |
| --- | --- |
| `fill` | 0–100% da altura máxima de 10 cm; não é percentual volumétrico |
| `shape` | 0 pirâmide; 1 duas pilhas; 2 prisma; 3 rampa; 4 camada |
| `centerX` | 0,10–0,20 m; não desloca duas pilhas ou camada |
| `sensorX/Y/Z` | Pose; padrão (0,15; 0,15; 0,40) m |
| `yaw`, `tilt` | Orientação do sensor |
| `obstacle` | Viga de oclusão |
| `rangeM` | Corte induzido de alcance entre 0,2 e 4 m; não modela iluminação |
| `dropout` | Ausência de retorno induzida |
| `freeze`, `i2cFault` | Sequência congelada e NACK |

A captura virtual dura 100 ms, com tentativa a cada 3 segundos. O framebuffer mostra as 64 zonas, escala zero a um metro ou mais, cinza sem retorno e rosa fora do corte. A escala de cor não altera distâncias ou alcance.

## Interpretar o painel

O estimador recebe distâncias, direções, pose e referência vazia. Não recebe forma, centro ou preenchimento da carga. Interpola alturas relativas à base entre vizinhos e integra uma grade de 20×20 células de 1,5 cm. As 400 células não são 400 medições independentes.

`valid` significa suporte em todos os centros de célula, não precisão aprovada. `partial` mantém total nulo; `unavailable` indica ausência/falha/calibração incompatível; `stale` aparece após 45 segundos. Leituras anteriores ficam identificadas. Ausência de retorno não vira volume zero. A ambiguidade das lacunas não é intervalo de confiança nem corrige o erro observado.

## Compilar e reproduzir

O pacote inclui firmware e WASM da referência atual. Alterar `config.h` exige recompilar o ESP32. Arduino CLI com Arduino-ESP32 3.3.0:

```bash
arduino-cli core update-index --additional-urls https://espressif.github.io/arduino-esp32/package_esp32_index.json
arduino-cli core install esp32:esp32@3.3.0 --additional-urls https://espressif.github.io/arduino-esp32/package_esp32_index.json
python tools/build_firmware.py
wokwi-cli chip compile wokwi/boxflow-lidar.chip.c -o wokwi/boxflow-lidar.chip.wasm
```

O script mantém o `.chip.c` fora da compilação Arduino e contorna automaticamente a falha do toolchain Windows em caminhos com caracteres não ASCII. No VS Code, abra `wokwi/`, configure a extensão/licença Wokwi e execute Start Simulator. `wokwi.toml` aponta aos binários em `build/firmware/`. A execução por CLI exige token apropriado.

```bash
python tools/generate_samples.py
python -m unittest discover -s tests -v
node tests/test_wasm.mjs
python tools/reference_sensitivity.py --plot
python tools/compare_resolution.py
python tools/check_mounting.py
```

Geração nativa e comparação exigem GCC ou Clang; teste WASM exige Node 18+. A figura de sensibilidade exige matplotlib, que não é necessário para servidor, replay ou resultados JSON. Omita `--plot` para gerar somente os dados.

## Passar ao sensor físico

Use uma placa VL53L5CX compatível com os níveis elétricos do ESP32 e confira sua documentação. Integre o [ULD da ST](https://www.st.com/resource/en/user_manual/um2884-a-guide-to-using-the-vl53l5cx-multizone-timeofflight-ranging-sensor-with-wide-field-of-view-ultra-lite-driver-uld-stmicroelectronics.pdf) ou a [biblioteca Arduino aberta da SparkFun](https://github.com/sparkfun/SparkFun_VL53L5CX_Arduino_Library). Inicialização, firmware do sensor e estados por zona não são emulados pelo protocolo do mock.

Calibre pose, correspondência espacial das zonas e box vazio. Preserve a validade de cada retorno. Adapte origem e relógio no contrato: o receptor desta versão aceita apenas `simulation`. O [datasheet](https://www.st.com/resource/en/datasheet/vl53l5cx.pdf) documenta limites dependentes de luz, alvo e configuração; o alcance máximo anunciado não é uma garantia para todas as condições. A integração física e a precisão não foram validadas.
