# =============================================================================
# This script is uses the Flask microframework to create a web interface for 
# inspection and configuration of the sensor network.
# =============================================================================

import config
import json, os, arrow
import requests
from collections import namedtuple
from random import randint
from datetime import datetime
from flask import render_template, Flask, request, abort, redirect, url_for, flash
from influxdb import InfluxDBClient
from influxdb.exceptions import InfluxDBClientError
from tinydb import TinyDB, Query
from utils import Devices
from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.validators import DataRequired

app = Flask(__name__)

# ------------------------------------------------------------
# Setup
# ------------------------------------------------------------

app.config.from_object('config.general')
app.config.from_object('config.secure')
LOCAL = True if 'LOCAL' in os.environ and os.environ['LOCAL'] == '1' else False
if LOCAL:
    print('---> LOCAL MODE <----')
    app.config.from_object('config.local')
else:
    app.config.from_object('config.remote')

# Influx

try:
    app.config['IFDB'] = InfluxDBClient('localhost', 8086, 'root', 'root', app.config.get('INFLUX_DBNAME'))
    # Test connection
    _ = app.config.get('IFDB').query('SHOW FIELD KEYS FROM "reading"')
except requests.exceptions.RequestException as e:
    app.config['IFDB'] = None
    
#  Setup the Web API manager
from commlink import WebAPI
webapi = WebAPI(app.config.get('IFDB'))

devices = Devices(app)


# ------------------------------------------------------------
# Pages
# ------------------------------------------------------------

@app.route("/")
def home():
    return render_template('dashboard/index.html', field_names=devices.field_names())

# Register - pick device
@app.route("/device/register")
def device_register():
    stages, current = get_device_reg_stages()
    return render_template('device/register.html', stages=stages, current=current)

# Register - preview device
@app.route("/device/register/device/<string:device_id>", methods=['GET'])
def device_register_preview(device_id):
    stages, current = get_device_reg_stages("preview")
    return render_template('device/register.html', stages=stages, current=current, device_id=device_id)

# Register - configure device
@app.route("/device/configure/<string:device_id>", methods=['GET','POST'])
def device_register_config(device_id):
    db = TinyDB(app.config.get('DB_DEVICE_REGISTRATION'))

    # Does the device already have a record?
    try:
        record = db.search(Query().device_id == device_id)[0]
        form = DeviceSettingsForm(device_id=device_id, name=record['name']) 
    except IndexError:
        form = DeviceSettingsForm(device_id=device_id) 

    # Save form data
    if form.is_submitted and form.validate_on_submit():
        # Save to database
        db.upsert({'device_id': device_id, 'name': form.name.data}, Query().device_id == device_id)
        # Show done page
        flash('Device registered', 'success')
        return redirect(url_for('home'))

    # Show config form page 
    stages, current = get_device_reg_stages("config")
    return render_template('device/register.html', stages=stages, current=current, device_id=device_id, form=form)

# Register - Helper function
def get_device_reg_stages(stage_id="home"):
    stages = [
        dict(id="home", title="Unregistered Devices", link="device_register"),
        dict(id="preview", title="Preview", link="device_register_preview"),
        dict(id="config", title="Configuration", link="device_register_config"),
        dict(id="done", title="Complete", link=None)
    ]
    current = list(filter(lambda stage: stage['id'] == stage_id, stages))
    if len(current) > 0:
        return stages, current[0]
    else:
        abort(404)

# WebAPI - put
@app.route("/api/put", methods=['GET', 'POST'])
def api_put():
    return webapi.rx(request.values)['json_response']

# WebAPI - get
@app.route("/api/devices/get")
def api_get_devices():
    return json.dumps(devices.as_dict())

# WebAPI - get
@app.route("/api/readings/get/<string:device_id>")
def api_get(device_id):

    # Fill gabs in period none=dont fill, null=fill intervals with null readings
    fillmode = request.args.get('fill','none')

    # interval
    try:
        interval = int(request.args.get('interval',5))
        if interval < 1:
            raise ValueError()
    except ValueError:
        return json.dumps({ "error" : "Invalid interval. Must be in second (integer) and > 0" })

    # Fields
    fields, field_keys = "", []
    for fk in devices.field_names():
        fields += 'mean("{0}") AS "mean_{0}", '.format(fk['name'])
        field_keys.append(dict(name="mean_{0}".format(fk['name']), type=fk['type']))

    # Timespan
    s = arrow.utcnow().shift(hours=-1)
    e = arrow.utcnow()

    try:
        if request.args.get('start', None) is not None:
            s = arrow.get(request.args.get('start'))
        if request.args.get('end', None) is not None:
            e = arrow.get(request.args.get('end'))
    except arrow.parser.ParserError:
        return json.dumps({ "error" : "Invalid start or end timestamp. Format example: 2018-03-08T15:29:00.000Z" })

    # Limit
    MAX_RESULTS = 5000
    MIN_RESULTS = 1
    try:
        limit = int(request.args.get('limit', MAX_RESULTS))
    except ValueError:
        return json.dumps({ "error" : "Invalid limit. Must be integer between {} and {}".format(MIN_RESULTS,MAX_RESULTS) })
    limit = max(min(limit, MAX_RESULTS), MIN_RESULTS)
   
    # Build Query
    q = 'SELECT {fields} FROM "reading" WHERE {timespan} AND "device_id"=\'{device_id}\' GROUP BY time({interval}) FILL({fill}) ORDER BY time DESC {limit}'.format(
        device_id=device_id, 
        interval="{}s".format(interval),
        timespan="time > '{start}' AND time <= '{end}'".format(start=s, end=e),
        fields=fields[:-2],
        fill=fillmode,
        limit="LIMIT {0}".format(limit)
    )
    print (q)
    readings = app.config.get('IFDB').query(q).get_points()
    readings = list(readings)
    
    timestamps = []
    used_keys = []
    for r in readings:
        timestamps.append(r['time'])
        for k, v in r.items():
            if v is not None:
                used_keys.append(k)
    
    
    return json.dumps({ 
        "field_keys": list(filter(lambda x: x['name'] in used_keys, field_keys)), 
        'readings': readings, 
        'timestamps': timestamps,
     })

# ------------------------------------------------------------
# Forms
# ------------------------------------------------------------

class DeviceSettingsForm(FlaskForm):
    device_id = StringField('Device Id', validators=[DataRequired()]) 
    name = StringField('Name', validators=[DataRequired()])



# ------------------------------------------------------------
# Other
# ------------------------------------------------------------

@app.context_processor
def context_basics():
    if app.config['IFDB'] == None:
        flash('No connection to InfluxDB', 'danger')
    return dict(config=app.config, devices=devices.get())


if __name__ == '__main__':
    if LOCAL:
        app.run()
    else:
        app.run(host='0.0.0.0')