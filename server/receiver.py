# =============================================================================
# This script is designed to be run as a background service using Systemd. The
# purpose of this script is to receive information from the sensors connected
# via a communication link e.g. Radio or GPIO pins.
# =============================================================================

import signal, sys, string, time
from random import randint, choice
import click, arrow
from utils import Logger

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

def pack_formatter_rf69(unformatted):
    utc = arrow.utcnow()
    data = unformatted.get('data')
    output_dict = dict(
        sound_pressure = data[0] + data[1]<<8,
        battery_level  = data[2] + data[3]<<8,
        mode           = data[4] + data[5]<<8,
        node_id   = unformatted.get('sender_id'),
        rssi      = unformatted.get('rssi')
    )
    return utc, "device_{}".format(output_dict['node_id']), output_dict


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
        return utc, "test_device_17", output_dict1
    else:
        return utc, "test_device_203", output_dict2

# =============================================================================
# Main event loop manager
# =============================================================================

@click.command()
@click.option('--test/--no-test', default=False)
def launch(test=False):

    if test:
        from commlink.test import RadioTest
        comm = RadioTest(pack_formatter_test)
        log.debug("Radio TEST Starting...")
    else:
        # Initialise
        from commlink.rfm69 import RadioRFM69
        comm = RadioRFM69(pack_formatter_rf69)
        log.debug("Radio RFM69 Starting...")
    
    # Add radio to pool
    comms_pool.append(comm)
    comm.initialise()
    
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







    