# =============================================================================
# This script is designed to be run as a background service using Systemd. The
# purpose of this script is to receive information from the sensors connected
# via a communication link e.g. Radio or GPIO pins.
# =============================================================================
import sys, json, time, string, io
from random import randint, choice
import serial
from serial.serialutil import SerialException
import signal
import click, arrow
from utils import SerialLogger, SerialTXQueue, Logger, Device, Field, FieldValue

loop = None
log = Logger()
serial_log = SerialLogger()
tx_queue = SerialTXQueue()
comments = []

# On the Pi you can run 'ls /dev/{tty,cu}.*' to list all serial ports.
SERIAL_PORT = '/dev/tty.usbmodem1461'


def process_json(line, test, verbose):
    if verbose:
        print('JSON', line)
    serial_log.rx('JSON: ' + line)
    try:
        asdict = json.loads(line)
        utc = "NOW" if 'utc' not in asdict else asdict['utc']

        fvs = FieldValue(Field.fromDict(asdict), asdict['value'])
        device = Device(asdict['device_id'], True)

        device.add_reading(utc, [fvs], 'serial_port')
    except KeyError as e:
        log.error('Serial data missing key', exception=str(e))
        if verbose:
            print('Exception', e)
    # except Exception as e:
    #     log.error('Serial receive failed', exception=str(e))
    #     if verbose:
    #         print('Exception', e)
    
def process_comment(comments, test, verbose):
    print('Comment', comments)
    serial_log.rx('Comment: ' + '| '.join(comments))

def read_serial(ser, test, verbose, comments):
    line = ser.readline().decode("utf-8").strip()
    if verbose:
        print('data received', line)

    if line.startswith('{') and line.endswith('}'):
        process_json(line, test, verbose)
    elif line.startswith('#'):
        comments.append(line)
    else:
        process_comment(comments, test, verbose)
        comments = []
            
def test_data_generator(verbose):
    if verbose:
        print("Generating test data")

    device1 = Device('test_device_1', True)
    field_values = [
        FieldValue(Field("float", "signal", "db"), randint(0,450)/10.0),
        FieldValue(Field("float", "audio_level", "db"), randint(0,450)/10.0),
        FieldValue(Field("int", "light_level", "lux"), randint(0,100)),
        FieldValue(Field("float", "temp", "f"), randint(0,72)),
    ]
    device1.add_reading("NOW", field_values, 'test_data')
    
    device2 = Device('test_device_2', True)

    field_values = [
        FieldValue(Field("float", "audio_level", "db"), randint(20,35)/10.0),
        FieldValue(Field("float", "battery_level", "volts"), randint(20,35)/10.0),
        FieldValue(Field("float", "signal_strength", "db"), randint(20,35)/10.0),
        FieldValue(Field("boolean", "switch", "state"), randint(0,1)),
        FieldValue(Field("string", "message", "text"), 'HEY' + ''.join(choice(string.ascii_uppercase + string.digits) for _ in range(10)) ),
    ]
    device2.add_reading("NOW", field_values, 'test_data')

def transmit(ser, verbose):
    next_message = tx_queue.pop()
    if next_message is not None:
        serial_log.tx(next_message['message'])
        if verbose:
            print("Processing", next_message)
        sio = io.TextIOWrapper(io.BufferedRWPair(ser, ser))
        sio.write("{}\n".format(next_message))
        sio.flush() # it is buffering. required to get the data out *now*


# =============================================================================
# Main event loop manager
# =============================================================================

@click.command()
@click.option('--test/--no-test', default=False)
@click.option('--verbose/--no-verbose', default=False)
def launch(test=False, verbose=False):
    if test:
        while True:
            test_data_generator(verbose)
            time.sleep(5)
    else:
        with serial.Serial(SERIAL_PORT, 115200, timeout=10) as ser:
            while True:
                read_serial(ser, test, verbose, comments)
                transmit(ser, verbose)
                if not ser.is_open:
                    ser.open()
                

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
