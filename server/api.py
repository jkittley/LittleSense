from datetime import datetime
from flask import Blueprint, abort
from flask_restful import Api, Resource, url_for, reqparse
from flask import current_app as app
from utils.exceptions import InvalidReadingsRequest, UnknownDevice
from utils import Metric, Device

api_bp = Blueprint('api', __name__)
api = Api(api_bp)

class DevicesAPI(Resource):

    def __init__(self, *args, **kwargs):
        self.devices = app.config.get('devices')

    def get(self):
        """List Devices
        
        .. :quickref: Device Collection; Get collection of devices.

        **Example request**:

        .. sourcecode:: http

          GET /api/devices/ HTTP/1.1
          Host: littlesense.local
          Accept: application/json
        
        **Example response**:

        .. sourcecode:: http

          HTTP/1.1 200 OK
          Vary: Accept
          Content-Type: application/json
        
          [
            {
                "device_id": "test_device_1",
                "fields": [
                    {
                        "is_numeric": true,
                        "unit": "db",
                        "is_string": false,
                        "dtype": "float",
                        "id": "float_audio_level_db",
                        "name": "Audio level",
                        "is_boolean": false
                    },
                    {
                        "is_numeric": true,
                        "unit": "db",
                        "is_string": false,
                        "dtype": "float",
                        "id": "float_signal_db",
                        "name": "Signal",
                        "is_boolean": false
                    }
                ],
                "last_upd_keys": [
                    "float_audio_level_db",
                    "float_signal_db",
                ],
                "last_update": {
                    "float_audio_level_db": 1.3,
                    "float_signal_db": 4.5,
                },
                "registered": false
            },
            
          ]
        
        :query filter: Filter results by "registered" or "unregistered

        :resheader Content-Type: application/json
        :status 200: posts found

        """

        parser = reqparse.RequestParser()
        parser.add_argument('filter', type=str, default="none", help='Filter results by "registered" or "unregistered"')
        args = parser.parse_args()  

        if args['filter'] == "registered":
            return self.devices.as_dict()['registered']
        elif args['filter'] == "unregistered":
            return self.devices.as_dict()['unregistered']
        else:
            return self.devices.as_dict()['all']

api.add_resource(DevicesAPI, '/devices')


class DeviceAPI(Resource):
 
    def __init__(self, *args, **kwargs):
        self.devices = app.config.get('devices')

    def get(self, device_id:str):
        """List Devices
        
        .. :quickref: Device; Get individual device info.

        **Example request**:

        .. sourcecode:: http

          GET /api/device/test_device_1 HTTP/1.1
          Host: littlesense.local
          Accept: application/json
        
        **Example response**:

        .. sourcecode:: http

          HTTP/1.1 200 OK
          Vary: Accept
          Content-Type: application/json
        
          {
            "registered": false,
            "last_upd_keys": [
                "int_light_level_lux",
                "float_signal_db",
            ],
            "device_id": "test_device_1",
            "last_update": {
                "int_light_level_lux": 135,
                "float_signal_db": 3.6,
                "time": "2018-03-20T13:52:22Z",
            },
            "fields": [
                {
                    "dtype": "int",
                    "unit": "lux",
                    "id": "int_light_level_lux",
                    "is_string": false,
                    "is_boolean": false,
                    "name": "Light level",
                    "is_numeric": true
                },
                {
                    "dtype": "float",
                    "unit": "db",
                    "id": "float_signal_db",
                    "is_string": false,
                    "is_boolean": false,
                    "name": "Signal",
                    "is_numeric": true
                }
              ]
            }
        
        :resheader Content-Type: application/json
        :status 200: device found
        :status 404: device not found
        
        """

        device = self.devices.get(device_id)
        if device is None:
            abort(404, "Device {} doesn't exist".format(device_id))
        return device.as_dict()

api.add_resource(DeviceAPI, '/device/<string:device_id>')


