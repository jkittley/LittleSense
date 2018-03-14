.. include:: global.rst

System Design Notes
===================
In this section we take a moment to dicuss the most important files and folders in the project and the motivations behind some of the deign choices made.

Key files
^^^^^^^^^
- webapp.py - This script creates a website using the Flask microframework. 
- rxtx.py - This script runs a background service to  listen to a communication channel e.g. a RMF69 radio receiver.
- fabfile.py - This file is used by Fabric to automate the deplotment of the project and setup services such as InfluxDB on a remote host i.e. a Raspberry Pi.
- commlink/ - In this folder (package) there are Classes which manage the communication through various channels.
- static/ - This is where all images, javascript, css and media files should be stored.
- templates/ - This folder contains all the HTML templates used in the site.

Technologies
^^^^^^^^^^^^
The server employs many technologies. Below we list the most prominant and link to their respective websites. If all of this is a bit confusing then don’t worry, we only mention them here as a reference for anyone who is interested.

- [InfluxDb](https://www.influxdata.com/) to store and inspect time series sensor data
- [TinyDb](http://tinydb.readthedocs.io/) to store general information and settings.
- [Flask](http://flask.pocoo.org/) to create the web interface 
- [Gunicorn](http://gunicorn.org/) and [Nginx](https://www.nginx.com/) to serve the web interface 

