/*
  Firmware de exemplo — ESP32 DevKit1
  Conecta ao backend via WebSocket e envia leituras periódicas.

  Bibliotecas necessárias (instalar via Library Manager da Arduino IDE):
    - WebSockets by Markus Sattler (arduinoWebSockets)
    - ArduinoJson

  Ajuste WIFI_SSID, WIFI_PASSWORD, SERVER_HOST, SERVER_PORT e DEVICE_API_KEY
  para os mesmos valores configurados no .env do backend.
*/

#include <WiFi.h>
#include <WebSocketsClient.h>
#include <ArduinoJson.h>

const char* WIFI_SSID     = "SEU_WIFI";
const char* WIFI_PASSWORD = "SUA_SENHA_WIFI";

const char* SERVER_HOST   = "192.168.0.100"; // IP ou domínio do backend
const uint16_t SERVER_PORT = 8000;
const char* DEVICE_ID     = "esp32-01";
const char* DEVICE_API_KEY = "troque-esta-chave-de-dispositivo"; // igual ao .env

WebSocketsClient webSocket;
unsigned long lastSend = 0;
const unsigned long SEND_INTERVAL_MS = 5000;

void onWebSocketEvent(WStype_t type, uint8_t* payload, size_t length) {
  switch (type) {
    case WStype_CONNECTED:
      Serial.println("[WS] Conectado ao backend");
      break;
    case WStype_DISCONNECTED:
      Serial.println("[WS] Desconectado do backend");
      break;
    case WStype_TEXT: {
      // Comandos recebidos do backend chegam aqui
      Serial.printf("[WS] Comando recebido: %s\n", payload);
      StaticJsonDocument<256> doc;
      DeserializationError err = deserializeJson(doc, payload, length);
      if (!err) {
        const char* command = doc["command"];
        // TODO: tratar comandos, ex: ligar/desligar relé, mudar intervalo, etc.
        Serial.printf("Comando: %s\n", command ? command : "desconhecido");
      }
      break;
    }
    default:
      break;
  }
}

void connectWiFi() {
  Serial.printf("Conectando ao WiFi %s", WIFI_SSID);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.printf("\nWiFi conectado. IP: %s\n", WiFi.localIP().toString().c_str());
}

void setup() {
  Serial.begin(115200);
  connectWiFi();

  String path = String("/ws/device?device_id=") + DEVICE_ID + "&api_key=" + DEVICE_API_KEY;
  webSocket.begin(SERVER_HOST, SERVER_PORT, path);
  webSocket.onEvent(onWebSocketEvent);
  webSocket.setReconnectInterval(5000);
}

void loop() {
  webSocket.loop();

  unsigned long now = millis();
  if (now - lastSend >= SEND_INTERVAL_MS) {
    lastSend = now;
    sendReading();
  }
}

void sendReading() {
  // Substitua pelos seus sensores reais (DHT22, LDR, etc.)
  float temperature = 25.0 + (random(-20, 20) / 10.0);
  float humidity = 60.0 + (random(-50, 50) / 10.0);

  StaticJsonDocument<128> doc;
  doc["temperature"] = temperature;
  doc["humidity"] = humidity;
  doc["uptime_s"] = millis() / 1000;

  String json;
  serializeJson(doc, json);
  webSocket.sendTXT(json);

  Serial.printf("Enviado: %s\n", json.c_str());
}
