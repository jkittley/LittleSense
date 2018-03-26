# =============================================================================
# This script is designed to be run as a background service using Systemd. The
# purpose of this script is to receive information from the sensors connected
# via a communication link e.g. Radio or GPIO pins.
# =============================================================================
import asyncio, sys, json, time
import serial_asyncio
from serial.serialutil import SerialException
import signal
import click, arrow
from utils import SerialLogger, SerialTXQueue, Logger

loop = None
log = Logger()
serial_log = SerialLogger()
tx_queue = SerialTXQueue()

# On the Pi you can run 'ls /dev/{tty,cu}.*' to list all serial ports.
SERIAL_PORT = '/dev/tty.usbmodem1411'

async def transmitter(verbose):
    while True:
        next_message = tx_queue.pop()
        if next_message is not None:
            serial_log.tx(next_message['message'])
            if verbose:
                print("Processing", next_message)
        await asyncio.sleep(0)
    
class Output(asyncio.Protocol):

    def __init__(self):
        self.json_str = "" 

    def connection_made(self, transport):
        self.transport = transport
        print('port opened', transport)
        transport.serial.rts = False  # You can manipulate Serial object via transport
        transport.write(b'Hello, World!\n')  # Write serial data via transport

    def data_received(self, data):
        # print('data received', repr(data))
        self.json_str += data.decode("utf-8")
        if b'\n' in data:
            serial_log.rx(str(self.json_str))
            self.json_str = ""
            # self.transport.close()

    def connection_lost(self, exc):
        print('port closed')
        self.transport.loop.stop()

    def pause_writing(self):
        print('pause writing')
        print(self.transport.get_write_buffer_size())

    def resume_writing(self):
        print(self.transport.get_write_buffer_size())
        print('resume writing')

# =============================================================================
# Main event loop manager
# =============================================================================

@click.command()
@click.option('--test/--no-test', default=False)
@click.option('--verbose/--no-verbose', default=False)
def launch(test=False, verbose=False):

    loop = asyncio.get_event_loop()

    coro = serial_asyncio.create_serial_connection(loop, Output, SERIAL_PORT, baudrate=115200)
    loop.run_until_complete(coro) 
    
    loop.create_task(transmitter(verbose))
    
    loop.run_forever()
    loop.close()



    # if test:
    #     from commlink.test import ManagerTEST
    #     comm = ManagerTEST(pack_formatter_test, save_reading, verbose=True)
    #     log.debug("Radio TEST Starting...")
    # else:
    #     # Initialise
    #     from commlink.rfm69 import ManagerRFM69
    #     comm = ManagerRFM69(pack_formatter_rf69, save_reading, verbose=verbose)
    #     log.debug("Radio RFM69 Starting...")
    
    # # Add radio to pool
    # comms_pool.append(comm)
    # comm.initialise()
    
    # # comm.transmit(2, "Hi ya")

    # # This loop tries repeatedly to make receive work.
    # while True:
    #     try:
    #         comm.receive()
    #     except Exception as e:
    #         log.error("BG Service Receiving...", error=str(e))
    #         print (e)
        


# # =============================================================================
# # Do not edit below this line
# # =============================================================================

def signal_handler(signal, frame):
    print ('Stopping process...')
    if loop is not None:
        loop.stop()
    sys.exit(0)

if __name__ == "__main__":
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    launch()




# import signal, sys, string, time
# from random import randint, choice
# import click, arrow
# from utils import Logger, Device
# from utils.exceptions import InvalidPacket

# log = Logger()
# comms_pool = []

# # =============================================================================
# # Formatter functions. Each commlink class takes a formatter function when
# # instansiated. The purpose of the function is to format the received packet
# # data into a dictionary of field:value pairs which will be saved to the 
# # database. Each class will send different data in a dict called 'unformatted'
# # you must see the instructions for the radio class you are using. Every 
# # formatter must return three thing: timestamp (utc), device_id (sting) and a 
# # dictionary of field:value pairs as described above.
# # =============================================================================
# # Little Sense does it’s best to minimise configuration server side. To help 
# # this, all sensor devices should transmit readings where the variable name 
# # is constructed as `<dtype>_<variable-name>_<unit>`.
# # 
# # - dtype: (Data type) can be either int, float, bool, str or string. 
# # - name:  The name can include extra semicolons e.g. float_light_level_lux is 
# #          valid. 
# # - unit:  Unit can be anything you want, but is used to automatically group 
# #          reading in some visualisations.
# # =============================================================================


# # =============================================================================
# # Function to act on the formatted packets (returned by the punction above)
# # =============================================================================

# def save_reading(commlink_name, utc, device_id, sensor_readings):
#     dev = Device(device_id, True)
#     dev.add_reading(utc, sensor_readings, commlink_name)
#     return











    