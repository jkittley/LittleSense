# =============================================================================
# This script is uses the Flask microframework to create a web interface for 
# inspection and configuration of the sensor network.
# =============================================================================

import json, os
from random import randint

import arrow
from flask import render_template, Flask, request, abort, redirect, url_for, flash
from unipath import Path
from forms import DeviceSettingsForm, DBPurgeForm, AreYouSureForm, LogFilterForm, BackupForm

from config import settings
from utils import Device, Devices, Logger, DashBoards
from utils.influx import is_connected as influx_connected
from utils.exceptions import UnknownDevice
from sysadmin import sysadmin

app = Flask(__name__)
log = None

# ------------------------------------------------------------
# Setup
# ------------------------------------------------------------

# Settings
app.config.from_object(settings)

# ------------------------------------------------------------
# Dashboard
# ------------------------------------------------------------

@app.route("/<string:dash_selected>")
@app.route("/")
def home(dash_selected=None):
    dash = None
    dashes = app.config.get('dashes')
    if settings.DEBUG:
        dashes.update()
    if dash_selected is not None:
        dash = dashes.get(slug=dash_selected)
    elif len(dashes) > 0:
        dash = dashes[0]        
    return render_template('dashboard/index.html', dash=dash, dashes=dashes)

# ------------------------------------------------------------
# System Admin
# ------------------------------------------------------------

app.register_blueprint(sysadmin, url_prefix='/system')

# ------------------------------------------------------------
# Web API
# ------------------------------------------------------------

# WebAPI - readings get
@app.route("/api/readings/get", methods=['POST'])
def api_get(device_id=None):
    # A metric is a dict(device_id=,field_id,agrfunc=)
    errors = []
    metrics_str = request.values.get('metrics', None)
    device_id = request.values.get('device_id', None)

    if metrics_str is not None:
        metrics = metrics_string_to_dict(metrics_str)
    elif device_id is not None:
        metrics = get_device_metrics(device_id)
    else:
        return json.dumps({ 'error': 'you must specify either a device_id of a set of metrics' })
      
    joined_data = {} 
    joined_fields = {}
    count_field_readings = 0
    for device_id, fields_data in metrics.items():
        try:
            device = Device(device_id)
        except UnknownDevice:
            return json.dumps({ 'error': 'Unknown device' })

        success, device_results = device.get_readings(
            fields   = fields_data,
            fill     = request.values.get('fill', 'none'), 
            interval = request.values.get('interval', 5), 
            start    = request.values.get('start', None),
            end      = request.values.get('end', None),
            limit    = request.values.get('limit', None)
        )
        # HERE we need to merge all device data into on stack by time
        # request.values.get('format', None)
        if success:
            for time, field_readings in device_results['readings'].items():
                count_field_readings += len(field_readings.keys())
                joined_data.setdefault(time, {}).update(field_readings)
                joined_fields.update(device_results['fields'])
        else:
            log.error("get_readings failure", extra=device_results)
            errors.append(device_results)


    joined_data_as_list = joined_data.values()

    # Return a dict where the key is time and the value is a dict of field value pairs
    return json.dumps({
        "count_timestamps": len(joined_data_as_list),
        "count_field_readings": count_field_readings,
        "fields": joined_fields,
        "field_ids": list(joined_fields.keys()),
        "timestamps": list(joined_data.keys()),
        "readings": list(joined_data_as_list),
        "errors": errors
    }), 200 , {'ContentType':'application/json'} 


# Convert device_id|field_id|agrfunc to dict
def metrics_string_to_dict(metrics_str):
    by_devices = {}
    for metrics in json.loads(metrics_str):
        by_devices.setdefault(metrics['device_id'], []).append(
            dict(field_id=metrics['field_id'], 
                 agrfunc=metrics['agrfunc'], 
                 ref=metrics.get('ref', None))
        )
    return by_devices

def get_device_metrics(device_id):
    device = Device(device_id)
    by_devices = {}
    by_devices[device_id] = []
    for field_data in device.fields():
        by_devices[device_id].append(dict(
            field_id=field_data['id']
        ))
    return by_devices


# ------------------------------------------------------------
# Other
# ------------------------------------------------------------

@app.before_first_request
def init_devices():
    app.config['devices'] = Devices()

@app.before_first_request
def init_dashboards():
    app.config['dashes']  = DashBoards()

@app.before_first_request
def init_log():
    app.config['log'] = Logger()
    global log
    log = app.config['log']


@app.before_request
def handle_missing_db_connection():
    log = Logger()
    if not influx_connected():
        return "<h1>No Device Database Connection</h1>"

@app.context_processor
def context_basics():
    log.interaction(request.url)
    return dict(config=app.config, devices=app.config.get('devices'))


if __name__ == '__main__':
    if settings.LOCAL:
        app.run()
    else:
        app.run(host='0.0.0.0')