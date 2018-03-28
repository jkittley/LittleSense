// **********************************************************************************
//
// RFM69 <--> Serial Gateway
//
// This cript acts as an interface between the LittleSense Serial port and the RFM69 
// Radio. Because radios such as the RFM69 need to keep the packet length to a minimum
// you must edit this script to translate the RFM69 packet data into JSON. Don't worry
// this script has an example. In addition, the script translates serial messages set 
// from the server and transmits them to devices.
//
// **********************************************************************************

#include <RFM69.h>         //get it here: https://www.github.com/lowpowerlab/rfm69
#include <RFM69_ATC.h>     //get it here: https://www.github.com/lowpowerlab/rfm69
#include <SPI.h>           //included with Arduino IDE install (www.arduino.cc)
#include <ArduinoJson.h>   //https://arduinojson.org/d

// Node and network config
#define NODEID        1    // The ID of this node (must be different for every node on network)
#define NETWORKID     100  // The network ID

// The transmision frequency of the baord. Change as needed.
#define FREQUENCY      RF69_433MHZ //RF69_868MHZ // RF69_915MHZ

// An encryption key. Must be the same 16 characters on all nodes. Comment out to disable
#define ENCRYPTKEY    "sampleEncryptKey"

// Uncomment if this board is the RFM69HW/HCW not the RFM69W/CW
#define IS_RFM69HW_HCW

// Uncomment to enable auto transmission control - adjusts power to save battery
#define ENABLE_ATC

// Serial board rate
#define SERIAL_BAUD   115200

// Which LED
#define LED LED_BUILTIN

// Board specific config - You should not need to edit
#if defined (__AVR_ATmega32U4__)
  #define RF69_RESET    4
  #define RF69_SPI_CS   8
  #define RF69_IRQ_PIN  7
  #define RF69_IRQ_NUM  4
#elif defined(ARDUINO_SAMD_FEATHER_M0)
  #define RF69_RESET    4
  #define RF69_SPI_CS   8
  #define RF69_IRQ_PIN  3
  #define RF69_IRQ_NUM  3
#endif

// Create Radio
#ifdef ENABLE_ATC
    RFM69_ATC radio(RF69_SPI_CS, RF69_IRQ_PIN, false, RF69_IRQ_NUM);
#else
    RFM69 radio(RF69_SPI_CS, RF69_IRQ_PIN, false, RF69_IRQ_NUM);
#endif

 //set to 'true' to sniff all packets on the same network
bool promiscuousMode = false;

// Setup
void setup() {
  Serial.begin(SERIAL_BAUD);
  
  // Wait for serial port to connect before anything starts
  while (!Serial) { 
    ; 
  }

  // Reset the radio
  resetRadio();

  // Initialize the radio
  radio.initialize(FREQUENCY,NODEID,NETWORKID);
  #ifdef IS_RFM69HW_HCW
    radio.setHighPower(); //must include this only for RFM69HW/HCW!
  #endif
  #ifdef ENCRYPTKEY
    radio.encrypt(ENCRYPTKEY);
  #endif
  radio.promiscuous(promiscuousMode);

  // Show debug info
  printDebugInfo();
}


// Define payload
typedef struct {
  char msg[50]; // A string msg
  uint8_t uptime; //uptime in ms
  uint8_t temp;   //temperature
} Payload;
Payload payload;


// Main loop
void loop() {
  
  // Process any serial input
  if (Serial.available() > 0) {
    
    char input = Serial.read();
    if (input == 'd') {
      printDebugInfo();
    }

    if (isDigit(input)) {
      char buff[] = "ShowYourSelf";
      Serial.print("Asking Node "); Serial.print(String(input).toInt()); Serial.println(" to show itself");
      if (radio.sendWithRetry(String(input).toInt(), buff, sizeof(buff))) {
        Serial.println(" Acknoledgment received!");
      } else {
        Serial.println(" No Acknoledgment after retries");
      }
    }
  }

  // Process packets received
  if (radio.receiveDone()) {
    
    Serial.print('[sender: '); Serial.print(radio.SENDERID, DEC); Serial.println("] ");
    if (promiscuousMode) { Serial.print("to [");Serial.print(radio.TARGETID, DEC);Serial.print("] "); }

    Serial.print("Data length: "); Serial.println(radio.DATALEN);
    Serial.print("[RX_RSSI:"); Serial.print(radio.RSSI); Serial.print("]");

    if (radio.DATALEN != sizeof(Payload)) {
      Serial.println("Invalid payload received, not matching Payload struct!");
      Serial.print(radio.DATALEN);
      Serial.print(" vs ");
      Serial.println(sizeof(Payload));
    } else {    
      payload = *(Payload*)radio.DATA; //assume radio.DATA actually contains our struct and not something else
      Serial.print(" msg=");
      Serial.print(payload.msg);
      Serial.print(" uptime=");
      Serial.print(payload.uptime);
      Serial.print(" temp=");
      Serial.print(payload.temp);
      if (radio.ACKRequested()) {
        radio.sendACK();
        Serial.print(" - ACK sent.");
      }
    }
        
    Serial.println();
    Blink(3, 1);
  }
}

// Helper function to blink the LED
void Blink(int delayms, int numberTimes) {
  pinMode(LED, OUTPUT);
  for (int x=0; x < numberTimes; x++) {
    digitalWrite(LED, HIGH);
    delay(delayms);
    digitalWrite(LED, LOW);
  }
}

// Reset the Radio
void resetRadio() {
  Serial.print("Resetting radio...");
  pinMode(RF69_RESET, OUTPUT);
  digitalWrite(RF69_RESET, HIGH);
  delay(20);
  digitalWrite(RF69_RESET, LOW);
  delay(500);
  Serial.println(" complete");
}

// Print Info
void printDebugInfo() {
  char buff[50];
  sprintf(buff, "\nListening at %d Mhz...", FREQUENCY==RF69_433MHZ ? 433 : FREQUENCY==RF69_868MHZ ? 868 : 915);
  Serial.println(buff);
  Serial.print("RF69_SPI_CS: "); Serial.println(RF69_SPI_CS);
  Serial.print("RF69_IRQ_PIN: "); Serial.println(RF69_IRQ_PIN);
  Serial.print("RF69_IRQ_NUM: "); Serial.println(RF69_IRQ_NUM);
  #ifdef ENABLE_ATC
    Serial.println("RFM69 Auto Transmission Control: Enabled");
  #else
    Serial.println("RFM69 Auto Transmission Control: Disabled");
  #endif
  if (promiscuousMode) {
    Serial.println("Promiscuous Mode: Enabled");
  } else {
    Serial.println("Promiscuous Mode: Disabled");
  }
  #ifdef ENCRYPTKEY
    Serial.println("Encryption: Enabled");
  #else
    Serial.println("Encryption: Disabled");
  #endif
}

// sendReadingToSerial
void sendReadingToSerial(String dtype, String field_name, String unit, float value) {
  // Build message
  StaticJsonBuffer<200> jsonBuffer;
  JsonObject& root = jsonBuffer.createObject();
  root["device_id"] = "device_"+String(NODEID);
  root["dtype"] = dtype;
  root["field"] = field_name;
  root["unit"] = unit;
  root["value"] = value;
  root["utc"] = "NOW";
  char JSONmessage[300];
  root.printTo(JSONmessage);
  // Print to serial
  root.printTo(Serial);
  Serial.println();
}

// Identify yourself
void showMe() {
  Blink(500, 2);
  Blink(100, 10);
  Blink(500, 2);
  Blink(100, 10);
  Blink(500, 2);
}




