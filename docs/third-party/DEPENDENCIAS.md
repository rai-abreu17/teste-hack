# Dependências de compilação

O cabeçalho `wokwi-api.h` utilizado na compilação do custom chip foi obtido do exemplo oficial [wokwi/inverter-chip](https://github.com/wokwi/inverter-chip). Seu aviso MIT está preservado no arquivo `WOKWI_API_LICENSE.txt` desta pasta. Os quatro exemplos comunitários analisados em `docs/DECISOES.md` não foram incorporados ao código.

O firmware compilado usa o núcleo [Arduino-ESP32 3.3.0](https://github.com/espressif/arduino-esp32/tree/3.3.0), incluindo suas bibliotecas Arduino, Wire, WiFi, Network, HTTPClient e NetworkClientSecure, além dos componentes ESP-IDF distribuídos por esse núcleo. As fontes, avisos e condições desses componentes pertencem aos projetos de origem. Para reconstruir com as mesmas dependências, siga a instalação versionada no README. O código da aplicação não substitui as licenças das dependências.

Ferramentas usadas: [Arduino CLI](https://github.com/arduino/arduino-cli), [WASI SDK](https://github.com/WebAssembly/wasi-sdk), [Wokwi CLI](https://github.com/wokwi/wokwi-cli), GCC, Python e Node. Os executáveis dessas ferramentas não são redistribuídos neste pacote. O receptor usa somente a biblioteca padrão do Python e o dashboard não incorpora bibliotecas externas ou fontes web.
