# Sensor Store - Device
This folder contains code for various platforms and communication channels. Each folder contains instructions and the required part to setup a device to send sensor readings to the [server](/server/readme.md).  

Sensor store does it’s best to minimise configuration server side. To help this, all sensor devices should transmit readings where the variable name is constructed as `<dtype>_<variable-name>_<unit>`.

- dtype: (Data type) can be either int, float, bool, str or string. 
- name: The name can include extra semicolons e.g. float_light_level_lux is valid. 
- unit: Unit can be anything you want, but is used to automatically group reading in some visualisations.

## Platforms
Below is a list of the currently supported platforms:

- [Ardunio](arduino/readme.md)

