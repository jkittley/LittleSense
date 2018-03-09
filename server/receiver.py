# =============================================================================
# This script is designed to be run as a background service using Systemd. The
# purpose of this script is to receive information (rx) and send information
# (tx) to the sensors via a communication link.
# =============================================================================

import time
import arrow
import signal, sys
from utils import Logger
import click

log = Logger()
radios = []

#this should properly shutdown the rfm69 instance
def signal_handler(signal, frame):
    print ('Stopping process...')
    for radio in radios:
        radio.shutdown()
    sys.exit(0)

@click.command()
@click.option('--test/--no-test', default=False)
def launch(test=False):

    if test:
        from commlink.test import RadioTest
        radio = RadioTest()
        log.debug("Radio TEST Starting...")
    else:
        # Initialise
        from commlink.rfm69 import RadioRFM69
        radio = RadioRFM69()
        log.debug("Radio RFM69 Starting...")
    
    # Add radio to pool
    radios.append(radio)
    radio.initialise()
    
    # This loop tries repeatedly to make receive work.
    while True:
        try:
            radio.receive()
        except Exception as e:
            log.error("BG Service Receiving...", error=e)
        time.sleep(15)

if __name__ == "__main__":
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    launch()







    