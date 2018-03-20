from datetime import datetime
from flask import Blueprint, abort
from flask_restful import Api, Resource, url_for, reqparse
from flask import current_app as app
from utils.exceptions import InvalidReadingsRequest, UnknownDevice
from utils import Metric, Device

api_bp = Blueprint('api', __name__)
api = Api(api_bp)

class DevicesAPI(Resource):
    """Device Listing """

    def __init__(self, *args, **kwargs):
        self.devices = app.config.get('devices')

    def get(self):
        return self.devices.as_dict()

api.add_resource(DevicesAPI, '/devices')


class DeviceAPI(Resource):
    """Device API"""

    def __init__(self, *args, **kwargs):
        self.devices = app.config.get('devices')

    def get(self, device_id):
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
        """Query readings from one or more device"""
        
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
            abort(500, str(e))
      
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
                abort(500, str(e))
            except InvalidReadingsRequest as e:
                abort(500, str(e))
        
        return merged_results.all()

api.add_resource(ReadingsAPI, '/readings/')
