#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>
#include <WiFiClientSecure.h>
#include <ArduinoJson.h>
#include <NewPing.h>
#include <WebSocketsClient.h>

#define TRIGGER_PIN 5 
#define ECHO_PIN 4   
#define MAX_DISTANCE 200 
NewPing sonar(TRIGGER_PIN, ECHO_PIN, MAX_DISTANCE);

const char* rede = "sua rede";
const char* senha = "sua senha";
WebSocketsClient webSocket;


int motorIn1 = 13;
int motorIn2 = 15;
int motorIn3 = 0;
int motorIn4 = 2;
int enbA = 14;
int enbB = 12;
int velocidade = 150;


const char* apiKey = "sua chave do google";  

void setup() {
  
  Serial.begin(115200);
  pinMode(motorIn1,OUTPUT);
  pinMode(motorIn2,OUTPUT);
  pinMode(motorIn3,OUTPUT);
  pinMode(motorIn4,OUTPUT);
  pinMode(enbA,OUTPUT);
  pinMode(enbB,OUTPUT);

  WiFi.begin(rede, senha);

  
  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.print(".");
  }
  Serial.println("Conectado ao Wi-Fi");

 
  webSocket.begin("localhost", 8080, "/ws1");
  webSocket.onEvent(webSocketEvent);
  webSocket.setReconnectInterval(5000);
}

void loop() {
  webSocket.loop();
  int distance = sonar.ping_cm();

 
  if (distance > 20 || distance ==0) {
    frente(); 
   
  } else {
    parar();
    tras();
    girar(); 

  }

  delay(10);

}

void webSocketEvent(WStype_t type, uint8_t * payload, size_t length) {
    switch (type) {
        case WStype_DISCONNECTED:
            Serial.println("WebSocket desconectado!");
            break;
        case WStype_CONNECTED:
            Serial.println("Conectado ao servidor WebSocket!");
            break;
        case WStype_TEXT:
            Serial.printf("Mensagem recebida: %s\n", payload);
            if (strcmp((char*)payload, "socorro") == 0) { 
                
                Serial.println("A mensagem 'socorro' foi recebida. Executando ação.");

                WiFi.scanNetworks(true);
                delay(5000); 

                String jsonPayload = redesDeWifiJson();
                String local = pegarLocalizacao(jsonPayload);

                
                float lat = 0;
                float lng = 0;

                
                StaticJsonDocument<256> responseDoc;
                DeserializationError error = deserializeJson(responseDoc, local);
                if (!error) {
                    lat = responseDoc["location"]["lat"];
                    lng = responseDoc["location"]["lng"];
                    Serial.printf("Latitude: %f, Longitude: %f\n", lat, lng);

                    
                    StaticJsonDocument<128> messageDoc;
                    messageDoc["lat"] = lat;
                    messageDoc["lng"] = lng;

                    String message;
                    serializeJson(messageDoc, message);
                    webSocket.sendTXT(message);
                } else {
                    Serial.println("Falha ao analisar a resposta JSON.");
                }
            }
            else if(strcmp((char*)payload, "parar") == 0){
              parar(10000);


            }
            else if(strcmp((char*)payload, "girar") == 0){
              girar(10000);
            }
            break;
        case WStype_PING:
            Serial.println("Ping recebido.");
            break;
        case WStype_PONG:
            Serial.println("Pong recebido.");
            break;
        default:
            break;
    }
}

void parar() {
  digitalWrite(motorIn1,LOW);
  digitalWrite(motorIn2,LOW);
  digitalWrite(motorIn3,LOW);
  digitalWrite(motorIn4,LOW);
  analogWrite(enbA,0);
  analogWrite(enbB,0);
  delay(1000);
}

void parar(int tempo){
   digitalWrite(motorIn1,LOW);
  digitalWrite(motorIn2,LOW);
  digitalWrite(motorIn3,LOW);
  digitalWrite(motorIn4,LOW);
  analogWrite(enbA,0);
  analogWrite(enbB,0);
  delay(tempo);
}

void frente() {
  digitalWrite(motorIn1, HIGH);
  digitalWrite(motorIn2, LOW);
  digitalWrite(motorIn3, LOW);
  digitalWrite(motorIn4, HIGH);
  analogWrite(enbA, velocidade);
  analogWrite(enbB, velocidade);
}
void tras() {
  digitalWrite(motorIn1, LOW);
  digitalWrite(motorIn2, HIGH);
  digitalWrite(motorIn3, HIGH);
  digitalWrite(motorIn4, LOW);
  analogWrite(enbA, velocidade);
  analogWrite(enbB, velocidade);
  delay(500); 
}

void girar() {
  digitalWrite(motorIn1, HIGH);
  digitalWrite(motorIn2, LOW);
  digitalWrite(motorIn3, HIGH);
  digitalWrite(motorIn4, LOW);
  analogWrite(enbA, velocidade);
  analogWrite(enbB, velocidade);
  delay(300);  
}
void girar(int tempo) {
  digitalWrite(motorIn1, HIGH);
  digitalWrite(motorIn2, LOW);
  digitalWrite(motorIn3, HIGH);
  digitalWrite(motorIn4, LOW);
  analogWrite(enbA, velocidade);
  analogWrite(enbB, velocidade);
  delay(tempo);  
}


String redesDeWifiJson() {
  StaticJsonDocument<512> doc;
  JsonArray wifiAccessPoints = doc.createNestedArray("wifiAccessPoints");

  int n = WiFi.scanComplete();
  for (int i = 0; i < n; ++i) {
    JsonObject wifiObject = wifiAccessPoints.createNestedObject();
    wifiObject["macAddress"] = WiFi.BSSIDstr(i);
    wifiObject["signalStrength"] = WiFi.RSSI(i);
    wifiObject["signalToNoiseRatio"] = 0;  
  }

  String jsonString;
  serializeJson(doc, jsonString);
  return jsonString;
}


String pegarLocalizacao(String jsonPayload) {
  WiFiClientSecure client;  
  client.setInsecure();     

  HTTPClient http;
  http.begin(client, "https://www.googleapis.com/geolocation/v1/geolocate?key=" + String(apiKey));  

  http.addHeader("Content-Type", "application/json");

  int httpResponseCode = http.POST(jsonPayload);

  String response;
  if (httpResponseCode > 0) {
    response = http.getString();
  } else {
    Serial.print("Erro na solicitação HTTP: ");
    Serial.println(httpResponseCode);
  }

  http.end();
  return response;
}
