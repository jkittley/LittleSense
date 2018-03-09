# Sensor Store
This folder contains a number of utility functions. You shouldn't need to edit anything in here, but incase you need to, here is a list of the files and what the classes they contain do.

- backup.py - Manage backups and upload of backups
- device_register.py - Manages a registry of devices which have communicated with the server and user settings assosiated with them e.g. a friendly name.
- devices.py - Classes to represent a Device and a collection of Devices
- influx.py - A wrapper for the initialisation of the Influx database and some helpful tools
- logger.py - A bespoke loggin tool which records log data to the Influx database