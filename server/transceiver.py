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
from utils import SerialLogger, SerialTXQueue, Logger, Device

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
            try:
                asjson = json.loads(str(self.json_str))
                utc = "NOW" if 'utc' not in asjson else asjson['utc']
                field_id = "{}_{}_{}".format(asjson['dtype'], asjson['field'], asjson['unit'])
                fields = dict()
                fields[field_id] = asjson['value']
                device = Device(asjson['device_id'], True)
                device.add_reading(utc, fields, 'serial_port')
            except KeyError as e:
                log.error('Serial data missing key', exception=str(e))
            except Exception as e:
                log.error('Serial receive failed', exception=str(e))
                
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
