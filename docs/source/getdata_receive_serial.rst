.. include:: global.rst

Sending Data via the Serial Port
================================
In order for |project| to monitor the Serial ports of the Raspberry Pi, the server needs to run a background service.

The Background Service 
^^^^^^^^^^^^^^^^^^^^^^
On initial setup |project| creates a background task which keeps ```transceiver.py``` running constantly. This script listens to communications send via the serial port. In this way you can attach any radio transceiver via USB and relay messages to |project|. When you make a change and redeploy using the fabric command, this background service gets rebooted automatically. However if you want to control it manually then you can use the following commands (when SSH'd into the Pi).

```sudo systemctl status transceiver``` - What is the current status of the transceiver
```sudo systemctl stop transceiver``` - Stop the service
```sudo systemctl start transceiver``` - Start the service
```sudo systemctl restart transceiver``` - Restart the service

Manually run the service 
^^^^^^^^^^^^^^^^^^^^^^^^
You can run the ```transceiver.py``` manually by calling ```python transceiver.py --verbose```. We strongly recommend you stop the background service first, to save confusion. The --verbose flag tells the transceiver to script to print out debug information.

Attaching Radio Receivers
^^^^^^^^^^^^^^^^^^^^^^^^^
Tutorial coming soon.