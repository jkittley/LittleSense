.. Little Sense documentation master file, created by
   sphinx-quickstart on Mon Mar 12 14:37:40 2018.

.. include:: global.rst

.. note::

   This project has just been released so it may contain bugs. If you spot one then please report it as an issue on Github. We want to make this project awesome and to do that we need your help!

Welcome to |project| documentation!
===================================
So you want to deploy a bunch of sensors and store the data they produce locally? Well you 
have come to the right place. |project| was developed as a foundation on which novice and 
experienced programmers can develope bespoke sensor network applciations. Out of the box
|project| has all the code you need to sense, record and visualise data from any number of 
sensors. In addition the code has been specifically designed and written to make editing 
the layout and functionality easy.

At the heart of this project (and its creators) is the `Raspberry Pi <https://www.raspberrypi.org/>`_. The Pi acts as a server, listening for data over WiFi and Serial ports, storing the data it receives in a timeseries optimised database (`InfluxDB <https://www.influxdb.com/>`_). Radio receivers (such as RFM69) can be connected to the Raspberry Pi via USB allowing for low energy sensor devices to communicated via any radio or protocal (there's a bunch of examples in the repository). The Pi also provides a local website on which the recieved data can be inspected and the system monitored and debugged.

.. image:: _static/architecture.png

Features
--------

- All the latest tech: Python 3, InfluxDB, Flask...
- Simple setup and updates using Fabric automation scripts.
- Example sensor device code.
- Communication via various Radios and WiFi.
- Designed to be simple to expand and modify.
- Well documented.

Contents
--------

.. toctree::
   :maxdepth: 2

   self
   getstarted
   getdata
   customisation
   api
   server_about
   
About the code
--------------
The project code is designed for novice user to deploy and for novice programmers (e.g. academic researchers) to modify. As such we have chosen to use technologies which make the reading and adapting of the code less difficult, for example, we chose to use jQuery over more modern technologies such as React.js because the structure is more intuitive and there are fewer idependant technologies. In addition we have structured the project so that all relevant CSS and Javascript is contained within the tempalates. We chose to defy the convention of splitting code into seporate files so that it is obvious what code affects what and to maximise decoupling, thus minimising the chance of changes having unexpected consiquences elsewhere.

All the code you need can be found at: https://github.com/jkittley/LittleSense

Why |project|
-------------
My mother always said should have a little sense and listen.

Contribute
----------
- Issue Tracker: https://github.com/jkittley/LittleSense/issues
- Source Code: https://github.com/jkittley/LittleSense

Support
-------
If you are having issues, please let us know by submitting an issue.

License
-------
The project is licensed under the BSD license.

Index
=====

* :ref:`genindex`


