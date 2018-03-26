from config import settings
from .influx import get_InfluxDB
import arrow, json, math
from functools import wraps
from tinydb import TinyDB, Query
import uuid

class SerialTXQueue():
    """An interface between the web UI and serial interface. Messages can be added to the queue which will then be sent by the background transeiver service."""
    
    def __init__(self):
        self.queue = TinyDB(settings.TINYDB['db_serial_tx'])

    def push(self, message:str):
        """Add a messages to the send queue.
        
        Args:
            message: The message to be transmitted.

        Returns:
            int: A unique reference for the newly created message in the queue. 

        """
        data = {
            'message': message, 
            'time': arrow.utcnow().format()
        }
        return self.queue.insert(data)
    
    def remove(self, message_id:int):
        """Remove msg from TX queue
        
        Args:
            message_id: The unique id of the message in the queue to remove.

        """
        self.queue.remove(doc_ids=[message_id])

    def pop(self):
        """Return and remove the next message in the queue.
        
        Returns: 
            dict: Dictionary containing the message and meta data i.e. doc_id - the unique id of the message in the queue, and the time it was created. Returns "None" if no messages in the queue.

        """
        try:
            result = self.queue.all()[0]
            self.remove(result.doc_id)
            return result
        except IndexError:
            return None

    def __iter__(self, **kwargs):
        return (x for x in self.queue.all())
    
    def __len__(self, **kwargs):
        return len(self.queue)

    def __str__(self):
        return "Serial TX Queue"

    def __repr__(self):
        return "SerialTXQueue()"

  
class SerialLogger():
    """Log specifically designed for the serial data with InfluxDB backend. Data has a special retention poilicy meaning that it is automatically destroyed after an hour."""

    def __init__(self):
        self._ifdb = get_InfluxDB()
        self._ifdb.create_retention_policy('serial_data', '1h', 1, default=False)

    def add_message(self, rxtx:str, message:str):
        """Add a serial message to the log.
        
        Args:
            rxtx: Was the message received (rx) or sent (tx)
            message: Message to record

        """
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
        
    def rx(self, message:str):
        """Shortcut to add_message for RX
        
        Args:
            message: Message to record (as RX)
        
        """
        self.add_message('rx', message)

    def tx(self, message:str):
        """Shortcut to add_message for TX

        Args:
            message: Message to record (as TX)
        
        """
        self.add_message('tx', message)

    def all(self):
        """Short cut to filter with no params"""
        return self.filter()

    def filter(self, **kwargs):
        """List serial messages in log.

        Keyword Args:
            start: Start of search period
            end: Endo of search period

        """
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
        return (x for x in self.all())

    def __str__(self):
        return "Serial Logger"

    def __repr__(self):
        return "SerialLogger()"