.. include:: global.rst

Receiving Data
==============
One of the most important things once the system is setup is to receive data from your sensor devices. Devices can transmit information to |project| in a number of ways. The simplest is by making http requests to the RESTful API over a wired of WiFi connection. |project| also supports a number of alternative radio solutions. Details on how to configure the various supported radios can be found in the `commlinks directory <https://github.com/jkittley/LittleSense/tree/master/server/commlink>`_. To receive data from these radios, |project| creates a background service.

Background Service 
^^^^^^^^^^^^^^^^^^
|project| on initial setup creates a background task which keeps ```receive.py``` running constantly. This script listens to communications send via the serial port. In this way you can attach any radio receiver via USB and relay messages to |project|. When you make a change and redeploy using the fabric command, this background service gets rebooted automatically. However if you want to control it manually then you can use the following commands (when SSH'd into the Pi).

```sudo systemctl status receiver``` - What is the current status of the receiver
```sudo systemctl stop receiver``` - Stop the service
```sudo systemctl start receiver``` - Start the service
```sudo systemctl restart receiver``` - Restart the service

Manually Run Receiver Service 
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
You can run the ```receiver.py``` manually by calling ```python receiver.py --verbose```. We strongly recommend you stop the background service first, to save confusion. The --verbose flag tells the receiver to script to print out debug information.

Test data
^^^^^^^^^
```python receiver.py --test``` generates test data. Adding sensor data to the systems on a timed loop. See the contents of receiver.py for more details.

