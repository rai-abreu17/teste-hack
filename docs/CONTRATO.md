# Contrato binário v2 — referência de maquete v3

Referência `bench-vl53-30cm-v3`; algoritmo `tof-zone-tin-grid-v3`; origem `simulation`. Protocolo próprio do mock em I²C 0x42, não compatível com registradores/ULD do VL53L5CX.

## Aquisição

SDA GPIO 21, SCL GPIO 22, 400 kHz. Comando `FF FF A1` congela os controles e inicia captura virtual de 100 ms. Byte pronto zero durante captura; sequência incrementada após conclusão. O quadro fica imutável até a captura seguinte. `freeze` mantém sequência; `i2cFault` induz NACK. Timeout no ESP32: 2.500 ms.

Ponteiro I²C de dois bytes big-endian, repeated START e até 28 bytes por leitura. Conteúdo multibyte little-endian. O firmware lê cabeçalho, corpo e cabeçalho novamente; exige igualdade e CRC. Fora do quadro, resposta 0xFF.

| Offset | Bytes | Conteúdo |
| --- | --- | --- |
| 0 | 4 | ASCII BFLD |
| 4 | 1 | Protocolo 2 |
| 5 | 1 | 1 pronto; 0 ocupado |
| 6 | 2 | Cabeçalho 64 |
| 8 | 4 | Sequência uint32 |
| 12 | 8 | Início no relógio virtual, ms uint64 |
| 20 | 4 | Duração 100 ms |
| 24 | 2 | Colunas 8 |
| 26 | 2 | Linhas 8 |
| 28 | 2 | Registro 10 bytes |
| 30 | 2 | Referência geométrica 3 |
| 32 | 12 | float32 x, y, z em metros |
| 44 | 12 | float32 yaw, tilt, roll; roll zero |
| 56 | 2 | Corte de alcance 200–4.000 mm |
| 58 | 2 | Corpo 640 bytes |
| 60 | 4 | CRC32 IEEE |

Cada registro `<HhhhBB`: distância mm uint16, direção local x/y/z int16 multiplicada por 32767, validade e reservado zero. Validade 0 sem retorno, 1 válido, 2 fora do corte. Distância inválida zero não é altura ou volume zero. Total: 704 bytes.

CRC32 IEEE dos bytes 0–59 concatenados com 64–703, polinômio refletido 0xEDB88320, inicialização/XOR 0xFFFFFFFF. Em Python: `zlib.crc32(payload, zlib.crc32(header[:60]))`.

O quadro não transmite forma, preenchimento, centro, identidade de superfícies ou volume analítico da carga.

## HTTP e armazenamento

`POST /api/scans`: corpo binário com Content-Type `application/vnd.boxflow.scan-v2`, Content-Length 704. Cabeçalhos: X-Device-ID `boxflow-esp32-demo`, X-Box-ID `BOX-DEMO-01`, X-Boot-ID da sessão, X-Source `simulation`, X-Geometry-ID `bench-vl53-30cm-v3`, X-Acquisition-Clock `simulation_monotonic`, X-Transport `wokwi-esp32` ou `native-c-test`, X-Frame-Age-Ms. Authorization Bearer exigido somente quando token configurado.

Referências v1/v2, quadros densos, CRC errado, valores inválidos, dimensões incompatíveis e pose fora do envelope são rejeitados. Identidade (dispositivo, box, sessão, sequência) é única. Duplicata idêntica não renova horário; dados conflitantes ou nova sequência fora de ordem são rejeitados. Nova sessão permite reiniciar sequência. Um emissor por vez.

`POST /api/device-status` usa os mesmos metadados com JSON `{"state":"unavailable","reason":"i2c_nack"}`. Também há motivos de timeout, congelamento, leitura incompleta, mistura de quadros e CRC. Sem rede, o receptor identifica interrupção por expiração. Não há fila persistente no ESP32.

Consultas: `/api/latest`, `/api/raw/latest`, `/health`, `/` e arquivos estáticos. `/favicon.ico` retorna 204. Banco novo `server/boxflow-vl53-30cm-v3.sqlite3`, sem migração automática dos bancos anteriores; histórico de até 80 entradas no painel.

`valid`: todos os 400 centros suportados e referência aceita; `partial`: total nulo; `unavailable`: ausência/falha; `stale`: idade aproximada superior a 45 s. Leituras antigas têm `is_previous_measurement=true`. `precision_status=not_validated`; `zone_model=ideal-center-ray-45deg-v2`.

UTC de recebimento é do servidor; aquisição usa relógio virtual. Idade soma tempo real desde recebimento à idade informada no emissor. Não há sincronização UTC ou correção completa da latência. Duplicatas não renovam idade. Integrar hardware real exige adaptar origem/relógio, validade das zonas, driver e calibração.