class ReadingsAPI(Resource):
    """Readings API"""

    def __init__(self, *args, **kwargs):
        self.devices = app.config.get('devices')

    def get(self):
        """Query readings from one or more device
        
        .. :quickref: Readings Collection; Get collection of readings.

        **Example request**:

        .. sourcecode:: http

          GET /api/readings HTTP/1.1

          ?start=2018-03-20T13%3A30%3A00Z
          &end=2018-03-20T13%3A35%3A00Z
          &fill=none
          &interval=5
          &metric[]=test_device_2,float_temp_c,mean
          &metric[]=test_device_2,bool_switch_state,count

          Host: littlesense.local
          Accept: application/json
        
        **Example response**:

        .. sourcecode:: http

          HTTP/1.1 200 OK
          Vary: Accept
          Content-Type: application/json
          
          {
            "device_ids": [
                "test_device_2"
            ],
            "count": 2,
            "readings": [
                {
                "test_device_2__count__bool_switch_state": 2,
                "test_device_2__mean__float_temp_c": 22.54,
                "time": "2018-03-20T13:34:35Z"
                },
                {
                "test_device_2__count__bool_switch_state": 2,
                "test_device_2__mean__float_temp_c": 31.25,
                "time": "2018-03-20T13:34:40Z"
                }
            ],
            "field_ids": [
                "test_device_2__count__bool_switch_state",
                "test_device_2__mean__float_temp_c"
            ],
            "fields": {
                "test_device_2__count__bool_switch_state": {
                "is_numeric": false,
                "dtype": "bool",
                "is_string": false,
                "id": "bool_switch_state",
                "name": "Unregistered: Count Switch",
                "is_boolean": true,
                "unit": "state"
                },
                "test_device_2__mean__float_temp_c": {
                "is_numeric": true,
                "dtype": "float",
                "is_string": false,
                "id": "float_temp_c",
                "name": "Unregistered: Mean Temp",
                "is_boolean": false,
                "unit": "c"
                }
            },
            "end": "2018-03-20 13:35:00+00:00",
            "start": "2018-03-20 13:30:00+00:00"
          }

        :query fill: Fill mode specifies what to do if there is no data for an interval. If set to "null" then an interval reading will be returned but with a null value. If "none" then no reading will be returned for the interval. 
        :query interval: Interval must be an integer of seconds. The results will be grouped into intervals and the aggregation function applied.
        :query start: Start of reading period (inclusive)
        :query end: End of readings period (inclusive)
        :query limit: Limit the number of results
        :query format: Results format. Default is as a list. by_time = dict where key is timestamp and value is a dict of field:value pairs

        :resheader Content-Type: application/json
        :status 200: query successful found
        :status 404: device not found
        :status 400: invalid metrics

        """
        
        # Parse variables
        parser = reqparse.RequestParser()
        parser.add_argument('fill',     type=str, default="none", help='Fill mode specifies what to do if there is no data for an interval. If set to "null" then an interval reading will be returned but with a null value. If "none" then no reading will be returned for the interval. ')
        parser.add_argument('interval', type=int, default=5,      help='Interval must be an integer of seconds. The results will be grouped into intervals and the aggregation function applied.')
        parser.add_argument('start',    type=str, default=None,   help='Start of reading period (inclusive)')
        parser.add_argument('end',      type=str, default=None,   help='End of readings period (inclusive)')
        parser.add_argument('limit',    type=int, default=None,   help='Limit the number of results')
        parser.add_argument('format',   type=str, default=None,   help='Results format. Default is as a list. by_time = dict where key is timestamp and value is a dict of field:value pairs')
        
        parser.add_argument('metric[]',  action='append', default=[], type=str, help='Must be a comma seportared list (device_is, field_id, aggregation function)')
        args = parser.parse_args()  

        metrics_by_device = {}
        try:
            for metric_str in args['metric[]']:
                m = Metric.fromString(metric_str)
                metrics_by_device.setdefault(m.device_id, []).append(m)
        except ValueError as e:
            abort(400, str(e))
      
        merged_results = None
        for device_id, metrics in metrics_by_device.items():
            # Fetch readings
            try:
                device = Device(device_id)
                device_results = device.get_readings(
                    fields   = metrics,
                    fill     = args.get('fill'), 
                    interval = args.get('interval'), 
                    start    = args.get('start'),
                    end      = args.get('end'),
                    limit    = args.get('limit')
                )
                if merged_results is None:
                    merged_results = device_results
                else: 
                    merged_results.merge_with(device_results)

            except UnknownDevice as e:
                abort(400, str(e))
            except InvalidReadingsRequest as e:
                abort(404, str(e))
        
        return merged_results.all()

api.add_resource(ReadingsAPI, '/readings/')
