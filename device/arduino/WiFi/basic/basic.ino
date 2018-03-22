// ========================
//
// This example shows how you can post data to the LittleSense server using the RESTful API.
//
// Adjust the settings below and this script will send random values to the server every few
// seconds. You can add a sensor to the Arduino and then report the readings in the payload.
// 
// ========================

#include <ESP8266WiFi.h>
#include <WiFiClient.h>
#include <ArduinoJson.h>

// ========================
// Settings
// ========================
String ssid = "YOUR WIFI NAME";
String pass = "YOUR PASSWORD";

// IP Address of LittleSense server
const char* host = "192.168.1.188";

// Make sure this is different for every device
String device_id = "test_device_1";

// ========================
// Setup
// ========================
ADC_MODE(ADC_VCC);
WiFiClient client;
void setup() {
  delay(2000);
  Serial.begin(115200);
  Serial.println("Little Sense WiFi Example");
  pinMode(LED_BUILTIN, OUTPUT); 
}

// ========================
// Loop
// ========================
void loop() {  
  if (wifiConnection()) {
    String url = "/api/readings/";
    Serial.println("PUT to http://" + String(host) + url);
    String pload = payload();
    String reply = httpPut(url, pload);
    Serial.println(reply);
  }
  delay(5000);
}

// ========================
// Payload - Data to send
// ========================

String payload() {
  StaticJsonBuffer<200> jsonBuffer;
  JsonObject& root = jsonBuffer.createObject();
  
  root["device_id"] = device_id;
  root["dtype"] = "float";
  root["field"] = "temperature";
  root["unit"] = "C";
  root["value"] = random(0,450) / 10;
  root["utc"] = "NOW";
  
  char JSONmessage[300];
  root.printTo(JSONmessage);
  
  Serial.println("Payload: ");
  root.prettyPrintTo(Serial);

  return String(JSONmessage);
}

// ========================
// Helpers
// ========================

boolean wifiConnection() {
  WiFi.begin(ssid.c_str(), pass.c_str());
  int count = 0;
  Serial.print("Waiting for Wi-Fi connection");
  while ( count < 20 ) {
    if (WiFi.status() == WL_CONNECTED) {
      Serial.println("");
      Serial.println("WiFi connected");
      Serial.println("IP address: ");
      Serial.println(WiFi.localIP());
      return (true);
    }
    delay(500);
    Serial.print(".");
    count++;
  }
  Serial.println("Timed out.");
  return false;
}

String httpPut(String url, String data) {
  if (client.connect(host, 80)) {
    Serial.println("Sending...");
    client.println("PUT " + url + " HTTP/1.1");
    client.println("Host: " + (String)host);
    client.println("User-Agent: ESP8266/1.0");
    client.println("Connection: close");
    client.println("Content-Type: application/json;");
    client.print("Content-Length: ");
    client.println(data.length());
    client.println();
    client.println(data);
    delay(10);
    // Wait foir reply
    unsigned long timeout = millis();
    while (client.available() == 0) {
      if (millis() - timeout > 5000) {
        Serial.println("!!! Client Timeout !!!");
        client.stop();
        break;
      }
    }
    // Read all the lines of the reply from server and print them to Serial
    while (client.available()) {
      String line = client.readStringUntil('\r');
      Serial.print(line);
    }
    // Close connection
    Serial.println();
    Serial.println("closing connection");
  }
  else {
    // Return error if failed to get response
    return "ERROR - No reply from host";
  }
}
