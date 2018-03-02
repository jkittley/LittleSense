# =============================================================================
# This script is uses the Flask microframework to create a web interface for 
# inspection and configuration of the sensor network.
# =============================================================================

import config
import json, os
from collections import namedtuple
from random import randint
from datetime import datetime
from flask import render_template, Flask, request, abort, redirect, url_for, flash

from utils import Device, Devices, DeviceRegister
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

    
#  Setup the Web API manager
from commlink import WebAPI
webapi = WebAPI(app.config.get('IFDB'))

devices = Devices()
dev_reg = DeviceRegister()

# ------------------------------------------------------------
# Pages
# ------------------------------------------------------------

@app.route("/")
def home():
    return render_template('dashboard/index.html', field_names=devices.field_names())

# Register - pick device
@app.route("/device/register")
def device_register():
    devices.update()
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
    # Does the device already have a record?
    try:
        record = dev_reg.get_record(device_id=device_id)
        form = DeviceSettingsForm(device_id=device_id, name=record['name']) 
    except IndexError:
        form = DeviceSettingsForm(device_id=device_id) 

    # Save form data
    if form.is_submitted and form.validate_on_submit():
        # Save to database
        dev_reg.register_device(device_id=device_id, name=form.name.data)
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

# ------------------------------------------------------------
# Web API
# ------------------------------------------------------------

# WebAPI - put
@app.route("/api/put", methods=['GET', 'POST'])
def api_put():
    return webapi.rx(request.values)['json_response']

# WebAPI - devices get
@app.route("/api/devices/get")
def api_get_devices():
    return json.dumps(devices.as_dict())

# WebAPI - readings get
@app.route("/api/readings/get/<string:device_id>")
def api_get(device_id):
    fillmode = request.args.get('fill', 'none')
    interval = request.args.get('interval',5)
    start    = request.args.get('start', None)
    end      = request.args.get('end', None)
    limit    = request.args.get('limit', None)
    device   = Device(device_id)
    success, readings = device.get_readings(fill=fillmode, interval=interval, start=start, end=end, limit=limit)
    if success:
        return json.dumps(readings), 200 , {'ContentType':'application/json'} 
    else:
        return readings['error'], 400

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
    # if app.config['IFDB'] == None:
    #     flash('No connection to InfluxDB', 'danger')
    return dict(config=app.config, devices=devices.get())


if __name__ == '__main__':
    if LOCAL:
        app.run()
    else:
        app.run(host='0.0.0.0')