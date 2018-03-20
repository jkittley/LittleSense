.. include:: global.rst

System Design Notes
===================
The server employs many technologies. Below we list the most prominant and link to their respective websites. If all of this is a bit confusing then don’t worry, we only mention them here as a reference for anyone who is interested.

- InfluxDb (https://www.influxdata.com/) to store and inspect time series sensor data
- TinyDb (http://tinydb.readthedocs.io/) to store general information and settings.
- Flask (http://flask.pocoo.org/) to create the web interface 
- Gunicorn (http://gunicorn.org/) and Nginx (https://www.nginx.com/) to serve the web interface 

