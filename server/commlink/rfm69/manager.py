# =============================================================================
# RFM 69 RADIO
# 
# !!! You should NOT need to edit this file !!!
#
# All commlink classes take two functions. The first is used to format the 
# received packet into a dictionary e.g. { dtype_name_unit: value }. The second
# tels the commlink class how to save the function.
# 
# =============================================================================

import arrow
import time
from commlink import CommLink
from uuid import getnode as get_mac_address
from .Rfm69 import Rfm69
from .Rfm69registers import RF69_433MHZ
from utils.exceptions import InvalidPacket
import itertools, sys

class ManagerRFM69(CommLink):
    
    def initialise(self, **kwargs):
        # freqBand, nodeID, networkID, isRFM69HW = False, intPin = 18, rstPin = 29, spiBus = 0, spiDevice = 0
        self.radio = Rfm69(RF69_433MHZ, 1, 10, True)
        self._report("Rfm69 initialized")
        self._report("Rfm69 Performing rcCalibration")
        self.radio.rcCalibration()
        self._report("Rfm69 setting high power")
        self.radio.setHighPower(True)
        # self._report("Rfm69 setting encryption")
        # self.radio.encrypt("ABCDEFGHIJKLMNOP")
        self.COMMLINK_NAME = "RadioRFM69"
        return self.radio

    def receive(self, **kwargs):
        self._report("Rfm69 receive started")
        while True:
            self._report('Loop start')
            
            self.radio.receiveBegin()
            spinner = itertools.cycle(['-', '/', '|', '\\'])
            while not self.radio.receiveDone():
                time.sleep(.1)
                if self.verbose == True:
                    sys.stdout.write(next(spinner))  # write the next character
                    sys.stdout.flush()                # flush stdout buffer (actual character display)
                    sys.stdout.write('\b')        

            self._report('Receive Done')
            try:
                unformatted = dict(
                    data=self.radio.DATA, 
                    sender_id=self.radio.SENDERID,
                    rssi=self.radio.RSSI
                )
                self._report("Rfm69 Packet unformatted:", **unformatted)
                utc, device_id, formatted = self.packet_formatter(unformatted)
                self._report("Rfm69 Packet formatted:", **formatted)
                # Save reading
                self.save_reading(self.COMMLINK_NAME, utc, device_id, formatted)
                
            except InvalidPacket as e:
                self._error('Rfm69 InvalidPacket', e)
            except Exception as e:
                self._error("Rfm69 Failed to format and save packet", **unformatted)
                self._error("Rfm69 Failed to format and save packet", e)
   

            # Respond to acknowledgement request
            if self.radio.ACKRequested():
                # 
                # Be warned sendACK will exec receiveDone() which will reset sender
                # ID etc.
                # 
                self.radio.sendACK(self.radio.SENDERID)
                self._report("Rfm69 ACKRequested response sent")
             

            time.sleep(1)

    def transmit(self, destination, message="No message", retry=3, retry_wait_ms=500):
        if not isinstance(destination, int):
            raise Exception('Destination must be int')
        if not isinstance(message, str):
            raise Exception('Message must be string')
        if not isinstance(retry, int):
            raise Exception('Retry times must be int')
        if not isinstance(retry_wait_ms, int) or retry_wait_ms < 100:
            raise Exception('Retry wait must be int, in ms and > 100')
        self._report("Rfm69 sending message:", message=message)
        if self.radio.sendWithRetry(destination, message, retry, retry_wait_ms):
            self._report("Rfm69 ACKReceived")

    def shutdown(self, **kwargs):
        self._report("Rfm69 shutting down")
        self.radio.shutdown()