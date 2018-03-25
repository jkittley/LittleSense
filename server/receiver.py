# =============================================================================
# This script is designed to be run as a background service using Systemd. The
# purpose of this script is to receive information from the sensors connected
# via a communication link e.g. Radio or GPIO pins.
# =============================================================================

import signal, sys, string, time
from random import randint, choice
import click, arrow
from utils import Logger, Device
from utils.exceptions import InvalidPacket

log = Logger()
comms_pool = []

# =============================================================================
# Formatter functions. Each commlink class takes a formatter function when
# instansiated. The purpose of the function is to format the received packet
# data into a dictionary of field:value pairs which will be saved to the 
# database. Each class will send different data in a dict called 'unformatted'
# you must see the instructions for the radio class you are using. Every 
# formatter must return three thing: timestamp (utc), device_id (sting) and a 
# dictionary of field:value pairs as described above.
# =============================================================================
# Little Sense does it’s best to minimise configuration server side. To help 
# this, all sensor devices should transmit readings where the variable name 
# is constructed as `<dtype>_<variable-name>_<unit>`.
# 
# - dtype: (Data type) can be either int, float, bool, str or string. 
# - name:  The name can include extra semicolons e.g. float_light_level_lux is 
#          valid. 
# - unit:  Unit can be anything you want, but is used to automatically group 
#          reading in some visualisations.
# =============================================================================

def pack_formatter_rf69(unformatted):
    utc = arrow.utcnow()
    data = unformatted.get('data', None)
    if data is None:
        raise InvalidPacket('data is None')
    output_dict = dict(
        sound_pressure = data[0],
        battery_level  = data[1],
        rssi = unformatted.get('rssi')
    )
    return utc, "device_{}".format(unformatted.get('sender_id')), output_dict

def pack_formatter_test(unformatted):
    # Because this is a test class there is no incomming data in the 'unformatted'
    # dictionary so we just make some up and out put it. 
    utc = arrow.utcnow()
    output_dict1 = dict(
        float_signal_db=randint(0,100) / 10.0,
        float_audio_level_db=randint(1,110) / 10.0,
        int_light_level_lux=randint(100,200),
        float_temp_f=randint(180,350) / 10.0,
    )
    output_dict2 = dict(
        float_temp_c=randint(180,350) / 10.0, 
        int_signal_percent=randint(0,100),
        bool_switch_state=randint(0,1),
        string_messages_text=''.join(choice(string.ascii_uppercase + string.digits) for _ in range(5))
    )
    # Randomly pick which one of two test devices is returning data
    if bool(randint(0,1)):
        return utc, "test_device_1", output_dict1
    else:
        return utc, "test_device_2", output_dict2

# =============================================================================
# Function to act on the formatted packets (returned by the punction above)
# =============================================================================

def save_reading(commlink_name, utc, device_id, sensor_readings):
    dev = Device(device_id, True)
    dev.add_reading(utc, sensor_readings, commlink_name)
    return


# =============================================================================
# Main event loop manager
# =============================================================================

@click.command()
@click.option('--test/--no-test', default=False)
@click.option('--verbose/--no-verbose', default=False)
def launch(test=False, verbose=False):

    if test:
        from commlink.test import ManagerTEST
        comm = ManagerTEST(pack_formatter_test, save_reading, verbose=True)
        log.debug("Radio TEST Starting...")
    else:
        # Initialise
        from commlink.rfm69 import ManagerRFM69
        comm = ManagerRFM69(pack_formatter_rf69, save_reading, verbose=verbose)
        log.debug("Radio RFM69 Starting...")
    
    # Add radio to pool
    comms_pool.append(comm)
    comm.initialise()
    
    # comm.transmit(2, "Hi ya")

    # This loop tries repeatedly to make receive work.
    while True:
        try:
            comm.receive()
        except Exception as e:
            log.error("BG Service Receiving...", error=str(e))
            print (e)
        


# =============================================================================
# Do not edit below this line
# =============================================================================

def signal_handler(signal, frame):
    print ('Stopping process...')
    for comm in comms_pool:
        comm.shutdown()
    sys.exit(0)

if __name__ == "__main__":
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    launch()







    