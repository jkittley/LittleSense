import json
from collections import namedtuple
from tinydb import TinyDB, Query
from config import settings
from .logger import Logger
from .readings import Readings
from .metric import Metric
from .influx import get_InfluxDB
from .exceptions import InvalidUTCTimestamp, InvalidFieldDataType, IllformedFieldName, UnknownDevice, InvalidReadingsRequest
from tinydb import TinyDB, Query
from unipath import Path
import arrow

log = Logger()


class Devices():
    
    def __init__(self):
        self.all = []
        self.registered = []
        self.unregistered = []
        self._ifdb = get_InfluxDB()
        self.update()
       
    def update(self):
        devices_in_readings = self._ifdb.query('SHOW TAG VALUES FROM "reading" WITH KEY = "device_id"').get_points()
        self.all = [ self.get(d['value'], True) for d in devices_in_readings ]
        self.registered = list(filter(lambda x: x.is_registered, self.all))
        self.unregistered = list(filter(lambda x: not x.is_registered, self.all))

    def get(self, device_id, create_if_unknown=False):
        for x in self.all:
            if x.id == str(device_id).strip():
                return x
        if create_if_unknown:
            return Device(device_id, True)
        return None

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
            "registered_devices": len(self.registered)
        }

    def purge(self, **kwargs):
        registered   = kwargs.get('registered', False)
        unregistered = kwargs.get('unregistered', False)
        registry     = kwargs.get('registry', False)

        if registry:
            Path(settings.TINYDB['db_device_reg']).remove()

        default_start = arrow.utcnow().shift(years=-10)
        start = kwargs.get('start', default_start)

        default_end = arrow.utcnow().shift(minutes=-settings.PURGE['unreg_interval'])
        end = kwargs.get('end', default_end)

        to_process = None
        if registered and unregistered:
            to_process = self.all
        elif registered:
            to_process = self.registered
        elif unregistered:
            to_process = self.unregistered
       
        if to_process is not None:
            for device in to_process:
                q = 'DELETE FROM "reading" WHERE time > \'{start}\' AND time < \'{end}\' AND "device_id"=\'{device_id}\''.format(
                    device_id=device.id,
                    start=start,
                    end=end
                )
                log.funcexec('Purged', registered=registered, unregistered=unregistered)
                self._ifdb.query(q)

        return True
 
    def to_dict(self, devs):
        return [ d.as_dict() for d in devs ]

    def as_dict(self, update=False):
        if update:
            self.update()
        return {
            "all": self.to_dict(self.all),
            "registered": self.to_dict(self.registered),
            "unregistered": self.to_dict(self.unregistered)
        }

    def __str__(self):
        return "Device List"

    def __repr__(self):
        return "Devices()"

    def __len__(self):
        return len(self.all)

    def __getitem__(self, index):
        return self.all[index]

    def __iter__(self):
        return (d for d in self.all)
   

#  ----------------------------------------------------------------------------
#  ----------------------------------------------------------------------------
#  ----------------------------------------------------------------------------


