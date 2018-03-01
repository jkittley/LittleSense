# Sensor
Hello this project is designed to be deployed on a local server e.g. a Raspberry Pi.

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
- Chronograf:  http://IP_ADDRESS:8888/
- Admin: http://IP_ADDRESS/admin

## Scripts
- webapp.py - This script provides a web ui for inspecting data and configuring the system
- rxtx.py - Runs as a background service (Systemd) and manages communication e.g. through radios like RMF69.
- fabfile.py - Is for deploying the webapp and rxtx services to a remote host e.g. a raspberry pi

## Core Companants
- InfluxDB and the TICK Stack
- Python
- Flask
- nginx and gunicorn
