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

        default_end = arrow.utcnow().shift(minutes=-settings.PURGE['unreg_interval'])
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
            # print(q)
            o = self._ifdb.query(q)
            # print(o)
        
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

    def field_ids(self, **kwargs):
        return self._dev_reg.get_seen_fields(self.id)

    def fields(self, **kwargs):
        out = []
        requested_field_ids = kwargs.get('only', None)
     
        for field_id in self.field_ids():
            if requested_field_ids is not None and field_id not in requested_field_ids:
                continue
            dtype, name, unit = self._field_id_components(field_id)
            out.append({
                'id': field_id,
                'name': name,
                'dtype': dtype,
                'unit': unit,
                'is_numeric': dtype in ['float','int','pecent'],
                'is_boolean': dtype in ['bool'],
                'is_string': dtype in ['string', 'str']
            }) 
        return out

    def clean_fields(self, fields, device_id=None):
        if fields is None:
            log.device('Clean fields exception', exception="No fields")
        remove_list = []
        for field_name, value in fields.items():
            try:
                dtype, _, _ = self._field_id_components(field_name)
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
        # Remove bad fields
        for fn in remove_list:
            fields.pop(fn) 
        return fields

    def add_reading(self, utc, fields, commlink_name):
        # If device has not been seen before then add to register as unregistered
        if not self.is_registered():
            self._dev_reg.add_as_unregistered(self.id)
        # Add seen fields to device register
        self._dev_reg.add_seen_fields(self.id, list(fields.keys()))
        # Create reading
        reading = {
            "measurement": "reading",
            "tags": {
                "device_id": self.id,
                "commlink": commlink_name
            },
            "time": utc.strftime("%c"),
            "fields": self.clean_fields(fields, self.id)
        }
        # Save Reading
        self._ifdb.write_points([reading])
        return True

    @staticmethod
    def _clean_interval(interval):
        try:
            interval = int(interval)
            if interval < 1:
                raise ValueError()
            return interval
        except ValueError:
            return None

    
    def _fields_to_query(self, requested_fields):
        fields_data = self.fields(only=[ x['field_id'] for x in requested_fields ])
        fields_out = {}

        qfields = ""
        for rf in requested_fields:
            field_id = rf.get('field_id', None)
            agrfunc  = rf.get('agrfunc', None)
            field_data = list(filter(lambda x: x['id']==field_id, fields_data))[0]
   
            if field_id is None:
                log.error('_fields_to_query missing field_id', **rf)
                continue
            if field_data['is_numeric']:
                if agrfunc is None:
                    agrfunc = "mean"
                if agrfunc in ['count', 'mean', 'mode', 'median', 'sum', 'max', 'min', 'first', 'last']:
                    qfields += '{agrfunc}("{fid}") AS "{did}__{agrfunc}__{fid}", '.format(fid=field_id, agrfunc=agrfunc, did=self.id)
                else:
                    log.debug('_fields_to_query invalid agrfunc', **rf)
                    continue
            elif field_data['is_boolean']:
                if agrfunc is None:
                    agrfunc = "count"
                if agrfunc in ['count', 'first', 'last', 'max', 'min']:
                    qfields += '{agrfunc}("{fid}") AS "{did}__{agrfunc}__{fid}", '.format(fid=field_id, agrfunc=agrfunc, did=self.id)
                else:
                    log.debug('_fields_to_query invalid agrfunc', **rf)
                    continue
            elif field_data['is_string']:
                log.debug('_fields_to_query dtype string not yet implemented', **rf)
                continue
            else:
                log.error('_fields_to_query unknown dtype', **rf)
                continue

            # Make new_fields data with correct names
            new_field_id = '{did}__{agrfunc}__{fid}'.format(fid=field_id, agrfunc=agrfunc, did=self.id)
            fields_out[new_field_id] = field_data
            fields_out[new_field_id]['name'] = '{devname}: {agrfunc} {fname}'.format(fname=fields_out[new_field_id]['name'], agrfunc=agrfunc.capitalize(), devname=self.get_name())
            
            # Ref provides a trace from requested device-&-field-&-agrfunc right through the system
            fields_out[new_field_id]['ref'] = rf.get('ref', None)

        return qfields[:-2], fields_out
        
    @staticmethod
    def _clean_limit(limit, min_results, max_results):
        if limit is None:
            return max_results
        try:
            return max(min(int(limit), max_results), min_results)
        except (ValueError, TypeError):
            return None

    def get_readings(self, **kwargs):
        # Fill gabs in period none=dont fill, null=fill intervals with null readings
        fillmode = kwargs.get('fill','none')

        # Interval
        interval = self._clean_interval(kwargs.get('interval',5))
        if interval is None:
            return False, { "error" : "Invalid interval. Must be in second (integer) and > 0" }

        # Fieldnames to get - defaults to all
        requested_fields = kwargs.get('fields', None)
       
        # Fields
        qfields, fields_data = self._fields_to_query(requested_fields)
        if len(qfields) == 0:
            return False, { "error" : "Device has no fields" }

        # Time span
        try:
            s = arrow.get(kwargs.get('start', arrow.utcnow().shift(hours=-1)))
            e = arrow.get(kwargs.get('end', arrow.utcnow()))
        except arrow.parser.ParserError:
            return False, { "error" : "Invalid start or end timestamp. Format example: 2018-03-08T15:29:00.000Z" }
        
        # Limit
        min_results, max_results = 1, 5000
        limit = self._clean_limit(kwargs.get('limit'), min_results, max_results)
        if limit is None:
            return False, { "error" : "Invalid limit. Must be integer between {} and {}".format(min_results, max_results) }
         
        # Build Query
        q = 'SELECT {fields} FROM "reading" WHERE {timespan} AND "device_id"=\'{device_id}\' GROUP BY time({interval}) FILL({fill}) ORDER BY time DESC {limit}'.format(
            device_id=self.id, 
            interval="{}s".format(interval),
            timespan="time > '{start}' AND time <= '{end}'".format(start=s, end=e),
            fields=qfields,
            fill=fillmode,
            limit="LIMIT {0}".format(limit)
        )
        # print (q)
        readings = self._ifdb.query(q)
        readings = sorted(list(readings.get_points()), key=lambda k: k['time']) 
    
        # Build list of timestamps  
        timestamps = []
        by_time = {}
        for r in readings:
            timestamps.append(r['time'])
            by_time[r['time']] = r

        # Return
        return True, { 
            "count": len(readings),
            "fields": fields_data,
            'readings': by_time, 
            'timestamps': timestamps
        }

    def __eq__(self, other):
        return self.id == other.id

    def as_dict(self):
        last_update, last_upd_keys =  self.last_update()
        return { 
            "device_id": self.id,
            "registered": self.is_registered(),
            "fields": self.fields(),
            "last_update": last_update,
            "last_upd_keys": last_upd_keys
        }
   