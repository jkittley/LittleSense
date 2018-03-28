# LittleSense - Device
This folder contains code for various platforms and communication channels. Each folder contains instructions and the required part to setup a device to send sensor readings to the [server](/server/). Full documentation for setting up LittleSense can be found at http://littlesense.readthedocs.io/.

## Basic examples
- [Wifi Test](wifi_test/): Generates data every few seconds and sends it to the servers RESTful API via wifi. 
- [Serial Test](serial_test/): Generates data every few seconds and sends it to the servers Serial port via USB.

## RFM69
- [RFM69 TX Test](rfm69/tx_test/): Generates data every few seconds and sends it to a RFM69 receiver (with ID 1).
- [RFM69 RX to Serial](rfm69/rx_to_serial/): Receiver any data send specifically to ID 1 and forward to the server via the USB (Serial).
