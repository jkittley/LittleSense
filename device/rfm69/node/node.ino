// **********************************************************************************
// 
// Test RFM69 Radio trasmitter. Sends a messages every 5 seconds.
//                                                       
// **********************************************************************************

#include <RFM69.h>              // https://www.github.com/lowpowerlab/rfm69
#include <RFM69_ATC.h>          // https://www.github.com/lowpowerlab/rfm69
#include <SPI.h>                // Included with Arduino IDE
#include <ArduinoJson.h>        // https://arduinojson.org/d
#include <Adafruit_SleepyDog.h> // https://github.com/adafruit/Adafruit_SleepyDog

// Node and network config
#define NODEID        3    // The ID of this node (must be different for every node on network)
#define NETWORKID     100  // The network ID
#define GATEWAYID     1    // Where to send data
int TRANSMITPERIOD = 5000; // Transmission interval in ms e.g. 5000 = every 5 seconds 

// Are you using the RFM69 Wing? Uncomment if you are.
//#define USING_RFM69_WING 

// The transmision frequency of the baord. Change as needed.
#define FREQUENCY      RF69_433MHZ //RF69_868MHZ // RF69_915MHZ

// An encryption key. Must be the same 16 characters on all nodes. Comment out to disable
#define ENCRYPTKEY    "sampleEncryptKey"

// Uncomment if this board is the RFM69HW/HCW not the RFM69W/CW
#define IS_RFM69HW_HCW

// Uncomment to enable auto transmission control - adjusts power to save battery
#define ENABLE_ATC

// Serial board rate - just used to print debug messages
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

// Battery pin
#if defined (__AVR_ATmega32U4__) 
  #define VBATPIN A9
#elif defined(ARDUINO_SAMD_FEATHER_M0)
  #define VBATPIN A7
#endif

// Create Radio
#ifdef ENABLE_ATC
    RFM69_ATC radio(RF69_SPI_CS, RF69_IRQ_PIN, false, RF69_IRQ_NUM);
#else
    RFM69 radio(RF69_SPI_CS, RF69_IRQ_PIN, false, RF69_IRQ_NUM);
#endif

// Setup
void setup() {
  Serial.begin(SERIAL_BAUD);

  // wait for serial port to connect. Needed for native USB port only
  while (!Serial) { 
    ; 
  } 

  // Reste the radio
  resetRadio();

  // Initialize the radio
  radio.initialize(FREQUENCY,NODEID,NETWORKID);
  #ifdef IS_RFM69HW_HCW
    radio.setHighPower(); //must include this only for RFM69HW/HCW!
  #endif
  #ifdef ENCRYPTKEY
    radio.encrypt(ENCRYPTKEY);
  #endif
  
  printDebugInfo();
}

// Main loop
long lastPeriod = 0;

void loop() {

  // Send a reading
  sendReading();
  delay(5);

  // Listen form messages for x milliseconds before going to sleep
  unsigned long waitfor = 5000;
  unsigned long started = millis();
  while (millis() < started + waitfor) {
    if (radio.receiveDone()) {
      if (radio.ACKRequested()) { radio.sendACK(); }
      Serial.print('[sender: '); Serial.print(radio.SENDERID, DEC); Serial.println("] ");
      Serial.print("Data length: "); Serial.println(radio.DATALEN);
      Serial.print("[RX_RSSI:"); Serial.print(radio.RSSI); Serial.println("]");
      for (byte i = 0; i < radio.DATALEN; i++) { Serial.print((char)radio.DATA[i]); }
      //showMe();
    }
  }

  Serial.println("Going to sleep");
  radio.sleep();
  Watchdog.sleep(TRANSMITPERIOD);
}

// Define payload
typedef struct {
  char command[20]; // command
  uint8_t battery; // Battery voltage
  uint8_t volume;   // Volume
  uint8_t rssi;     // RSSI as seen by node
} Payload;
Payload payload;



// sendReading
void sendReading() {
  
  // Set payload command
  String("none").toCharArray(payload.command, sizeof(payload.command));

  // Battery Level
  float measuredvbat = analogRead(VBATPIN);
  measuredvbat *= 2;    // we divided by 2, so multiply back
  measuredvbat *= 3.3;  // Multiply by 3.3V, our reference voltage
  measuredvbat /= 1024; // convert to voltage
  payload.battery = 100 * measuredvbat;

  // RSSI
  payload.rssi    = radio.RSSI * 100;

  // Volume
  payload.volume  = random(0,450)/10; 
  
  // Print payload
  Serial.print("Sending payload (");
  Serial.print(sizeof(payload));
  Serial.print(" bytes)");
  Serial.print(" battery=");
  Serial.print(payload.battery);
  Serial.print(" signal=");
  Serial.print(payload.rssi);
  Serial.print(" volume=");
  Serial.print(payload.volume);
  Serial.println(")");
  
  // Send payload
  if (radio.sendWithRetry(GATEWAYID, (const void*) &payload, sizeof(payload))) {
    Serial.println(" Acknoledgment received!");
    Blink(100, 1);
  } else {
    Serial.println(" No Acknoledgment after retries");
    Blink(500, 1);
  }
}


// Helper function to blink the LED
void Blink(int delayms, int numberTimes) {
  pinMode(LED, OUTPUT);
  for (int x=0; x < numberTimes; x++) {
    digitalWrite(LED, HIGH);
    delay(delayms);
    digitalWrite(LED, LOW);
    delay(delayms);
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
  #if defined (__AVR_ATmega32U4__)
    Serial.println("AVR ATmega 32U4");
  #else
    Serial.println("SAMD FEATHER M0");
  #endif
  #ifdef USING_RFM69_WING
    Serial.println("Using RFM69 Wing: YES");
  #else
    Serial.println("Using RFM69 Wing: NO");
  #endif
  Serial.print("RF69_SPI_CS: "); Serial.println(RF69_SPI_CS);
  Serial.print("RF69_IRQ_PIN: "); Serial.println(RF69_IRQ_PIN);
  Serial.print("RF69_IRQ_NUM: "); Serial.println(RF69_IRQ_NUM);
  #ifdef ENABLE_ATC
    Serial.println("RFM69 Auto Transmission Control: Enabled");
  #else
    Serial.println("RFM69 Auto Transmission Control: Disabled");
  #endif
  #ifdef ENCRYPTKEY
    Serial.println("Encryption: Enabled");
  #else
    Serial.println("Encryption: Disabled");
  #endif
  sprintf(buff, "\nListening at %d Mhz...", FREQUENCY==RF69_433MHZ ? 433 : FREQUENCY==RF69_868MHZ ? 868 : 915);
  Serial.println(buff);
}

// Identify yourself
void showMe() {
  Blink(500, 2);
  Blink(100, 10);
  Blink(500, 2);
  Blink(100, 10);
  Blink(500, 2);
}

