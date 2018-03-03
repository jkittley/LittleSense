# =============================================================================
# This script is uses the Flask microframework to create a web interface for 
# inspection and configuration of the sensor network.
# =============================================================================

import config
import json, os, arrow
from collections import namedtuple
from random import randint
from flask import render_template, Flask, request, abort, redirect, url_for, flash

from utils import Device, Devices, DeviceRegister, Logger
from flask_wtf import FlaskForm
from wtforms import StringField, HiddenField, BooleanField, SubmitField, DateTimeField, SelectField
from wtforms.validators import DataRequired, EqualTo

app = Flask(__name__)
log = Logger()

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
    device = devices.get_device(device_id)
    form = DeviceSettingsForm(device_id=device_id, name=device.get_name()) 
    # Save form data
    if form.is_submitted and form.validate_on_submit():
        # Save to database
        device.register(name=form.name.data)
        # Show done page
        flash('Device registered', 'success')
        return redirect(url_for('sysadmin_devices'))
    # Show config form page 
    return render_template('system/register.html', current="configure", device_id=device_id, form=form)

# System Admin - Index
@app.route("/sys/admin")
def sysadmin_index():
    stats = dict(log=log.stats(), device=devices.stats())
    return render_template('system/index.html', stats=stats)

# System Admin - Index
@app.route("/sys/devices")
def sysadmin_devices():
    return render_template('system/devices.html')

# System Admin - Index
@app.route("/sys/devices/unregister/<string:device_id>", methods=['POST','GET'])
def sysadmin_unreg(device_id):
    unreg_form = AreYouSureForm()
    if unreg_form.validate_on_submit():
        flash('Device {} unregistered'.format(device_id), 'success')
        devices.set_unregistered(device_id)
        return redirect(url_for('sysadmin_devices'))
    return render_template('system/unregister.html', device_id=device_id, unreg_form=unreg_form)

# System Admin - Database Functions
@app.route("/sys/admin/db", methods=['GET','POST'])
def sysadmin_db():
    purge_form = DBPurgeForm()
    if purge_form.validate_on_submit():
        # Purge
        success = devices.purge(
            end=arrow.utcnow(),  
            unregistered=purge_form.unreg.data,
            registered=purge_form.reged.data
        )
        if success:
            flash('Purged devices data', 'success')
        else:
            flash('Failed to purge devices data', 'danger')
    return render_template('system/db.html', purge_form=purge_form)

# System Admin - Logs
@app.route("/sys/admin/logs", methods=['GET','POST'])
def sysadmin_logs():
    form = LogFilterForm()
    if form.validate_on_submit():
        print("VALID")
        logdata = log.list_records(
            cat=form.cat.data, 
            start=form.start.data,
            end=form.end.data,
            limit=form.limit.data
        )
    else:
        print("INVALID")
        print(form.errors)
        logdata = log.list_records()
    return render_template('system/logs.html', logdata=logdata, form=form)

# System Admin - Index
@app.route("/sys/backup/restore")
def sysadmin_backup():
    return render_template('system/backup.html')


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

class AreYouSureForm(FlaskForm):
    confirm = BooleanField('Confirm', validators=[DataRequired()])

class LogFilterForm(FlaskForm):
    start = DateTimeField('Start Date', default=arrow.utcnow().shift(days=-1), validators=[])
    end = DateTimeField('End Date', default=arrow.utcnow(), validators=[])
    cat = SelectField('Category',choices=[('','All')] + log.get_categories(), default="all")
    limit = SelectField('Category', choices=[
        ('50', 50),
        ('250', 250),
        ('500', 500),
        ('1000', 1000)
    ], default=500)


# ------------------------------------------------------------
# Other
# ------------------------------------------------------------

@app.context_processor
def context_basics():
    # if app.config['IFDB'] == None:
    #     flash('No connection to InfluxDB', 'danger')
    log.interaction(request.url)
    return dict(config=app.config, devices=devices.get_all())


if __name__ == '__main__':
    if LOCAL:
        app.run()
    else:
        app.run(host='0.0.0.0')