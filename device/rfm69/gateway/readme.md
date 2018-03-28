# LittleSense - RFM69 Gateway
This example code demonstrates how data can be relayed to and from the LittleSense server via the Pi's Serial ports. Further information can be found in the main [LittleSense documentations](http://littlesense.readthedocs.io).

## Hardware
This example uses the [Adafruit Feather](https://www.adafruit.com/feather) modules. In particular the [Feather M0 RFM69HCW](https://www.adafruit.com/product/3177]) or the [Feather 32U4 RFM69HCW](https://www.adafruit.com/product/3077]). However the code can be adapted to work with any RFM69 Feather boards. We chose this boards because Adafruit has very good tutorials on how you can utilise these boards to develope sensors.

### Dependancies
Adafruit has really detailed [instructions](https://learn.adafruit.com/adafruit-feather-m0-radio-with-rfm69-packet-radio/overview) on how to get started with their Feather boards, so we are not going to repeat what is already well documented.

Once you are up and running you need the ArduinoJson library. Open the libraries manager in the Arduino IDE and search for "ArduinoJson". You should see a result titled: "ArduinoJson by Benolt Blanchon", click install. For more information and troubleshooting see the [Arduino JSON website](https://arduinojson.org/doc/installation/).

## Software
The file `gateway.ino` contains all the code you need. Open it up in the Arduino IDE, read the comments and change the settings as instructed. Make sure you select the correct port and board from the menu and upload. To test open the serial viewer or use the serial manager built into the LittleSense server.