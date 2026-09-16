#include <Arduino.h>
#include <Wire.h>
#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <HTTPClient.h>
#include <esp_system.h>
#include "config.h"
#include "ITofSensor.h"

#ifndef BOXFLOW_SIM
#define BOXFLOW_SIM 1
#endif

#if BOXFLOW_SIM
#include "SimTofSensor.h"
static SimTofSensor tofSensor(Wire);
#else
#error "BOXFLOW_SIM=0 requires a physical ITofSensor backend; it is not implemented or validated yet."
#endif

static const size_t MAX_FRAME=64+8*8*10;
static uint8_t frame[MAX_FRAME];
static char bootId[33];
static unsigned long lastAttempt=0,lastWifiAttempt=0;

bool postBytes(const char *path,const char *contentType,uint8_t *body,size_t length,unsigned long age=0){
  if(WiFi.status()!=WL_CONNECTED){Serial.println("HTTP: Wi-Fi indisponivel; tentativa nao enviada.");return false;}
  String url=String(API_BASE)+path;HTTPClient http;WiFiClient plain;WiFiClientSecure secure;
  if(url.startsWith("https://")){
    if(!strlen(ROOT_CA)){Serial.println("HTTPS: configure ROOT_CA em config.h.");return false;}
    secure.setCACert(ROOT_CA);if(!http.begin(secure,url))return false;
  } else if(url.startsWith("http://")){
    if(!http.begin(plain,url))return false;
  } else {Serial.println("API_BASE deve comecar com http:// ou https://");return false;}
  http.setConnectTimeout(3000);http.setTimeout(5000);
  http.addHeader("Content-Type",contentType);
  http.addHeader("X-Device-ID",DEVICE_ID);http.addHeader("X-Box-ID",BOX_ID);http.addHeader("X-Boot-ID",bootId);
  const TofSensorMetadata &sensorMetadata=tofSensor.metadata();
  http.addHeader("X-Source",sensorMetadata.source);http.addHeader("X-Geometry-ID",sensorMetadata.geometryId);
  http.addHeader("X-Acquisition-Clock",sensorMetadata.acquisitionClock);http.addHeader("X-Transport","wokwi-esp32");
  http.addHeader("X-Frame-Age-Ms",String(age));
  if(strlen(API_TOKEN))http.addHeader("Authorization",String("Bearer ")+API_TOKEN);
  int code=http.POST(body,length);
  Serial.printf("HTTP %s: %d\n",path,code);
  if(code>0)Serial.println(http.getString());http.end();return code>=200&&code<300;
}
void setup(){
  Serial.begin(115200);
  if(!tofSensor.begin()){Serial.println("Falha ao inicializar o sensor ToF.");}
  WiFi.mode(WIFI_STA);WiFi.begin("Wokwi-GUEST","",6);
  snprintf(bootId,sizeof(bootId),"%08lx%08lx%08lx%08lx",(unsigned long)esp_random(),(unsigned long)esp_random(),(unsigned long)esp_random(),(unsigned long)esp_random());
  Serial.printf("BoxFlow | SIMULACAO | %s\n",tofSensor.metadata().name);Serial.printf("Sessao: %s\n",bootId);
  Serial.printf("API: %s\n",API_BASE);
}
void loop(){
  if(WiFi.status()!=WL_CONNECTED&&millis()-lastWifiAttempt>=10000){lastWifiAttempt=millis();WiFi.reconnect();}
  if(millis()-lastAttempt<SCAN_INTERVAL_MS){delay(20);return;}lastAttempt=millis();
  size_t length=0;TofFrameMetadata scan={};const char *reason=nullptr;unsigned long acquisitionStart=millis();
  if(tofSensor.acquire(frame,sizeof(frame),length,scan,reason)){
    Serial.printf("Varredura %lu: %u zonas, %u bytes, CRC OK\n",(unsigned long)scan.sequence,
      (unsigned)(scan.columns*scan.rows),(unsigned)scan.frameBytes);
    // Acquisition age is measured on the MCU's monotonic clock. It is not UTC.
    if(!postBytes("/api/scans","application/vnd.boxflow.scan-v2",frame,length,millis()-acquisitionStart))
      Serial.println("Varredura nao confirmada. Sem fila persistente neste prototipo; verificar historico por sequencia.");
  }else{
    Serial.printf("Aquisicao indisponivel: %s\n",reason);
    char body[120];snprintf(body,sizeof(body),"{\"state\":\"unavailable\",\"reason\":\"%s\"}",reason);
    postBytes("/api/device-status","application/json",(uint8_t*)body,strlen(body));
  }
}
