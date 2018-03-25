# Little Sense - Server
The code in this folder creates a webserver which can be run locally on your machine for testing, and deployed to a Raspberry Pi over a local network. Full documentation can be found at http://littlesense.readthedocs.io/.

## Folders
- [Commlinks](commlink/) Code relating to communication with channels e.g. Radios. This is where you can add new communication and radio types.
- [Config](config/) All settings for the project.
- [Database](databases) Database and data.
- [Requirements](requirements/) Python environment requirements.
- [Static](static/) Libraries and images used by the HTML.
- [Templates](templates/) All the HTML templates for the web interface. This is where you can create new visualisations.
- [Utils](utils/) Utility and helper functions through the code.

## Files
- api.py - Web API for interaction with devices and their readings.
- cronjobs.py - Periodic tasks managed by crontab and configured automatically - see file for details. 
- fabfile.py - This file is used by Fabric to automate the deplotment of the project and setup services such as InfluxDB on a remote host i.e. a Raspberry Pi.
- forms.py - This file contains all the WTForm forms used by the webserver.
- receiver.py - This script runs a background service to  listen to a communication channel e.g. a RMF69 radio receiver.
- sysadmin.py - The views and controls assosiated with the System Admin section of the web interface.
- webapp.py - This script creates a website using the Flask microframework. 
