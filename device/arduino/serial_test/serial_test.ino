// 
// This sketch is designed to test the serial port. 
// 
#include <ArduinoJson.h>

String device_id = "test_device_99";
// ========================
// Setup
// ========================

void setup() {
  Serial.begin(11520);
  while (!Serial) {
    ; // wait for serial port to connect.
  }
}

// ========================
// Loop
// ========================
void loop() {  
  
  StaticJsonBuffer<200> jsonBuffer;
  JsonObject& root = jsonBuffer.createObject();
  
  root["device_id"] = device_id;
  root["dtype"] = "float";
  root["field"] = "temperature";
  root["unit"] = "C";
  root["value"] = random(0,450) / 10;
  root["utc"] = "NOW";
  
  root.printTo(Serial);
  Serial.println();
  delay(3000);
}

