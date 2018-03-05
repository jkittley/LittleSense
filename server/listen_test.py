import time 
from datetime import datetime
from commlink import RFM69
from config import settings
from random import randint
from utils import get_InfluxDB

ifdb = get_InfluxDB()
comm = RFM69(ifdb)

while True:

    for i in range(0,5):
        data = dict(
            float_signal_db=randint(0,100) / 10.0,
            float_audio_level_db=randint(1,110) / 10.0,
            int_light_level_lux=randint(100,200),
            float_temp_f=randint(180,350) / 10.0,
        )
        print (data)
        comm.rx(datetime.utcnow(), 'test_device_{}'.format(i), data)
    
    for i in range(10,15):
        data = dict(
            float_temp_c=randint(180,350) / 10.0, 
            int_signal_percent=randint(0,100),
            bool_switch_state=randint(0,1)
        )
        print (data)
        comm.rx(datetime.utcnow(), 'test_device_{}'.format(i), data)

    # for i in range(10,15):
    #     data = dict(
    #         float_temp_c="HELLO", 
    #         int_signal_percent=True,
    #         bool_switch_state=10.0
    #     )
    #     print (data)
    #     comm.rx(datetime.utcnow(), 'test_device_{}'.format(i), data)

    time.sleep(1)