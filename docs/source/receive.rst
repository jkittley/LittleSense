.. include:: global.rst

Receiving Data
==============
One of the most important things once the system is setup is to receive data from your sensor devices. Devices can transmit information to |project| in a number of ways. The simplest is by making http requests to the RESTful API over a wired of WiFi connection. However |project| also supports the connection of transceivers to the serial port. The background service detailed below manages this communication method.

Background Service 
^^^^^^^^^^^^^^^^^^
On initial setup |project| creates a background task which keeps ```transceiver.py``` running constantly. This script listens to communications send via the serial port. In this way you can attach any radio transceiver via USB and relay messages to |project|. When you make a change and redeploy using the fabric command, this background service gets rebooted automatically. However if you want to control it manually then you can use the following commands (when SSH'd into the Pi).

```sudo systemctl status transceiver``` - What is the current status of the transceiver
```sudo systemctl stop transceiver``` - Stop the service
```sudo systemctl start transceiver``` - Start the service
```sudo systemctl restart transceiver``` - Restart the service

Manually Run Receiver Service 
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
You can run the ```transceiver.py``` manually by calling ```python transceiver.py --verbose```. We strongly recommend you stop the background service first, to save confusion. The --verbose flag tells the transceiver to script to print out debug information.

Test data
^^^^^^^^^
```python transceiver.py --test``` generates test data. Adding sensor data to the systems on a timed loop. See the contents of transceiver.py for more details.

