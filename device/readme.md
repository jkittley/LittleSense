# Sensor Store - Device
This folder contains code for various platforms and communication channels. Each folder contains instructions and the required part to setup a device to send sensor readings to the [server](/server/readme.md).  

Sensor store does it’s best to minimise configuration server side. To help this, all sensor devices should transmit readings where the files name is constructed as `dtype_name_unit` the name can include extra semicolons e.g. float_light_level_lux is valid. Below is a list of accepted dtypes...

Units are used to group and convert readings. You can use anything you like here. However there are known units...

## Platforms
Below is a list of the currently supported platforms:

- [Ardunio](arduino/readme.md)

