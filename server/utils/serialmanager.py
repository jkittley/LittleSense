from config import settings
from .influx import get_InfluxDB
import arrow, json, math
from functools import wraps
from tinydb import TinyDB, Query
import uuid
import os, logging
from logging.handlers import RotatingFileHandler
from unipath import Path

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
# create a file handler

log_file = Path(os.path.realpath(__file__)).parent.parent.child('data').child('serial.log')
if not log_file.exists():
    log_file.write_file("")
handler = RotatingFileHandler(log_file, mode='a', maxBytes=5*1024*1024, backupCount=2, encoding=None, delay=0)
handler.setLevel(logging.INFO)
# create a logging format
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
# add the handlers to the logger
logger.addHandler(handler)

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
    """Log specifically designed for the serial data."""

    def add_message(self, rxtx:str, message:str):
        """Add a serial message to the log.
        
        Args:
            rxtx: Was the message received (rx) or sent (tx)
            message: Message to record

        """
        logger.info("{} {}".format(rxtx, str(message).strip()))
        
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

    def tail(self, nlines:int=15):
        """Return the tail of the logg file
        
        Args:
            nlines: Number of lines to return

        Returns:
            str: lines seporated with newlines

        """
        bufsize = 8192
        fsize = os.stat(log_file).st_size
        iter = 0
        with open(log_file) as f:
            if bufsize > fsize:
                bufsize = fsize-1
            data = []
            while True:
                iter +=1
                f.seek(fsize-bufsize*iter)
                data.extend(f.readlines())
                if len(data) >= nlines or f.tell() == 0:
                    return ''.join(data[-nlines:])
                           
    def __len__(self):
        try:
            counts = next(self._ifdb.query('SELECT count(*) FROM "{}"'.format(settings.INFLUX_SERIAL)).get_points())
            return counts['count_message']
        except:
            return 0

    def __iter__(self):
        return (x for x in self.tail())

    def __str__(self):
        return "Serial Logger"

    def __repr__(self):
        return "SerialLogger()"