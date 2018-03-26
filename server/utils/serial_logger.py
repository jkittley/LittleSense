from config import settings
from .influx import get_InfluxDB
import arrow, json, math
from functools import wraps

class SerialLogger():
    """Log icomming serial data with InfluxDB backend"""

    def __init__(self):
        self._ifdb = get_InfluxDB()
        self._ifdb.create_retention_policy('serial_data', '1h', 1, default=False)

    def add_line(self, rxtx, message):
        """Add a serial line to the log.
        
        Args:
            rxtx: Was the message received (rx) or sent (tx)
            msg: Message to record

        """
        print(rxtx)
        logmsg = {
            "measurement": settings.INFLUX_SERIAL,
            "tags": {
                "rxtx": str(rxtx).lower().strip(),
            },
            "time": arrow.utcnow().format(),
            "fields": {
                "message": str(message).strip()
            }
        }
        # Save Reading
        self._ifdb.write_points([logmsg], retention_policy="serial_data")
        
    def rx(self, message):
        """Add line to log for RX"""
        self.add_line('rx', message)

    def tx(self, message):
        """Add line to log for TX"""
        self.add_line('tx', message)

    def list_lines(self, **kwargs):
        start   = kwargs.get('start', arrow.utcnow().shift(days=-1))
        end     = kwargs.get('end', arrow.utcnow())
        query = 'SELECT * FROM "{policy}"."{mess}" WHERE time >= \'{start}\' and time <= \'{end}\''.format(
            policy="serial_data",
            mess=settings.INFLUX_SERIAL, 
            start=start, 
            end=end
        )
        results = list(self._ifdb.query(query).get_points())
        return results
       
    def __len__(self):
        try:
            counts = next(self._ifdb.query('SELECT count(*) FROM "{}"'.format(settings.INFLUX_SERIAL)).get_points())
            return counts['count_message']
        except:
            return 0

    def __iter__(self):
        return (x for x in self.list_lines())

    def __str__(self):
        return "Custom Logger"

    def __repr__(self):
        return "Logger()"