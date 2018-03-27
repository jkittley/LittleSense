.. include:: global.rst

Getting Data
============
One of the most important things once the system is setup is to receive data from your sensor devices. Devices can transmit information to |project| in a number of ways. The simplest is by making http requests to the RESTful API over a wired of WiFi connection. However |project| also supports the connection of transceivers to the serial port. We suggest you start by generating some test data, just to make sure everything is working.

.. toctree::
   :maxdepth: 1

   getdata_testdata
   getdata_webapi
   getdata_receive_serial
   device_common_errors

.. Note::

    You can through any number of key:value pairs at the server (along with a UTC time string and a unique sender device id) and the server will record them without question. You don't even need to register devices first!. However, |project| will only keep the data of unregistered devices for a limited time. Devices can easily be registered via the web interface and once registered their data will be kept forever. 

Sensing Devices
^^^^^^^^^^^^^^^
Example sensor code for various harware platforms such as Arduinoscan be found in the  repository here: https://github.com/jkittley/LittleSense/tree/master/device


