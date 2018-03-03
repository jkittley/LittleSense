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
from wtforms import StringField, HiddenField, BooleanField, SubmitField
from wtforms.validators import DataRequired, EqualTo

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

# Register - preview device
@app.route("/system/register/device/<string:device_id>")
def device_register_preview(device_id):
    return render_template('system/register.html', current="preview", device_id=device_id)

# Register - configure device
@app.route("/system/configure/device/<string:device_id>", methods=['GET','POST'])
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
        return redirect(url_for('sysadmin_devices'))
    # Show config form page 
    return render_template('system/register.html', current="configure", device_id=device_id, form=form)

# System Admin - Index
@app.route("/sys/admin")
def sysadmin_index():
    return render_template('system/index.html', stats=devices.stats())

# System Admin - Index
@app.route("/sys/devices")
def sysadmin_devices():
    return render_template('system/devices.html')

# System Admin - Database Functions
@app.route("/sys/admin/db", methods=['GET','POST'])
def sysadmin_db():
    purge_form = DBPurgeForm()
    if purge_form.validate_on_submit():
        # Purge
        success = devices.purge(datetime.utcnow(), None, 
            unregistered=purge_form.unreg.data,
            registered=purge_form.reged.data
        )
        if success:
            flash('Purged devices data', 'success')
        else:
            flash('Failed to purge devices data', 'danger')
    return render_template('system/db.html', purge_form=purge_form)

# System Admin - Logs
@app.route("/sys/admin/logs")
def sysadmin_logs():
    return render_template('system/logs.html')


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

class DBPurgeForm(FlaskForm):
    reged = BooleanField('Registered Devices')
    unreg = BooleanField('Unregistered Devices')
    confirm = HiddenField("conf", default="I CONFIRM")
    verify = StringField('Confirm by typing "I CONFIRM"', validators=[
        DataRequired(),
        EqualTo('confirm', message='You must enter "I CONFIRM"')
    ])




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