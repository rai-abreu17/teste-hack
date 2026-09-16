#pragma once
// Gateway privado: execute o receptor no seu computador, porta 8000.
// Gateway público: substitua por um endpoint HTTP/HTTPS realmente acessível.
static const char *API_BASE = "http://host.wokwi.internal:8000";
static const char *DEVICE_ID = "boxflow-esp32-demo";
static const char *BOX_ID = "BOX-DEMO-01";
static const char *API_TOKEN = ""; // Mesmo valor de BOXFLOW_TOKEN no receptor, se usado.
// Para HTTPS, cole o certificado CA PEM do endpoint. Nunca desabilitamos TLS.
static const char *ROOT_CA = "";
static const unsigned long SCAN_INTERVAL_MS = 3000;
