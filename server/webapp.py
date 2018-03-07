# =============================================================================
# This script is uses the Flask microframework to create a web interface for 
# inspection and configuration of the sensor network.
# =============================================================================

import json, os, arrow
from config import settings
from random import randint
from flask import render_template, Flask, request, abort, redirect, url_for, flash, send_from_directory
from unipath import Path

from utils import Device, Devices, DeviceRegister, Logger, BackupManager
from utils.influx import INFLUX_MESSUREMENTS

from flask_wtf import FlaskForm
from wtforms import StringField, HiddenField, BooleanField, SubmitField, DateTimeField, SelectField
from wtforms.validators import DataRequired, EqualTo

app = Flask(__name__)
log = Logger()

# ------------------------------------------------------------
# Setup
# ------------------------------------------------------------

# Settings
app.config.from_object(settings)
#  Setup the Web API manager
from commlink import WebAPI
webapi = WebAPI(app.config.get('IFDB'))
# Device managment
devices = Devices()

# ------------------------------------------------------------
# Pages
# ------------------------------------------------------------

@app.route("/<string:dash_selected>")
@app.route("/")
def home(dash_selected=None):
    dashes = [ (str(x.stem).capitalize().replace('_',' '), x.stem) for x in Path(settings.DASHBOARDS_PATH).listdir(pattern="*.json")]
    dash = None
    if dash_selected is None:
        dash_selected = dashes[0][1]
    p = Path(settings.DASHBOARDS_PATH).child(dash_selected+'.json')
    if p.exists():
        with open(p.absolute(), "r") as dashfile:
            print (dashfile)
            dash = json.load(dashfile)
            dash['title'] = str(p.stem).capitalize().replace('_',' ')
    return render_template('dashboard/index.html', dash=dash, dashes=dashes)


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
    devices.update()
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

        if purge_form.reged.data or purge_form.unreg.data:
            success = devices.purge(
                end=arrow.utcnow(),  
                unregistered=purge_form.unreg.data,
                registered=purge_form.reged.data
            )
            if success:
                flash('Purged devices data', 'success')
            else:
                flash('Failed to purge devices data', 'danger')

        if purge_form.logs.data:
            flash('Log Purge not implemented yet.', 'warning')

        if purge_form.registry.data:
            flash('Registry Purge not implemented yet.', 'warning')
    
    # Always clear verify
    purge_form.verify.data = ""
    return render_template('system/db.html', purge_form=purge_form)

# System Admin - Logs
@app.route("/sys/admin/logs", methods=['GET','POST'])
def sysadmin_logs():
    form = LogFilterForm()
    if form.validate_on_submit():
        logdata = log.list_records(
            cat=form.cat.data, 
            start=form.start.data,
            end=form.end.data,
            limit=form.limit.data
        )
    else:
        logdata = log.list_records()
    return render_template('system/logs.html', logdata=logdata, form=form)


# System Admin - Backup index
@app.route("/sys/backup/restore", methods=['GET','POST'])
def sysadmin_backup(del_file=None):
    backup_manager = BackupManager()
    backup_form = BackupForm()
    return render_template('system/backup.html', backup_form=backup_form, restore_form='NOT YET', backups_list=backup_manager.get_backups())

# System Admin - Backup index
@app.route("/sys/backup/delete/<string:filename>", methods=['GET','POST'])
def sysadmin_backup_delete(filename):
    delete_form = AreYouSureForm()
    if delete_form.validate_on_submit():
        backup_manager = BackupManager()
        success, msg = backup_manager.delete_backup(filename+".csv")
        if success:
            flash(msg, 'success')
            return redirect(url_for('sysadmin_backup'))
        else:
            flash(msg, 'danger')
    return render_template('system/backup.html', delete_form=delete_form, delete_file=filename)

# System Admin - Backup create
@app.route("/sys/backup/create", methods=['POST']) 
def sysadmin_backup_create(): 
    backup_form = BackupForm()
    # Create Backup
    if backup_form.validate_on_submit():
        # Create backup 
        backup_manager = BackupManager()
        download_file, message = backup_manager.create(
            backup_form.messurement.data, backup_form.start.data, backup_form.end.data)
        if download_file is not None:
            flash('Backup created', 'success')
        else:
            flash('Backup failed {}'.format(message), 'danger')
    return redirect(url_for('sysadmin_backup'))

