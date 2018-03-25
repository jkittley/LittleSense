# =============================================================================
# TEST RADIO
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
import string
from commlink import CommLink
from random import randint, choice

class ManagerTEST(CommLink):

    def initialise(self, **kwargs):
        self._report("Initialised")
        self.COMMLINK_NAME = "RadioTest"

    def receive(self, **kwargs):
        self._report("test receiver started")
        while True:
 
            # |Pretend to take ime receiving
            time.sleep(2)

            # Prep data from packets
            try:
                utc, device_id, formatted = self.packet_formatter({})
                self._report("Test Radio Packet receieved", **formatted)
                # Save reading
                self.save_reading(self.COMMLINK_NAME, utc, device_id, formatted)
                self._report('Test packet saved', utc, device_id, formatted)
            except Exception as e:
                self._error("Test Radio failed to format and save packet")
                self._report('Test packet failed to save')
                self._report(e)


    def shutdown(self, **kwargs):
        self._report("RadioTest shutting down")
        