class Device():

    def __init__(self, device_id, create_if_unknown=False):
        self._tydb = TinyDB(settings.TINYDB['db_device_reg'])
        self._ifdb = get_InfluxDB()
        self.id = device_id
        self.load(create_if_unknown)

    def _create(self):
        data = {
            'device_id': self.id, 
            'name': "Unregistered",
            "registered": False
        }
        self._tydb.upsert(data, Query().device_id == self.id)

    def load(self, create_if_unknown=False):
        try:
            record = self._tydb.search(Query().device_id == self.id)[0]
        except IndexError:
            if create_if_unknown:
                self._create()
                record = self._tydb.search(Query().device_id == self.id)[0]
            else:
                raise UnknownDevice("Unknown device", self.id)

        self.name = record['name']
        self._registered = record['registered']
        self._seen_field_ids = []
        if 'fields' in record:
            self._seen_field_ids = record['fields']

    def fields(self, **kwargs):
        self.load()
        out = []
        only_ids = kwargs.get('only', None)
        for field_id in self._seen_field_ids:
            if only_ids is not None and field_id not in only_ids:
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

    def is_registered(self, setto=None):
        if setto is not None: 
            assert type(setto) == bool
            data = {
                'device_id': self.id, 
                "registered": setto
            }
            self._tydb.upsert(data, Query().device_id == self.id)
            self.load()
        return self._registered

    def set_name(self, name):
        data = {
            'device_id': self.id, 
            "name": str(name).strip()
        }
        self._tydb.upsert(data, Query().device_id == self.id)
        self.load()
        
    def add_reading(self, utc, fields, commlink_name):
        # Clean and validate incoming data
        utc_str = self._clean_utc_str(utc)
        fields  = self._clean_fields(fields, self.id)
        # Add seen fields to device register
        self._add_fields(list(fields.keys()))
        # Create reading
        reading = {
            "measurement": "reading",
            "tags": {
                "device_id": self.id,
                "commlink": commlink_name
            },
            "time": utc_str,
            "fields": fields
        }
        # Save Reading
        self._ifdb.write_points([reading])
        return True

    def last_reading(self):
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

    def get_readings(self, **kwargs):
        # Fill gabs in period none=dont fill, null=fill intervals with null readings
        fillmode = kwargs.get('fill','none')

        # Interval
        interval = self._clean_interval(kwargs.get('interval',5))
        if interval is None:
            raise InvalidReadingsRequest("Invalid interval. Must be in second (integer) and > 0")

        # Fieldnames to get - defaults to all
        requested_fields = kwargs.get('fields', None)
        
        # Fields
        qfields, fields_data = self._fields_to_query(requested_fields)
        if len(qfields) == 0:
            raise InvalidReadingsRequest("Device has no fields or none that match the requested metrics")

        # Time span
        try:
            s = arrow.get(kwargs.get('start', arrow.utcnow().shift(hours=-1)))
            e = arrow.get(kwargs.get('end', arrow.utcnow()))
        except arrow.parser.ParserError:
            raise InvalidReadingsRequest("Invalid start or end timestamp. Format example: 2018-03-08T15:29:00.000Z")
        
        # Limit
        min_results, max_results = 1, 5000
        limit = self._clean_limit(kwargs.get('limit'), min_results, max_results)
        if limit is None:
            raise InvalidReadingsRequest("Invalid limit. Must be integer between {} and {}".format(min_results, max_results))
         
        # Build Query
        q = 'SELECT {fields} FROM "reading" WHERE {timespan} AND "device_id"=\'{device_id}\' GROUP BY time({interval}) FILL({fill}) ORDER BY time DESC {limit}'.format(
            device_id=self.id, 
            interval="{}s".format(interval),
            timespan="time > '{start}' AND time <= '{end}'".format(start=s, end=e),
            fields=qfields,
            fill=fillmode,
            limit="LIMIT {0}".format(limit)
        )
        readings = self._ifdb.query(q)
    
        # Return
        return Readings(readings, self.id, s, e, interval, fillmode, limit, fields_data)
        

    # ---- Helpers ------------------------------------------------------------

    def _add_fields(self, field_ids_list):
        self.load()
        seen = self._seen_field_ids
        seen = list(set(seen + field_ids_list))
        self._tydb.update({ 'fields': seen }, Query().device_id == self.id)
        self.load()

    def _field_id_components(self, field_id):
        parts = field_id.split('_')
        if len(parts) < 3:
            raise IllformedFieldName('Too few elements')
        dtype = parts[0]
        name = " ".join(parts[1:-1]).capitalize()
        unit = parts[-1]
        return dtype, name, unit

    def _clean_fields(self, fields, device_id=None):
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
                    raise InvalidFieldDataType('Invalid data type for {}'.format(field_name))

            except Exception as e:
                log.device('Clean fields exception: {}'.format(field_name), exception=str(e), device_id=device_id)
                remove_list.append(field_name)

        # Remove bad fields
        for fn in remove_list:
            fields.pop(fn) 
        return fields

    def _clean_utc_str(self, utc_str):
        if utc_str is None or utc_str == '':
            raise InvalidUTCTimestamp('Invlaid timestamp - Missing')
        else:
            try:
                utc = arrow.get(utc_str)
                return utc.format()
            except ValueError:
                raise InvalidUTCTimestamp('Invlaid UTC timestamp: {}'.format(utc))
    
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
        
        if requested_fields is not None and len(requested_fields) > 0:
            fields_data = self.fields(only=[ x['field_id'] for x in requested_fields ])
        else:
            fields_data = self.fields()

        fields_out = {}
        qfields = ""
        for fd in fields_data:

            field_id = fd['id']
            agrfunc = None

         
            if field_id is None:
                log.error('_fields_to_query missing field_id', **fd)
                continue
            if fd['is_numeric']:
                if agrfunc is None:
                    agrfunc = "mean"
                if agrfunc in ['count', 'mean', 'mode', 'median', 'sum', 'max', 'min', 'first', 'last']:
                    qfields += '{agrfunc}("{fid}") AS "{did}__{agrfunc}__{fid}", '.format(fid=field_id, agrfunc=agrfunc, did=self.id)
                else:
                    log.debug('_fields_to_query invalid agrfunc', **fd)
                    continue
            elif fd['is_boolean']:
                if agrfunc is None:
                    agrfunc = "count"
                if agrfunc in ['count', 'first', 'last', 'max', 'min']:
                    qfields += '{agrfunc}("{fid}") AS "{did}__{agrfunc}__{fid}", '.format(fid=field_id, agrfunc=agrfunc, did=self.id)
                else:
                    log.debug('_fields_to_query invalid agrfunc', **fd)
                    continue
            elif fd['is_string']:
                log.debug('_fields_to_query dtype string not yet implemented', **fd)
                continue
            else:
                log.error('_fields_to_query unknown dtype', **fd)
                continue

            # Make new_fields data with correct names
            new_field_id = '{did}__{agrfunc}__{fid}'.format(fid=field_id, agrfunc=agrfunc, did=self.id)
            fields_out[new_field_id] = fd
            fields_out[new_field_id]['name'] = '{devname}: {agrfunc} {fname}'.format(fname=fields_out[new_field_id]['name'], agrfunc=agrfunc.capitalize(), devname=self.name)
    
        return qfields[:-2], fields_out
        
    @staticmethod
    def _clean_limit(limit, min_results, max_results):
        if limit is None:
            return max_results
        try:
            return max(min(int(limit), max_results), min_results)
        except (ValueError, TypeError):
            return None

    def as_dict(self):
        last_update, last_upd_keys =  self.last_reading()
        return { 
            "device_id": self.id,
            "registered": self.is_registered(),
            "fields": self.fields(),
            "last_update": last_update,
            "last_upd_keys": last_upd_keys
        }

    def __eq__(self, other):
        return self.id == other.id

    def __str__(self):
        return "Device {}".format(self.id)

    def __repr__(self):
        return "Device({})".format(self.id)

