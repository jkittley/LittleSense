# Sensor Store - Server
The code in this folder can be run locally on your machine for testing and deployed to a Raspberry Pi over a local network. We have done our best to document and comment as much as we can. However if you spot anything missing then please let us know, or even better submit a pull request. Each of the subdirectories has a readme file with more information.

- [Commlinks](commlink/) Code ralting to communication with channels e.g. Radios.
- [Config](config/) All settings for the project.
- [Database](databases) Database and data.
- [Requirements](requirements/) Python environment requirements.
- [Static](static/) Libraries and images used by the HTML.
- [Utils](utils/) Utility and helper functions through the code.

## Setup
To deploy this code to a Raspberry Pi we use Fabric, a tool which automates the process. The first step however is to setup the system on your local machine.

### Local Setup
To run the project locally and to use Fabric to deploy the code to a Raspberry PI on the local network, you fill first need to setup the local environment.

1. Create a Python 3.5+ virtual environment (we recommend using [Anaconda](https://www.anaconda.com/download/)) e.g. `conda create --name myenv` and launch it e.g. `conda activate myenv`
2. Navigate to the directory where you downloaded this file e.g `cd /Users/me/sensorStore/server`
3. Install the local requirements: `pip install -r requirements/local.txt`
4. Edit the "config/settings.py" as the comments instruct.

That's all you need to do if you don't want to run the InfluxDB database locally.

5. To tell the webapp that this is a local deployment set an environment variable: `export LOCAL=1`. This will tell the webapp to run in Debug mode.
6. To test the system run: `python webapp.py` and the Flask debug server should start. Now you can navigating to http://localhost:5000/ in your browser.

#### Additional - Local Influx Setup
To install InfluxDB follow the instructions relativant to your operating system [here](https://docs.influxdata.com/influxdb/v1.4/introduction/installation/) and start the server. On MacOS the command is `influxd -config /usr/local/etc/influxdb.conf`


### Remote (Raspberry PI) Setup
To deploy the project to a remote host you must first have created a local virtual environment (Local Setup above). 

1. If you have not already activated the environment then do so e.g. `conda activate myenv`
2. Navigate to the server folder (where this file is stored).
3. Run `fab -H 192.168.0.106 init` if you specify a SSH Key file in the settings then it will only ask you for a password the first time you connect to the device. 

If you make changes to the code locally and want to redeploy it to the server use the `fab -H 192.168.0.106 deploy` command. If you don't specify a SSH Key you can add `-p` followed by your password to speed things up.

#### Additional - Set .local domain name
Rather than entering the IP Address to access the Raspberry pi you can use a `http://raspberrypi.local/`. If you want to change this name then:

1. Connect to the Pi and run `sudo nano /etc/hosts`. 
2. Change the last entry for `127.0.1.1` to the name of your choice
3. Open `sudo nano /etc/nginx/sites-enabled/ROOT_NAME` (replace ROOT_NAME with the value in the settings file)
4. Run `sudo /etc/init.d/hostname.sh` to update the PI
5. Change raspberrypi.local to match the name you chose.
6. Save and reboot the Pi using `shutdown -r now`. 

Now you can access the site with ROOT_NAME.local in your browser.

## System Design
In this section we outline some of the most important files and folders in the project.

### Key files
- webapp.py - This script creates a website using the Flask microframework. 
- rxtx.py - This script runs a background service to  listen to a communication channel e.g. a RMF69 radio receiver.
- fabfile.py - This file is used by Fabric to automate the deplotment of the project and setup services such as InfluxDB on a remote host i.e. a Raspberry Pi.
- commlink/ - In this folder (package) there are Classes which manage the communication through various channels.
- static/ - This is where all images, javascript, css and media files should be stored.
- templates/ - This folder contains all the HTML templates used in the site.

### Technologies
The server employs many technologies. Below we list the most prominant and link to their respective websites. If all of this is a bit confusing then don’t worry, we only mention them here as a reference for anyone who is interested.

- [InfluxDb](https://www.influxdata.com/) to store and inspect time series sensor data
- [TinyDb](http://tinydb.readthedocs.io/) to store general information and settings.
- [Flask](http://flask.pocoo.org/) to create the web interface 
- [Gunicorn](http://gunicorn.org/) and [Nginx](https://www.nginx.com/) to serve the web interface 

