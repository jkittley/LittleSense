# Sensor Store - Server
The code in this folder can be run locally on your machine for testing and deployed to a Raspberry Pi shared access over a local network. To deploy this code to a Raspberry Pi we use Fabric, a tool which automates the process. The first step however is to setup the system on your local machine.

## Run locally
The project can be run locally for developement.

1. Create a python environment (Python 3.5+)
2. Install the local requirements '''pip install -r requirements/local.txt'''
3. Edit the config/general.py, config/secure.py and config/remote.py files as the comments instruct
4. Run '''fab deploy''' and the remote host will be initialised.

## Run remotely
To deploy the project to a remote host for execution e.g. on a RaspberryPi simply call:

```
fab -H 192.168.0.106 -u pi -pMyPassword deploy
```
This will deploy the project to the host located at 192.168.0.101 using the username 'pi' and the password 'MyPassword'.

## Web services
- Website: http://IP_ADDRESS/


## Scripts
- webapp.py - This script provides a web ui for inspecting data and configuring the system
- rxtx.py - Runs as a background service (Systemd) and manages communication e.g. through radios like RMF69.
- fabfile.py - Is for deploying the webapp and rxtx services to a remote host e.g. a raspberry pi

## Technologies
To server employs many technologies. Below we list the core components used and link to their respective websites. If all of this is a bit confusing then don’t worry, we only mention them here as a reference for anyone who is interested.

- [InfluxDb](https://www.influxdata.com/) to store and inspect time series sensor data
- [TinyDb](http://tinydb.readthedocs.io/) to store general information and settings.
- [Flask](http://flask.pocoo.org/) to create the web interface 
- [Gunicorn](http://gunicorn.org/) and [Nginx](https://www.nginx.com/) to serve the web interface 

