# =============================================================================
# Parent class for all communication links.
# =============================================================================

import json
from tinydb import TinyDB, Query

class CommLink:
    
    def __init__(self, influx_instance):
        self.db = influx_instance
        print (influx_instance)
        

    # def rx(self, **kwargs):
    #     raise NotImplementedError()

    # def tx(self):
    #     raise NotImplementedError()

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
        readings = [
            {
                "measurement": "reading",
                "tags": {
                    "device_id": device_id
                },
                "time": utc.strftime("%c"),
                "fields": sensor_readings
            }
        ]
        self.db.write_points(readings)
        return (True, { "readings" : readings })
    
    def _ping(self):
        print("ping")
        return (True, "")