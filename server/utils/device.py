import json
from collections import namedtuple
from tinydb import TinyDB, Query
from config import settings
from .logger import Logger
from .readings import Readings
from .metric import Metric
from .influx import get_InfluxDB
from .field import Field
from .exceptions import InvalidUTCTimestamp, UnknownDevice, InvalidReadingsRequest, IllformedField
from unipath import Path
import arrow

log = Logger()

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
            list of utils.Field: List of Fields, each carrying information pertaining to the Field.

        """
        self._load()
        out = []
        only_ids = kwargs.get('only', None)
        for field_id in self._seen_field_ids:
            if only_ids is not None and field_id not in only_ids:
                continue
            try:
                out.append(Field.fromString(field_id)) 
            except IllformedField as e:
                log.error('device.fields() returning an ill formed field name! Skipped.', exception=str(e))
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
        
    def add_reading(self, utc:str, field_values, commlink_name:str):
        """Add a new reading for the device.
        
        Args:
            utc: UTC timestamp as a string.
            field_values (list of utils.FieldValues): List of FieldValue objects
            commlink_name: Name of the commulication link through which the reading was devivered 
        
        Raises:
            utils.exceptions.InvalidUTCTimestamp: If UTC value is incorrectly formatted
            utils.exceptions.IllformedField: If field name does not conform to the prescribed pattern or conatins eronious values.

        """
        # Clean and validate incoming data
        if utc.lower() == "now":
            utc_str = arrow.utcnow().format()
        else:
            utc_str = self._clean_utc_str(utc)

        # Add seen fields to device register
        self._add_to_seen_fields(field_values)

        # Create reading
        reading = {
            "measurement": settings.INFLUX_READINGS,
            "tags": {
                "device_id": self.id,
                "commlink": commlink_name
            },
            "time": utc_str,
            "fields": { fv.field.id: fv.value for fv in field_values }
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
            metrics (list of utils.Metrics): Limit fields to this lists field_ids (defaults to all)
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

        # Metrics to get - defaults to all
        metrics = kwargs.get('metrics', None)
      
        # Fields
        query_string, query_fields = self._metrics_to_query(metrics)
        if len(query_fields) == 0:
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
            fields=query_string,
            fill=fillmode,
            limit="LIMIT {0}".format(limit)
        )
        readings = self._ifdb.query(q)
        readings = list(readings.get_points())
        # Return
        return Readings(readings, self.id, s, e, interval, fillmode, query_fields)

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

    def _add_to_seen_fields(self, field_values):
        self._load()
        seen = self._seen_field_ids
        seen = list(set(seen + [ fv.field.id for fv in field_values ]))
        self._tydb.update({ 'fields': seen }, Query().device_id == self.id)
        self._load()   

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
    
    def _metrics_to_query(self, metrics):
        
        if type(metrics) is not list:
            metrics = [Metric(self, f, None) for f in self.fields()]
    

        query_fields = {}
        query_string = ""

        for metric in metrics:

            if metric.field.id is None:
                log.error('_fields_to_query missing field_id')
                continue

            if metric.field.is_numeric:
                allowed_aggfuncs = Metric.AGGR_FUNC_NUMERIC
            elif metric.field.is_boolean:
                allowed_aggfuncs = Metric.AGGR_FUNC_BOOLEAN
            elif metric.field.is_string:
                allowed_aggfuncs = Metric.AGGR_FUNC_STRING
            else:
                log.error('_metrics_to_query field is not numeric, boolean or string!')
                continue
          
            # If aggregation function valid
            if metric.aggregation_function not in allowed_aggfuncs:
                log.error('_metrics_to_query aggregation function {} not permitted'.format(metric.aggregation_function), field=metric.field.as_dict())
                continue
            
            query_field_name = "{device_id}__{aggrfunc}__{field_id}".format(
                field_id=metric.field.id, 
                aggrfunc=metric.aggregation_function, 
                device_id=self.id
            )
            query_string += '{aggrfunc}("{field_id}") AS "{query_field_name}", '.format(
                field_id=metric.field.id, 
                aggrfunc=metric.aggregation_function, 
                query_field_name=query_field_name
            )

            query_fields[query_field_name] = Field(metric.field.dtype, query_field_name, metric.field.unit) 

        return query_string[:-2], query_fields
        
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


