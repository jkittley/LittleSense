# Sensor Store
Welcome to Sensor Store! This project is designed to make the deployment of sensor devices and the subsequent logging and inspection of the data they produce simple. Our ambition is not to provide an all-in-one solution, rather we hope to provide a solid foundation on which you can build a bespoke system to suite your needs. 

The project is centered around a RasperryPi which acts as a web server and radio receiver. Sensor devices (based on Arduinos for example) can transmit data to the server via the web API or through a radio channel such as RFM69. This repositiory is divided into two sections: [Server](server/) and [Devices](device/). Please see the the respective readme files for more information.

## About the code
The project code is designed for novice user to deploy and for novice programmers (e.g. academic researchers) to modify. As such we have chosen to use technologies which make the reading and adapting of the code less difficult, for example, we chose to use jQuery over more modern technologies such as React.js because the structure is more intuitive and there are fewer idependant technologies. In addition we have structured the project so that all relevant CSS and Javascript is contained within the tempalates. We chose to defy the convention of splitting code into seporate files so that it is obvious what code affects what and to maximise decoupling, thus minimising the chance of changes having unexpected consiquences elsewhere.

## Get started
To get started download this repository and follow the instructions in the relative read me files. We suggest you get started by setting up the [Server](server/).

## Radio and communication channels
Currently the project supports:

- RFM69 - Cheap, low power ISM band transievers
- GPIO - Direct manipulation of the servers GPIO pins (coming soon)
- BLE - Bluetooth Low Energy (coming soon)

You can easily add your own, please see [these instructions](server/commlink/). If you do create a new Commlink then please share it with usso we can add it to the project.
