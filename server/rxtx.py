# =============================================================================
# This script is designed to be run as a background service using Systemd. The
# purpose of this script is to receive information (rx) and send information
# (tx) to the sensors via a communication link.
# =============================================================================

from commlink import RFM69
from influxdb import InfluxDBClient
from datetime import datetime
import time
from config.general import INFLUX_DBNAME
from random import randint

ifdb = InfluxDBClient('localhost', 8086, 'root', 'root', INFLUX_DBNAME)
comm = RFM69(ifdb)

ifdb.create_database(INFLUX_DBNAME)


# Function needed to delete all readings for unregistered devices older than 24hrs
# 
# 

while True:

    for i in range(0,20):
        data = dict(
            signal=randint(0,100),
            db=randint(1,110),
            lux=randint(100,200)
        )
        print (data)
        comm.rx(datetime.utcnow(), 'test_device_{}'.format(i), data)
    
    for i in range(20,25):
        data = dict(
            temp=randint(180,350) / 10.0, 
            signal=randint(0,100)
        )
        print (data)
        comm.rx(datetime.utcnow(), 'test_device_{}'.format(i), data)

    time.sleep(1)