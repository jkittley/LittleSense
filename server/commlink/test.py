# =============================================================================
# TEST RADIO
# 
# !!! You should NOT need to edit this file !!!
# Please use the formatter function to process packet data.
# 
# =============================================================================

import arrow
import time
import string
from commlink import CommLink
from uuid import getnode as get_mac_address
from utils import Logger
from random import randint, choice

log = Logger()

class RadioTest(CommLink):

    def __init__(self, packet_formatter_func):
        self.MAC_ADDRESS = get_mac_address()
        self.commlink_name = "RadioTest"
        self.packet_formatter = self.validate_formatter(packet_formatter_func)

    def initialise(self):
        print("Initialised")
    
    def receive(self):
        log.debug("Rfm69 receive started")
        while True:
 
            # |Pretend to take ime receiving
            time.sleep(2)

            # Prep data from packets
            try:
                utc, device_id, formatted = self.packet_formatter({})
                log.debug("Test Radio Packet receieved", **formatted)
                self._save_reading(utc, device_id, formatted)
                print('Test packet saved', utc, device_id, formatted)
            except:
                log.error("Test Radio failed to format and save packet")
                print('Test packet failed to save')

            

    def shutdown(self):
        log.debug("RadioTest shutting down")
        