# =============================================================================
# RFM 69 RADIO
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

    def __init__(self):
        self.MAC_ADDRESS = get_mac_address()
        self.commlink_name = "RadioRFM69"

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
            data = dict(
                sound_pressure = self.radio.DATA[0] + self.radio.DATA[1]<<8,
                battery_level  = self.radio.DATA[2] + self.radio.DATA[3]<<8,
                mode           = self.radio.DATA[4] + self.radio.DATA[5]<<8,
                node_id   = self.radio.SENDERID,
                rssi      = self.radio.RSSI
            )
            log.debug("Rfm69 Packet receieved", **data)
            device_id = "node_{}".format(data['node_id'])
            self._save_reading(arrow.utcnow(), device_id, data)
   
    
    def shutdown(self):
        log.debug("Rfm69 shutting down")
        self.radio.shutdown()