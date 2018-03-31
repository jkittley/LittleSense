// 
// This sketch is designed to test the serial port. 
// 
#include <ArduinoJson.h>

String device_id = "test_device_1";
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
  
  sendReading("float", "signal", "db", random(0,450)/10);
  sendReading("int", "light_level", "lux", random(300,500)/10);
  sendReading("bool", "switch", "state", random(0,2));
  
  delay(3000);
}

void sendReading(String dtype, String field_name, String unit, int value) {
  StaticJsonBuffer<200> jsonBuffer;
  JsonObject& root = jsonBuffer.createObject();
  root["device_id"] = device_id;
  root["dtype"] = dtype;
  root["field"] = field_name;
  root["unit"] = unit;
  root["value"] = value;
  root["utc"] = "NOW";
  root.printTo(Serial);
  Serial.println();
  delay(100);
}

