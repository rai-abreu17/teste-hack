# Abstração do sensor e compilação ESP32

Data: 2026-09-16. Estado: **implementação concluída e compilada; execução ponta a ponta no Wokwi ainda pendente**.

O firmware agora depende de `ITofSensor`. O backend `SimTofSensor` preserva o contrato BFLD existente: disparo de captura, polling, leituras I²C em blocos de 28 bytes, releitura do cabeçalho, CRC e sequência. `BOXFLOW_SIM=1` permanece o padrão. Selecionar `BOXFLOW_SIM=0` produz erro explícito de compilação enquanto o backend físico não existir, impedindo que dados simulados sejam confundidos com hardware.

O Arduino CLI 1.2.0 incluído no Arduino IDE compilou o firmware com Arduino-ESP32 3.3.0. Como o toolchain falha em caminhos Windows com caracteres não ASCII, `tools/build_firmware.py` passou a usar automaticamente um estágio ASCII e uma unidade `subst` temporária, removida ao terminar. O binário usa 1.066.159 bytes de programa (81%) e 48.684 bytes de memória global (14%). Os artefatos atualizados estão em `build/firmware/`.

## Verificação

- 26/26 testes do pacote passaram, incluindo o contrato do backend simulado em C++ host e a preparação de todas as fontes Arduino.
- A compilação ESP32 terminou com código zero e produziu BIN, ELF, MAP, bootloader, partições e imagem combinada.
- O editor Wokwi recebeu as fontes atuais em uma sessão anônima. Duas tentativas de compilação remota falharam antes da simulação: uma por resolução/conectividade e outra com HTTP 524 por tempo de fila do serviço.
- A Wokwi CLI 0.26.1 está instalada, mas `WOKWI_CLI_TOKEN` não está definido. Portanto, ainda não há evidência do caminho ESP32 emulado → chip customizado → gateway → HTTP → dashboard.

Essa entrega encerra a lacuna de abstração e recompila o firmware. O driver VL53L5CX físico, a calibração e o ensaio em hardware continuam pendentes. O cálculo de volume permanece no servidor, conforme a arquitetura existente.

