from collections import namedtuple
from tinydb import TinyDB, Query
from config import settings
from .device_register import DeviceRegister
from .logger import Logger
from .influx import get_InfluxDB
import arrow

log = Logger()



    

class Devices():
    
    def __init__(self):
        self._ifdb = None
        self._all = []
        self._registered = []
        self._unregistered = []
        self._ifdb = get_InfluxDB()
        if self._ifdb is not None:
            self.update()
    
    def has_db_connection(self):
        self._ifdb = get_InfluxDB()
        return self._ifdb is not None 

    def stats(self):
        if self._ifdb is None:
            return
        try:
            counts = next(self._ifdb.query('SELECT count(*) FROM "reading"').get_points())
        except StopIteration:
            counts = {}
        try:
            last_upd = next(self._ifdb.query('SELECT * FROM "reading" ORDER BY time DESC LIMIT 1').get_points())
            last_upd = arrow.get(last_upd['time'])
            humanize = last_upd.humanize()
        except StopIteration:
            last_upd = "Never"
            humanize = "Never"
        return {
            "total_readings": counts,
            "last_update": last_upd.format('YYYY-MM-DD HH:mm:ss ZZ'),
            "last_update_humanized": humanize,
            "registered_devices": len(self._registered)
        }

    def purge(self, **kwargs):
        registered   = kwargs.get('registered', False)
        unregistered = kwargs.get('unregistered', False)

        default_start = arrow.utcnow().shift(years=-10)
        start = kwargs.get('start', default_start)

        default_end = arrow.utcnow().shift(minutes=-settings.PURGE['auto_interval'])
        end = kwargs.get('end', default_end)

        if registered and unregistered:
            to_process = self.get_all()
        elif registered:
            to_process = self.get_registered()
        elif unregistered:
            to_process = self.get_unregistered()
        else:
            return False

        for device in to_process:
            q = 'DELETE FROM "reading" WHERE time > \'{start}\' AND time < \'{end}\' AND "device_id"=\'{device_id}\''.format(
                device_id=device.id,
                start=start,
                end=end
            )
            log.funcexec('Purged', registered=registered, unregistered=unregistered)
            print(q)
            o = self._ifdb.query(q)
            print(o)
        
        return True

    def get_all(self, update=False):
        if update:
            self.update()
        return self._all

    def get_device(self, device_id):
        for x in self._all:
            if x.id == device_id:
                return x
        return None

    def get_registered(self, update=False):
        if update:
            self.update()
        return self._registered 

    def get_unregistered(self, update=False):
        if update:
            self.update()
        return self._unregistered 

    def set_unregistered(self, device_id):
        d = self.get_device(device_id)
        d.unregister()

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

    def update(self):
        if self._ifdb is None:
            return
        devices = self._ifdb.query('SHOW TAG VALUES FROM "reading" WITH KEY = "device_id"').get_points()
        self._all=[ Device(device_id=d['value']) for d in devices ]
        self._registered=list(filter(lambda x: x.is_registered(), self._all))
        self._unregistered= list(filter(lambda x: not x.is_registered(), self._all))
        
    def __str__(self):
        return "Devices"

   
#  ----------------------------------------------------------------------------

class Device():

    def __init__(self, device_id):
        self.id = device_id
        self._ifdb = get_InfluxDB()
        self._dev_reg = DeviceRegister()

    def get_name(self):
        registration_record = self._dev_reg.get_record(device_id=self.id)
        return registration_record['name']

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
        
    def register(self, **kwargs):
        self._dev_reg.register_device(self.id, kwargs.get('name', None))
        
    def unregister(self, **kwargs):
        self._dev_reg.unregister_device(self.id)
        
    def is_registered(self):
        registration_record = self._dev_reg.get_record(device_id=self.id)
        if registration_record is not None:
            if 'registered' in registration_record.keys():
                return registration_record['registered']
        return False
    
    def _field_id_components(self, field_id):
        parts = field_id.split('_')
        dtype = parts[0]
        name = " ".join(parts[1:-1]).capitalize()
        unit = parts[-1]
        return dtype, name, unit

    def field_names(self, **kwargs):
        return self._dev_reg.get_seen_fields(self.id)

    def fields(self, **kwargs):
        out = []
        for field in self.field_names():
            dtype, name, unit = self._field_id_components(field)
            out.append({
                'id': field,
                'name': name,
                'dtype': dtype,
                'unit': unit
            }) 
        return out

    def clean_fields(self, fields, device_id=None):
        if fields is None:
            log.device('Clean fields exception', exception="No fields")

        remove_list = []
        for field_name, value in fields.items():
            try:
                dtype, name, unit = self._field_id_components(field_name)
                if dtype == 'float' or dtype == 'int':
                    fields[field_name] = float(value)
                elif dtype == 'bool':
                    fields[field_name] = bool(value)
                elif dtype == 'string' or dtype == 'str':
                    fields[field_name] = str(value)
                elif dtype == 'precent':
                    fields[field_name] = min(100, max(0, int(value)))
                else:
                    raise Exception('Invalid data type for {}'.format(field_name))
            except Exception as e:
                log.device('Clean fields exception: {}'.format(field_name), exception=str(e), device_id=device_id)
                remove_list.append(field_name)

        for fn in remove_list:
            fields.pop(fn) 

        return fields

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
            "fields": self.clean_fields(fields, self.id)
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
            fields += 'mean("{0}") AS "mean_{0}", '.format(fk)
            field_keys.append(dict(name="mean_{0}".format(fk), type="TODO"))
        if len(field_keys) == 0:
            return False, { "error" : "Device has no fields" }

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
        # print (q)
        readings = self._ifdb.query(q).get_points()
        readings = list(readings)
        
        # Build list of timestamps  
        timestamps = []
        used_keys = []
        for r in readings:
            timestamps.append(r['time'])

        # Modify fields to to be mean
        fields = self.fields()
        for f in fields:
            f['id'] = 'mean_' + f['id']
            f['name'] = 'Mean ' + f['name']

        # Return
        return True, { 
            "count": len(readings),
            "fields": fields,
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
   