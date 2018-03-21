import json
from collections import namedtuple
from tinydb import TinyDB, Query
from config import settings
from .logger import Logger
from .readings import Readings
from .metric import Metric
from .influx import get_InfluxDB
from .exceptions import InvalidUTCTimestamp, InvalidFieldDataType, IllformedFieldName, UnknownDevice, InvalidReadingsRequest
from unipath import Path
import arrow

log = Logger()


class Devices():
    """Devices Collection (Iterator)"""

    def __init__(self):
        self.all = []
        self.registered = []
        self.unregistered = []
        self._ifdb = get_InfluxDB()
        self.update()
       
    def update(self):
        """Refreshed cache of known devices from database"""
        devices_in_readings = self._ifdb.query('SHOW TAG VALUES FROM "{}" WITH KEY = "device_id"'.format(settings.INFLUX_READINGS)).get_points()
        self.all = [ self.get(d['value'], True) for d in devices_in_readings ]
        self.registered = list(filter(lambda x: x.is_registered(), self.all))
        self.unregistered = list(filter(lambda x: not x.is_registered(), self.all))

    def get(self, device_id:str, create_if_unknown:bool=False):
        """Get (or create) a specific Device

        args:
            device_id: The unique ID of the device.

        keyword args:
            create_if_unknown: If the device_id is not known then create a new Device.

        returns:
            Device: If device_id is found returns a Device. If no mathcing device found and create_if_unknown is False then returns None. However if create_if_unknown is True then return the newly created Device()
        """
        for x in self.all:
            if x.id == str(device_id).strip():
                return x
        if create_if_unknown:
            return Device(device_id, True)
        return None

    def stats(self):
        """Generate device related statistics

        returns:
            dict: total_readings, last_update, last_update_humanized, list of registered_devices

        """
        if self._ifdb is None:
            return
        try:
            counts = next(self._ifdb.query('SELECT count(*) FROM "{}"'.format(settings.INFLUX_READINGS)).get_points())
        except StopIteration:
            counts = {}
        if 'time' in counts.keys():
            del counts['time']
        try:
            last_upd = next(self._ifdb.query('SELECT * FROM "{}" ORDER BY time DESC LIMIT 1'.format(settings.INFLUX_READINGS)).get_points())
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
        """Purge (delete) databases of requested content
        
        keyword args:
            registered (bool): Purge registered devices.
            unregistered (bool): Purge unregistered devices.
            registry (bool): Purge known device registry.
            start (str): DateTime string from when to purge data.
            end (str): DateTime string until when to purge data. 
        
        raises:
            ValueError: If ill defined purge
        """

        registered   = kwargs.get('registered', False)
        unregistered = kwargs.get('unregistered', False)
        device_ids   = kwargs.get('devices', [])

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
        else:
            to_process = self.all.copy()
            for device in to_process:
                if device.id not in device_ids:
                    to_process.remove(device)

        print(to_process)

        if to_process is not None:
            for device in to_process:
                q = 'DELETE FROM "{messurement}" WHERE time > \'{start}\' AND time < \'{end}\' AND "device_id"=\'{device_id}\''.format(
                    messurement=settings.INFLUX_READINGS,
                    device_id=device.id,
                    start=start,
                    end=end
                )
                log.funcexec('Purged', registered=registered, unregistered=unregistered, to_process=[ d.id for d in to_process])
                self._ifdb.query(q)
        else:
            raise ValueError('Nothing specified to process')

 
    def to_dict(self, devices:list):
        """Converts list of Devices to list of dictionaries

        Args:
            devices: List of Device() objects

        Returns:
            list: List of dictionaries, each representing a Device()
        """
        return [ d.as_dict() for d in devices ]

    def as_dict(self, update:bool=False) -> dict:
        """Get Devices collection represented as a dictionary

        Args:
            update: Update cache before returning.

        Returns:
            dict: Dictionary containing three lists. All devices (all), Registered devices (registered) and Unregistered devices (unregistered)
        
        """
        if update:
            self.update()
        return {
            "all": self.to_dict(self.all),
            "registered": self.to_dict(self.registered),
            "unregistered": self.to_dict(self.unregistered)
        }

    def __str__(self):
        return "Device List. Contains {} devices".format(len(self))

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
    """Individual Device
    
    Args:
        device_id: The unique ID of the device.
        create_if_unknown: If the device_id is not known then create a new Device.
    """

    def __init__(self, device_id:str, create_if_unknown:bool=False):
        self._tydb = TinyDB(settings.TINYDB['db_device_reg'])
        self._ifdb = get_InfluxDB()
        self.id = device_id
        self._load(create_if_unknown)

    def _create(self):
        """Create a new device in the database"""
        data = {
            'device_id': self.id, 
            'name': "No name",
            "registered": False
        }
        self._tydb.upsert(data, Query().device_id == self.id)

    def _load(self, create_if_unknown=False):
        """Load device from database"""
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
        """List all fields which this device has at some time reported values for.

        Keyword Args:
            only (list): List of device_ids to which results should be limited.

        Returns:
            list: List of dictionaries, each carrying information pertaining to the Field::

            [{
                'id': (str) field_id,
                'name': (str) human readable name,
                'dtype': (str) data type e.g. float, int,
                'unit': (str) unit of messurement,
                'is_numeric': (bool) is the value numeric,
                'is_boolean': (bool) is the value a boolean,
                'is_string': (bool) is the value a string
            },
            ...
            ]

        """
        self._load()
        out = []
        only_ids = kwargs.get('only', None)
        for field_id in self._seen_field_ids:
            if only_ids is not None and field_id not in only_ids:
                continue
            try:
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
            except IllformedFieldName:
                log.error('device.fields() returning an ill formed field name! Skipped.')
                
        return out

    def is_registered(self, setto=None) -> bool:
        """Set/Get device registration status

        Args:
            setto (bool): New registration status

        Returns:
            Current registration status

        """
        if setto is not None: 
            assert type(setto) == bool
            data = {
                'device_id': self.id, 
                "registered": setto
            }
            self._tydb.upsert(data, Query().device_id == self.id)
            self._load()
        return self._registered

    def set_name(self, name:str):
        """Set a human readable name for the device.
        
        Args:
            name: New human readable name for the device
            
        """
        data = dict(device_id=self.id, name=str(name).strip())
        self._tydb.upsert(data, Query().device_id == self.id)
        self._load()
        
    def add_reading(self, utc:str, fields:dict, commlink_name:str):
        """Add a new reading for the device.
        
        Args:
            utc: UTC timestamp as a string.
            fields: Dictionary of field_id:values
            commlink_name: Name of the commulication link through which the reading was devivered 
        
        Raises:
            utils.exceptions.InvalidUTCTimestamp: If UTC value is incorrectly formatted
            utils.exceptions.IllformedFieldName: If field name does not conform to the prescribed pattern or conatins eronious values.

        """
        # Clean and validate incoming data
        utc_str = self._clean_utc_str(utc)
        fields  = self._clean_fields(fields, self.id)
        # Add seen fields to device register
        self._add_fields(list(fields.keys()))
        # Create reading
        reading = {
            "measurement": settings.INFLUX_READINGS,
            "tags": {
                "device_id": self.id,
                "commlink": commlink_name
            },
            "time": utc_str,
            "fields": fields
        }
        # Save Reading
        self._ifdb.write_points([reading])
    

    def get_commlinks(self):
        """Get a list off commlinks which have provided data to this devices data
        
        Returns:
            list: List of commlink names.

        """
        all_tags = self._ifdb.query('SHOW TAG VALUES FROM "{0}" WITH KEY = "commlink" WHERE "device_id"=\'{1}\''.format(settings.INFLUX_READINGS, self.id))
        return [ x['value'] for x in list(all_tags.get_points()) if x['value'] != "NONE" ]

    def last_reading(self):
        """Get the most recent reading from this devices data.
        
        Returns:
            last_upd: The most recent reading.
            last_upd_keys: The keys assosiated with the reading.

        """
        last_upds = self._ifdb.query('SELECT * FROM "{}" GROUP BY * ORDER BY DESC LIMIT 1'.format(settings.INFLUX_READINGS))
        try:
            last_upd = list(last_upds.get_points(tags=dict(device_id=self.id)))[0]
        except IndexError:
            last_upd = None
        last_upd_keys = []
        if last_upd is not None:
            for k, v in last_upd.items():
                if v is not None:
                    last_upd_keys.append(k)
        return last_upd, last_upd_keys
        # Readings(readings, self.id, s, e, interval, fillmode, limit, fields_data)

    def get_readings(self, **kwargs):
        """Get the most recent reading from this devices data.
        
        Keyword Args:
            fill (str): A fill mode for intervals with no data. Options:: "none" don't fill and "null" fill intervals with null readings (defaults to none).
            interval (int): Reading interval in seconds. Readings are groupded into intervals (defaults to 5s).
            fields (list): Limit fields to this lists field_ids (defaults to all)
            start (arrow.arrow.Arrow): Datetime start of search period (defaults to 1 hour ago)
            end (arrow.arrow.Arrow): Datetime end of search period (defaults to now)
            limit (int): Limit the number of readings (Max = 5000, Min = 1).

        Returns:
            Readings: Readings matching query.

        """

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
        q = 'SELECT {fields} FROM "{messurement}" WHERE {timespan} AND "device_id"=\'{device_id}\' GROUP BY time({interval}) FILL({fill}) ORDER BY time DESC {limit}'.format(
            messurement=settings.INFLUX_READINGS,
            device_id=self.id, 
            interval="{}s".format(interval),
            timespan="time > '{start}' AND time <= '{end}'".format(start=s, end=e),
            fields=qfields,
            fill=fillmode,
            limit="LIMIT {0}".format(limit)
        )
        readings = self._ifdb.query(q)
        readings = list(readings.get_points())
        # Return
        return Readings(readings, self.id, s, e, interval, fillmode, fields_data)

    def count(self):
        """Count the number of readings for this device
                 
        Returns:
            int: Number of readings for this device

        """
        q = 'SELECT count(*) FROM "{messurement}" WHERE "device_id"=\'{device_id}\''.format(
            messurement=settings.INFLUX_READINGS,
            device_id=self.id, 
        )
        cmax = 0
        counts = next(self._ifdb.query(q).get_points())
        for field_id, count in counts.items():
            if count is not None and field_id != 'time':
                cmax = max(cmax, int(count))
        return cmax
        
    def get_dtypes(self, category:str=None):
        """Get the most recent reading from this devices data.
        
        Args:
            category (str): What sub type of dtypes to return. Options: numbers, strings, booleans
           
        Returns:
            list: List of acceptable data types.

        """

        alltypes = dict(
            numbers  = ['float', 'int'],
            strings  = ['string', 'str'],
            booleans = ['bool']
        )
        if category is None:
            return alltypes['numbers'] + alltypes['strings'] + alltypes['booleans']
        elif category in alltypes.keys():
            return alltypes[category]
        else:
            raise IndexError('Unknown Key Cat')


    # ---- Helpers ------------------------------------------------------------

    def _add_fields(self, field_ids_list):
        self._load()
        seen = self._seen_field_ids
        seen = list(set(seen + field_ids_list))
        self._tydb.update({ 'fields': seen }, Query().device_id == self.id)
        self._load()   

    def _field_id_components(self, field_id):
        """Split feild id into parts i.e. data rtype, name and unit"""
        parts = field_id.lower().strip().split('_')
        # Are there the right number of elements
        if len(parts) < 3:
            raise IllformedFieldName('Too few elements')
        # Are any of the elements blank
        for p in parts:
            if len(p) == 0:
                raise IllformedFieldName('Blank Elements')
        dtype = parts[0]
        if dtype not in self.get_dtypes():
            raise IllformedFieldName('Unknown data type {}'.format(dtype))

        name = " ".join(parts[1:-1]).capitalize()
        unit = parts[-1]
        return dtype, name, unit

    def _clean_fields(self, fields, device_id=None):
        if fields is None:
            log.device('Clean fields exception', exception="No fields")
        remove_list = []
        for field_name, value in fields.items():
            dtype, _, _ = self._field_id_components(field_name)
            if dtype in self.get_dtypes('numbers'):
                fields[field_name] = float(value)
            elif dtype in self.get_dtypes('booleans'):
                fields[field_name] = bool(value)
            elif dtype in self.get_dtypes('strings'):
                fields[field_name] = str(value)
            else:
                raise InvalidFieldDataType('Invalid data type for {}'.format(field_name))

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
                if agrfunc in ['count', 'first', 'last']:
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
        """Device represented as a dictionary
        
        Returns: Device represented as a dictionary::
        
            {
                "device_id": (str) The device ID,
                "registered": (bool) Is this device registered,
                "fields": {
                    see fields for details
                },
                "last_update": last update,
                "last_upd_keys": last update keys
            }

        """
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

