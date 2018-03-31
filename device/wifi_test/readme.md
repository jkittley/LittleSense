# LittleSense - REST API Example
This example code demonstrates how easy it is to set up a new sensor which sends information to LittleSense via the Wifi network. The device interacts with the LittleSense RESTful API. Further information can be found in the main [LittleSense documentations](http://littlesense.readthedocs.io).

## Hardware
This example uses the low cost [Wemos](http://wemos.cc) modules. In particular the [Wemos mini Pro](https://wiki.wemos.cc/products:d1:d1_mini_pro]). However should work well with most Arduinos and ESP8266 WiFi sheilds. We chose Wemos because the WiFI is integrated and there are a number of sheilds such as the [battery shield](https://wiki.wemos.cc/products:d1_mini_shields:battery_shield) and the [Humidity & Temperature (DHT) sheild](https://wiki.wemos.cc/products:d1_mini_shields:dht_shield) which can be plugged in to one another to make sensors devices withou any wiring.

### Dependancies
1. Install the [CP210x USB to UART Bridge VCP Drivers](https://www.silabs.com/products/development-tools/software/usb-to-uart-bridge-vcp-drivers) so that we can connect and upload via a serial connection. Once installed the board should appear in the ports menu as `/dev/cu.SLAB_USBtoUART/` on Mac/Linux and something like `USB-SERIAL CH340` on Windows.

2. Add Wemos board support to the Arduino IDE. There's a detailed tutorial [on instructables](http://www.instructables.com/id/Programming-the-WeMos-Using-Arduino-SoftwareIDE/) which has lots of images. Here we will cover the basic steps.
    1. Open the Arduino IDE preferences panel and add `http://arduino.esp8266.com/stable/package_esp8266com_index.json` to the "Additional Boards Manager URLs". If there is already something in this box then add a comma and the paste the URL to create a comma seporated list.
    2. Open the Arduino boards manager and search for "esp8266". You should see a result for "esp8266 by ESP8266 Community". Install this package and restart the Arduino IDE.

3. Add the ArduinoJson library to the Arduino IDE. Open the libraries manager and search for "ArduinoJson". You should see a result titled: "ArduinoJson by Benolt Blanchon", install it. For more information and troubleshooting see the [Arduino JSON website](https://arduinojson.org/doc/installation/).

## Software
The file `wifi_test.ino` contains all the code you need. Open it up in the Arduino IDE, read the comments and change the settings as instructed. Make sure you select the correct port and board from the menu and upload. The script will periodically send test data to the server. Add some sensors and adapt the code to suite your needs.
