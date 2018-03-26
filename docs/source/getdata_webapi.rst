.. include:: global.rst

Sending Data via WiFi
=====================
The simplest is to send data to |project| is via the RESTful API. Any device on the same local network as the server can make requests. See the :ref:`rest-api` for full details of its functionality.

Arduino Example
^^^^^^^^^^^^^^^
Here is a quick example of how you might send data to the server. This code was tested on an Adafruit Feather esp8266.

.. code:: c

    #include <ESP8266WiFi.h> // https://github.com/esp8266/Arduino
    #include <WiFiClient.h>  // https://github.com/esp8266/Arduino
    #include <ArduinoJson.h> // https://arduinojson.org

    // Wifi Credentials
    String ssid = "YOUR WIFI NAME";
    String pass = "YOUR PASSWORD";
    
    // IP Address of LittleSense server
    const char* host = "192.168.1.188";

    // Make sure this is different for every device
    String device_id = "test_device_1";

    // Setup
    ADC_MODE(ADC_VCC);
    WiFiClient client;
    void setup() {
        delay(2000);
        Serial.begin(115200);
        Serial.println("Little Sense WiFi Example");
        pinMode(LED_BUILTIN, OUTPUT); 
    }

    // Loop
    void loop() {  
    if (wifiConnection()) {
        String url = "/api/readings/";
        String pload = payload();
        String reply = httpPut(url, pload);
        delay(5000);
    }

    // Payload - Data to send
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
        return String(JSONmessage);
    }

    // WiFi
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

