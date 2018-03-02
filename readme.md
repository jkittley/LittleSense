# Sensor Store
Welcome to Sensor Store! This project is designed to make the deployment of sensor devices and the subsequent logging and inspection of the data they produce simple.

The project architecture is composed of a RasperryPi (acting as a server and data store) and Arduino based sensor devices. For more information, please see the respective reader files: [Server](server/) and [Devices](device/).

Devices can communicate with the server via a Web API or using a number of Radio technologies. Currently RFM69 and BLE are implemented, but you can easily ass your own. If you do then please share it with us and we might included it in the project.

The project code is designed for novice user to deploy and for novice programmers (e.g. academic researchers) to modify. As such we have chosen to use technologies which make the reading and adapting of the code less difficult, for example, we chose to use jQuery over more modern technologies such as React.js because the structure is more intuitive and there are fewer idependant technologies.

To get started download this repository and follow the instructions in the relative read me files.
