from collections import namedtuple
from tinydb import TinyDB, Query
from influxdb import InfluxDBClient
from influxdb.exceptions import InfluxDBClientError
from requests.exceptions import RequestException
from config.general import INFLUX_DBNAME
from .device_register import DeviceRegister
import arrow

def get_InfluxDB():
    try:
        ifdb = InfluxDBClient('localhost', 8086, 'root', 'root', INFLUX_DBNAME)
        # Test connection
        _ = ifdb.query('SHOW FIELD KEYS FROM "reading"')
        return ifdb
    except RequestException:
        return None

    

class Devices():
    
    def __init__(self):
        self._ifdb = None
        self._all = []
        self._registered = []
        self._unregistered = []
        self._ifdb = get_InfluxDB()
        if self._ifdb is not None:
            self.update()
        
        
    def get(self, update=False):
        if update:
            self.update()
        return self._all

    def registered(self, update=False):
        if update:
            self.update()
        return self._registered 

    def unregistered(self, update=False):
        if update:
            self.update()
        return self._unregistered 

    def to_dict(self, devs):
        return [ d.as_dict() for d in devs ]

    def as_dict(self, update=False):
        if update:
            self.update()
        return {
            "all": self.to_dict(self._all),
            "registered": self.to_dict(self._registered),
            "unregistered": self.to_dict(self._unregistered)
        }

    def field_names(self, **kwargs):
        q = 'SHOW FIELD KEYS FROM "reading"'
        field_names = self._ifdb.query(q).get_points()
        return [ dict(name=f['fieldKey'], type=f['fieldType']) for f in field_names ]
        
    def update(self):
        devices = self._ifdb.query('SHOW TAG VALUES FROM "reading" WITH KEY = "device_id"').get_points()
        self._all=[ Device(device_id=d['value']) for d in devices ]
        self._registered=list(filter(lambda x: x.is_registered(), self._all))
        self._unregistered= list(filter(lambda x: not x.is_registered(), self._all))
        
    def __str__(self):
        return "Devices"

   
  


class Device():

    def __init__(self, device_id):
        self.id = device_id
        self._ifdb = get_InfluxDB()
        self._dev_reg = DeviceRegister()

    def last_update(self):
        last_upds = self._ifdb.query('SELECT * FROM "reading" GROUP BY * ORDER BY DESC LIMIT 1')
        try:
            last_upd = list(last_upds.get_points(tags={'device_id': self.id}))[0]
        except IndexError:
            last_upd = None

        last_upd_keys = []
        if last_upd is not None:
            for k, v in last_upd.items():
                if v is not None:
                    last_upd_keys.append(k)

        return last_upd, last_upd_keys
        

    def is_registered(self):
        registration_record = self._dev_reg.get_record(device_id=self.id)
        return (registration_record is not None)
        
    def field_names(self, **kwargs):
        return self._dev_reg.get_seen_fields(self.id)
        # q = 'SHOW FIELD KEYS FROM "reading"'
        # field_names = self._ifdb.query(q).get_points()
        # return [ dict(name=f['fieldKey'], type=f['fieldType']) for f in field_names ]
    
    def add_reading(self, utc, fields):
        # If device has not been seen before then add to register as unregistered
        if not self.is_registered():
            self._dev_reg.add_as_unregistered(self.id)
        # Add seen fields to device register
        self._dev_reg.add_seen_fields(self.id, list(fields.keys()))
        # Create reading
        reading = {
            "measurement": "reading",
            "tags": {
                "device_id": self.id
            },
            "time": utc.strftime("%c"),
            "fields": fields
        }
        # Save Reading
        self._ifdb.write_points([reading])
        return True

    def get_readings(self, **kwargs):
        # Fill gabs in period none=dont fill, null=fill intervals with null readings
        fillmode = kwargs.get('fill','none')

        # interval
        try:
            interval = int(kwargs.get('interval',5))
            if interval < 1:
                raise ValueError()
        except ValueError:
            return False, { "error" : "Invalid interval. Must be in second (integer) and > 0" }

        # Fields
        fields, field_keys = "", []
        for fk in self.field_names():
            fields += 'mean("{0}") AS "mean_{0}", '.format(fk['name'])
            field_keys.append(dict(name="mean_{0}".format(fk['name']), type=fk['type']))

        # Timespan
        s = arrow.utcnow().shift(hours=-1)
        e = arrow.utcnow()

        try:
            if kwargs.get('start', None) is not None:
                s = arrow.get(kwargs.get('start'))
            if kwargs.get('end', None) is not None:
                e = arrow.get(kwargs.get('end'))
        except arrow.parser.ParserError:
            return False, { "error" : "Invalid start or end timestamp. Format example: 2018-03-08T15:29:00.000Z" }

        # Limit
        MAX_RESULTS = 5000
        MIN_RESULTS = 1
        limit = kwargs.get('limit', MAX_RESULTS)
        if limit is None:
            limit = MAX_RESULTS
        try:
            limit = int(limit)
            if limit > MAX_RESULTS or limit < MIN_RESULTS:
                return False, { "error" : "Invalid limit. Must be integer between {} and {}".format(MIN_RESULTS,MAX_RESULTS) }
        except (ValueError, TypeError):
            return False, { "error" : "Invalid limit. Must be integer between {} and {}".format(MIN_RESULTS,MAX_RESULTS) }
        
            
    
        # Build Query
        q = 'SELECT {fields} FROM "reading" WHERE {timespan} AND "device_id"=\'{device_id}\' GROUP BY time({interval}) FILL({fill}) ORDER BY time DESC {limit}'.format(
            device_id=self.id, 
            interval="{}s".format(interval),
            timespan="time > '{start}' AND time <= '{end}'".format(start=s, end=e),
            fields=fields[:-2],
            fill=fillmode,
            limit="LIMIT {0}".format(limit)
        )
        print (q)
        readings = self._ifdb.query(q).get_points()
        readings = list(readings)
        
        timestamps = []
        used_keys = []
        for r in readings:
            timestamps.append(r['time'])
            for k, v in r.items():
                if v is not None:
                    used_keys.append(k)

        return { 
            "count": len(readings),
            "field_keys": list(filter(lambda x: x['name'] in used_keys, field_keys)), 
            'readings': readings, 
            'timestamps': timestamps,
        }

    def __eq__(self, other):
        return self.id == other.id

    def as_dict(self):
        last_update, last_upd_keys =  self.last_update()
        return { 
            "device_id": self.id,
            "registered": self.is_registered(),
            "last_update": last_update,
            "last_upd_keys": last_upd_keys
        }
   