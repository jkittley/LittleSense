.. include:: global.rst

Installation
============
The fastest way to get this code up and running on a Raspberry Pi is with `Fabric <http://www.fabfile.org/>`_. Fabric is a tool which automates deployment of code and installation of dependancies on remote machines. In order to do this you must first setup the system on your local machine. N.B. We actually employ a fork of Fabric which is Python 3 compatable.

Getting Started Video Tutorial
------------------------------
This is a 10 minute video which walks you through the setup process from installing NOOBs on your Pi to collecting data. All the instructions you need are then detailed below.

.. raw:: html

    <iframe width="690" height="380" src="https://www.youtube.com/embed/gAPfL7tdLxY" frameborder="0" allow="autoplay; encrypted-media" allowfullscreen></iframe>
    <br>
    <br>

Local Install
-------------
1. Create a Python 3.5+ virtual environment (we recommend using `Anaconda <https://www.anaconda.com/download/>`_ as a tool for managing local environments. If you have Anaconda installed you can call ```conda create --name myenv``` to create an environment called "myenv".
2. Step in to the environment with ```conda activate myenv``` (or equivelent).
3. Navigate to the directory where you cloned/downloaded this project and enter the server subfolder e.g ```cd /Users/me/sensorStore/server```
4. Install the local requirements: ```pip install -r requirements/local.txt```
5. Edit the "config/settings.py" as the comments instruct in the file.

If you don't want to run the system locally, you can skip ahead to the next section. However if you to make any modifications it is recommened that you complete the following steps so you can test before deployment.

6. Install InfluxDB. Visit `InfluxDB <https://www.influxdb.com/>`_ and follow the instructions relativant to your operating system.
7. Export an environment variable: ```export LOCAL=1``` to tell the webserver it is running on a local machine (this will launch it in Debug mode).
8. To test the system run: ```python webapp.py``` and the Flask debug server should start. 
9. Navigating to http://localhost:5000/ in your favorite browser and you should see the |project| web interface.

Prepare yor Raspberry PI
------------------------
There are a number of operating system for the PI, however we recommend NOOBs. It may use a bit more disk space, but it if far easier for beginners and does all the drive expansion stuff for you. 

1. Follow the instructions at https://www.raspberrypi.org/ to install NOOBs.
2. Exit the desktop to command line mode.
3. Run ```sudo raspi-config``` to enter configuration mode.

First we are going to configure the pi so it boots to the command line and not the desktop. This will save system resources.

1. Select "Boot Options" from the 
2. Select "Desktop / CLI"
3. Select "Console"
4. The menu should return to the main menu.

Next we are going to change the host name. This allows the Pi to be accessed via <HOST_NAME>.local, which is much easier than entering the IP Address.

1. Select "Network Options"
2. Select "Hostname"
3. Read the instructions and hit ok
4. Enter a new hostname.

Now we want to enable a few service, namely SSH access so we can connect over the network and SPI so we can communicated via the SPI bus.

1. Select "Interface options"
2. Select "SSH" and answer "Yes" to enable this service.
3. Hit "ok" to return to the main menu.
4. Select "Interface options" again
5. Select "SPI" and answer "Yes" to enable this service.
6. Hit "ok" to return to the main menu.
7. Select "Finish" and "OK" to reboot.

Remote (Raspberry PI) First Install
-----------------------------------
Once you have prepared your Pi: 

1. Activated your local virtual environment e.g. ```conda activate myenv```.
2. Navigate to your local project folder and enter the server subfolder.
3. Run ```fab -H littlesense.local init``` to setup the Pi for the first time. 
4. Enter your username and password. If you have specifed a SSH public key path in the settings, this will be the only time the Pi will ask you. 

The init process can take quite a while - it will install large packages like Python 3.5 and update the OS. Don't worry deploying changes is much faster!

Remote Updates
--------------
When you want to update the Pi with changes that you have make locally (and tested!):

1. Make sure you are using the virtual environment and in the server folder. 
2. Run the command: ```fab -H littlesense.local deploy```. 

.. toctree::
   :maxdepth: 3
   
