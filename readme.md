# Little Sense
Welcome to Sensor Store! This project is designed to make the deployment of sensor devices and the subsequent logging and inspection of the data they produce simple. Our ambition is not to provide an all-in-one solution, rather we hope to provide a solid foundation on which you can build a bespoke system to suite your needs. 

![System Overview](docs/img/architecture.svg)

The project is centered around a RasperryPi which acts as a web server and radio receiver. Sensor devices (based on Arduinos for example) can transmit data to the server via the web API or through a radio channel such as RFM69. This repositiory is divided into two sections: [Server](server/) and [Devices](device/). Please see the the respective readme files for more information. Detailed documentation can be found here: http://littlesense.readthedocs.io and in each folder there is a readme file which contains some helpful information when modifying the code.

* Documentation: http://littlesense.readthedocs.io
* Website: http://littlesenseorg

## Quick Overview
In short you can through key:value pairs at the server (along with a UTC time string and a unique sender device id) and the server will record them without question. The keys encode the data type (int, string, float), the variable name (e.g. light_level) and the unit of measurement (e.g. lux). For example, a key:value pair might look like float_light_level_lux=35. This allows the system to automatically processes received data with zero configuration. Through a web interface, users can register devices for which they want to record data. Data from registered devices will be kept indefinitely. Unregistered device data will be held for a specified amount of time before they are automatically deleted. Using the web interface users can also inspect and visuals the data through customisable dashboards. 

You can add your own visualisations easily and request data from the server by passing a JSON encoded list of device_id, variable name and aggregation function (e.g. max, mean) along with a start time, end time and interval period. The system will automatically aggregat the results, returning aggregated values for each variable for each interval in the specified time period. 

