# =============================================================================
# RFM 69 RADIO
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

    def __init__(self):
        self.MAC_ADDRESS = get_mac_address()
        self.commlink_name = "RadioTest"

    def initialise(self):
        print("Initialised")
    
    def receive(self):
        log.debug("Rfm69 receive started")
        while True:
        
            for i in range(0,5):
                data = dict(
                    float_signal_db=randint(0,100) / 10.0,
                    float_audio_level_db=randint(1,110) / 10.0,
                    int_light_level_lux=randint(100,200),
                    float_temp_f=randint(180,350) / 10.0,
                )
                print (data)
                self._save_reading(arrow.utcnow(), 'test_device_{}'.format(i), data)
    
            for i in range(10,15):
                data = dict(
                    float_temp_c=randint(180,350) / 10.0, 
                    int_signal_percent=randint(0,100),
                    bool_switch_state=randint(0,1),
                    string_messages_text=''.join(choice(string.ascii_uppercase + string.digits) for _ in range(5))
                )
                print (data)
                self._save_reading(arrow.utcnow(), 'test_device_{}'.format(i), data)

            # for i in range(10,15):
            #     data = dict(
            #         float_temp_c="HELLO", 
            #         int_signal_percent=True,
            #         bool_switch_state=10.0
            #     )
            #     print (data)
            #     self._save_reading(arrow.utcnow(), 'test_device_{}'.format(i), data)

            time.sleep(0.5)
   
    
    def shutdown(self):
        log.debug("RadioTest shutting down")
        