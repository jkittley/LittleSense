# =============================================================================
# RFM 69 RADIO
# 
# !!! You should NOT need to edit this file !!!
# Please use the formatter function to process packet data.
# 
# =============================================================================

import arrow
import time
from commlink import CommLink
from uuid import getnode as get_mac_address
from utils import Logger
from commlink.rfm69_helpers.Rfm69 import Rfm69
from commlink.rfm69_helpers.RFM69registers import RF69_433MHZ

log = Logger()

class RadioRFM69(CommLink):

    def __init__(self, packet_formatter_func):
        self.MAC_ADDRESS = get_mac_address()
        self.commlink_name = "RadioRFM69"
        self.packet_formatter = self.validate_formatter(packet_formatter_func)

    def initialise(self):
        # freqBand, nodeID, networkID, isRFM69HW = False, intPin = 18, rstPin = 29, spiBus = 0, spiDevice = 0
        self.radio = Rfm69(RF69_433MHZ, 1, 100)
        log.debug("Rfm69 initialized")
        log.debug("Rfm69 Performing rcCalibration")
        self.radio.rcCalibration()
        log.debug("Rfm69 setting high power to false")
        self.radio.setHighPower(False)
        log.debug("Rfm69 setting encryption")
        self.radio.encrypt("ABCDEFGHIJKLMNOP")
        return self.radio

    def receive(self):
        log.debug("Rfm69 receive started")
        while True:
            self.radio.receiveBegin()
            while not self.radio.receiveDone():
                time.sleep(.1)

            # Respond to acknowledgement request
            if self.radio.ACKRequested():
                self.radio.sendACK()
                log.debug("Rfm69 ACKRequested response sent")
                # continue

            # Prep data from packets
            try:
                unformatted = dict(
                    data=self.radio.DATA, 
                    sender_id=self.radio.SENDERID,
                    rssi=self.radio.RSSI
                )
                utc, device_id, formatted = self.packet_formatter(unformatted)
                log.debug("Rfm69 Packet receieved", **formatted)
                self._save_reading(utc, device_id, formatted)
            except:
                log.error("Rfm69 Failed to format and save packet", **unformatted)
            
   
    
    def shutdown(self):
        log.debug("Rfm69 shutting down")
        self.radio.shutdown()