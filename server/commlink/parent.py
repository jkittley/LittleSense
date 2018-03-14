# =============================================================================
# Parent class for all communication links.
# =============================================================================

import json
from tinydb import TinyDB, Query
from utils import Device
from utils.exceptions import UnknownDevice

class InvaidPacketFormatter(Exception):
    pass

class CommLink:
    
    def __init__(self, influx_instance):
        self.db = influx_instance
        self.commlink_name = "NONE"
        
    def validate_formatter(self, func):
        return func
        # raise InvaidPacketFormatter()

    def _build_response(self, **kwargs):
        respose = {
            'success': kwargs.get('success', False),
            'errors': kwargs.get('errors', [])
        }
        return {
            'respose': respose,
            'json_response': json.dumps(respose)
        }


    def _save_reading(self, utc, device_id, sensor_readings):
        dev = Device(device_id, True)
        return dev.add_reading(utc, sensor_readings, self.commlink_name)
   

       

    
    def _ping(self):
        print("ping")
        return (True, "")