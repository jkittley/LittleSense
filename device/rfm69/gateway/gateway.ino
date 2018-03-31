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
// Note: Because it is expected that the serial output is going to be read by the 
//       server. Start all messages with a # and they will be ignored.
//
// **********************************************************************************

#include <RFM69.h>         //get it here: https://www.github.com/lowpowerlab/rfm69
#include <RFM69_ATC.h>     //get it here: https://www.github.com/lowpowerlab/rfm69
#include <SPI.h>           //included with Arduino IDE install (www.arduino.cc)
#include <ArduinoJson.h>   //https://arduinojson.org/d

// Node and network config
#define NODEID        1    // The ID of this node (must be different for every node on network)
#define NETWORKID     100  // The network ID

// Are you using the RFM69 Wing? Uncomment if you are.
#define USING_RFM69_WING 

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

// Board and radio specific config - You should not need to edit
#if defined (__AVR_ATmega32U4__) && defined (USING_RFM69_WING)
    #define RF69_SPI_CS  10   
    #define RF69_RESET   11   
    #define RF69_IRQ_PIN 2 
    #define RF69_IRQ_NUM digitalPinToInterrupt(RF69_IRQ_PIN) 
#elif defined (__AVR_ATmega32U4__)
    #define RF69_RESET    4
    #define RF69_SPI_CS   8
    #define RF69_IRQ_PIN  7
    #define RF69_IRQ_NUM  4
#elif defined(ARDUINO_SAMD_FEATHER_M0) && defined (USING_RFM69_WING)
    #define RF69_RESET    11
    #define RF69_SPI_CS   10
    #define RF69_IRQ_PIN  6
    #define RF69_IRQ_NUM  digitalPinToInterrupt(RF69_IRQ_PIN)
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
  char command[20]; // command
  uint8_t battery; // Battery voltage
  uint8_t volume;   // Volume
  uint8_t rssi;     // RSSI as seen by node
} Payload;
Payload payload;

// Main loop
void loop() {
  
  // Process any serial input
  if (Serial.available() > 0) {
    
    String input = Serial.readString();
    if (input == 'd') {
      printDebugInfo();
    }

    if (input.toInt() > 0) {
      char buff[] = "ShowYourSelf";
      
      Serial.print("# Asking Node "); Serial.print(String(input).toInt()); Serial.println(" to show itself");
      
      if (radio.sendWithRetry(String(input).toInt(), buff, sizeof(buff))) {
        Serial.println(" Acknoledgment received!");
      } else {
        Serial.println(" No Acknoledgment after retries");
      }
    }
  }

  // Process packets received
  if (radio.receiveDone()) {
    
    Serial.print("# sender: "); Serial.println(radio.SENDERID, DEC);
    Serial.print("# target  "); Serial.println(radio.TARGETID, DEC);
    Serial.print("# Data length: "); Serial.println(radio.DATALEN);
    Serial.print("# RX_RSSI:"); Serial.println(radio.RSSI); 

    if (radio.DATALEN != sizeof(Payload)) {
      Serial.print("# Invalid payload received, not matching Payload struct. -- ");
      Serial.print(radio.DATALEN);
      Serial.print(" vs ");
      Serial.println(sizeof(Payload));
    } else {    
      payload = *(Payload*)radio.DATA; //assume radio.DATA actually contains our struct and not something else
      
      sendReadingToSerial(radio.SENDERID, "float", "battery_level", "volts", payload.battery);
      sendReadingToSerial(radio.SENDERID, "float", "signal_strength", "db", radio.RSSI);
      sendReadingToSerial(radio.SENDERID, "float", "audio_level", "db", payload.volume);
      
      if (radio.ACKRequested()) {
        radio.sendACK();
        Serial.print("# ACK sent.");
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
  Serial.print("# Resetting radio...");
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
  #if defined (__AVR_ATmega32U4__)
    Serial.println("# AVR ATmega 32U4");
  #else
    Serial.println("# SAMD FEATHER M0");
  #endif
  #ifdef USING_RFM69_WING
    Serial.println("# Using RFM69 Wing: YES");
  #else
    Serial.println("U# sing RFM69 Wing: NO");
  #endif
  Serial.print("# RF69_SPI_CS: "); Serial.println(RF69_SPI_CS);
  Serial.print("# RF69_IRQ_PIN: "); Serial.println(RF69_IRQ_PIN);
  Serial.print("# RF69_IRQ_NUM: "); Serial.println(RF69_IRQ_NUM);
  #ifdef ENABLE_ATC
    Serial.println("# RFM69 Auto Transmission Control: Enabled");
  #else
    Serial.println("# RFM69 Auto Transmission Control: Disabled");
  #endif
  if (promiscuousMode) {
    Serial.println("# Promiscuous Mode: Enabled");
  } else {
    Serial.println("# Promiscuous Mode: Disabled");
  }
  #ifdef ENCRYPTKEY
    Serial.println("# Encryption: Enabled");
  #else
    Serial.println("# Encryption: Disabled");
  #endif
  sprintf(buff, "# Listening at %d Mhz...", FREQUENCY==RF69_433MHZ ? 433 : FREQUENCY==RF69_868MHZ ? 868 : 915);
  Serial.println(buff);
}

// sendReadingToSerial
void sendReadingToSerial(int sender_id, String dtype, String field_name, String unit, float value) {
  // Build message
  StaticJsonBuffer<200> jsonBuffer;
  JsonObject& root = jsonBuffer.createObject();
  root["device_id"] = "test_device_"+String(sender_id);
  root["dtype"] = dtype;
  root["name"] = field_name;
  root["unit"] = unit;
  root["value"] = value;
  root["utc"] = "NOW";
  char JSONmessage[300];
  root.printTo(JSONmessage);
  // Print to serial
  root.printTo(Serial);
  Serial.println();
  delay(100);
}

// Identify yourself
void showMe() {
  Blink(500, 2);
  Blink(100, 10);
  Blink(500, 2);
  Blink(100, 10);
  Blink(500, 2);
}



