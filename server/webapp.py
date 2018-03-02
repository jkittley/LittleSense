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


# ------------------------------------------------------------
# Pages
# ------------------------------------------------------------

@app.route("/")
def home():
    return render_template('index.html', field_names=get_field_names())

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
        stages, current = get_device_reg_stages("done")
        return render_template('device/register.html', stages=stages, current=current, device_id=device_id)
    
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
@app.route("/api/get/<string:device_id>")
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
    for fk in get_field_names(device_id=device_id):
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
# Data Functions
# ------------------------------------------------------------

def get_devices():
    if app.config['IFDB'] == None:
        return None
    devices = app.config.get('IFDB').query('SHOW TAG VALUES FROM "reading" WITH KEY = "device_id"').get_points()
    last_upds = app.config.get('IFDB').query('SELECT * FROM "reading" GROUP BY * ORDER BY DESC LIMIT 1')
    
    db = TinyDB(app.config.get('DB_DEVICE_REGISTRATION'))
    
    all_devices = []
    Device = namedtuple('Device', ['id', 'name', 'registered', 'last_upd', 'last_upd_keys'])
    
    for device in devices:
        device_id = device['value']

        last_upd = list(last_upds.get_points(tags={'device_id': device_id}))[0]
        last_upd_keys = []
        for k, v in last_upd.items():
            if v is not None:
                last_upd_keys.append(k)

        try:
            registration_record = db.search(Query().device_id == device_id)[0]
            registered = True
            name = registration_record['name']
        except IndexError:
            registration_record = None
            registered = False
            name = "Unregistered"

        all_devices.append(Device(
            id=device_id,
            name=name,
            last_upd=last_upd,
            last_upd_keys=last_upd_keys,
            registered=registered,
        ))
    
    Devices = namedtuple('Devices', ['all', 'registered', 'unregistered'])
    return Devices(
        all=all_devices, 
        registered=list(filter(lambda x: x.registered, all_devices)),
        unregistered= list(filter(lambda x: not x.registered, all_devices))
    )


def get_field_names(**kwargs):
    if app.config['IFDB'] == None:
        return []
    q = 'SHOW FIELD KEYS FROM "reading"'
    field_names = app.config.get('IFDB').query(q).get_points()
    print(field_names)
    return [ dict(name=f['fieldKey'], type=f['fieldType']) for f in field_names ]
    
   

# ------------------------------------------------------------
# Other
# ------------------------------------------------------------

@app.context_processor
def context_basics():
    if app.config['IFDB'] == None:
        flash('No connection to InfluxDB', 'danger')
    return dict(config=app.config, devices=get_devices())


if __name__ == '__main__':
    if LOCAL:
        app.run()
    else:
        app.run(host='0.0.0.0')