# System Admin - Backup create
@app.route("/sys/backup/upload/<string:filename>/to/remote", methods=['GET']) 
def sysadmin_backup_upload(filename): 
    flash('Not implemented yet', 'warning')
    return redirect(url_for('sysadmin_backup'))


@app.route("/sys/backup/download/<string:filename>")
def sysadmin_backup_download(filename):
    return send_from_directory(directory=app.config.get('BACKUP')['folder'], filename=filename+".csv")
   
# @app.route("/sys/backup/to/remote/<string:filename>")
# def sysadmin_backup_remote(filename):
#     success, message = Backup().sftp(filename)
#     flash(message), 'success' if success else 'danger')
#     return redirect('sysadmin_backup')
    

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
@app.route("/api/readings/get")
@app.route("/api/readings/get/<string:device_id>")
def api_get(device_id=None):
    if device_id is None:
        device_fields = group_fields_by_device(request.args.getlist('device_fields'))
    else:
        device = Device(device_id)
        device_fields = {}
        device_fields[device_id] = [ x['id'] for x in device.fields() ]
 
    settings = {
        'device_fields': device_fields,
        'fillmode' : request.args.get('fill', 'none'),
        'interval' : request.args.get('interval',5),
        'start'    : request.args.get('start', None),
        'end'      : request.args.get('end', None),
        'limit'    : request.args.get('limit', None)
    }
    
    return_data = {}
    for device_id, fields_ids in settings['device_fields'].items():
        device   = Device(device_id)
        success, readings = device.get_readings(
            fields   = fields_ids,
            fill     = settings['fillmode'], 
            interval = settings['interval'], 
            start    = settings['start'], 
            end      = settings['end'], 
            limit    = settings['limit']
        )
        
        if success:
            return_data[device_id] = readings
        else:
            return_data[device_id] = None
    
    return json.dumps(return_data), 200 , {'ContentType':'application/json'} 


def group_fields_by_device(fields):
    devices = {}
    for field in fields:
        part = field.split('|')
        if part[0] not in devices:
            devices[part[0]] = []
        devices[part[0]].append(part[1])
    return devices


# ------------------------------------------------------------
# Forms
# ------------------------------------------------------------

class DeviceSettingsForm(FlaskForm):
    device_id = StringField('Device Id', validators=[DataRequired()]) 
    name = StringField('Name', validators=[DataRequired()])

class DBPurgeForm(FlaskForm):
    reged = BooleanField('Registered Devices')
    unreg = BooleanField('Unregistered Devices')
    logs  = BooleanField('Log Files')
    registry = BooleanField('Device Registry')
    confirm = HiddenField("conf", default="I CONFIRM")
    verify = StringField('Confirm by typing "I CONFIRM"', validators=[
        DataRequired(),
        EqualTo('confirm', message='You must enter "I CONFIRM"')
    ])

class AreYouSureForm(FlaskForm):
    confirm = BooleanField('Confirm', validators=[DataRequired()])

class LogFilterForm(FlaskForm):
    start = DateTimeField('Start', default=arrow.utcnow().shift(days=-1), validators=[])
    end = DateTimeField('End', default=arrow.utcnow(), validators=[])
    cat = SelectField('Category',choices=[('','All')] + log.get_categories(), default="all")
    limit = SelectField('Limit', choices=[
        ('50', 50),
        ('250', 250),
        ('500', 500),
        ('1000', 1000)
    ], default=500)

class BackupForm(FlaskForm):
    start = DateTimeField('Start Date', default=arrow.utcnow().shift(days=-1), validators=[])
    end = DateTimeField('End Date', default=arrow.utcnow(), validators=[])
    messurement = SelectField('Dataset',choices=INFLUX_MESSUREMENTS, default=INFLUX_MESSUREMENTS[0][0])
    

# ------------------------------------------------------------
# Other
# ------------------------------------------------------------

@app.before_request
def handle_missing_db_connection():
    if not devices.has_db_connection():
        flash('No connection to InfluxDB', 'danger')
        return "<h1>No Device Database Connection</h1>"

@app.context_processor
def context_basics():
    log.interaction(request.url)
    return dict(config=app.config, devices=devices.get_all())


if __name__ == '__main__':
    if settings.LOCAL:
        app.run()
    else:
        app.run(host='0.0.0.0')