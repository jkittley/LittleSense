# =============================================================================
# This script is uses the Flask microframework to create a blueprint to extend 
# webapp.py with the admin panel functionality.
# =============================================================================

from random import randint
from flask import Blueprint, render_template, abort, redirect, url_for, flash, send_from_directory, request
from forms import SerialTXForm, DeviceSettingsForm, DBPurgeReadingsForm, DBPurgeDeviceReadingsForm, DBPurgeRegistryForm, DBPurgeLogsForm, LogFilterForm, BackupForm, ReadingForm, AreYouSureForm
import arrow
from unipath import Path
from flask import current_app as app
from utils import Device, Devices, Logger, BackupManager, DashBoards, SerialLogger
from config import settings
from flask import jsonify

sysadmin = Blueprint('sysadmin', __name__, template_folder='templates/system')

# -----------------------------------------------------------------------------
# Home i.e. Stats
# -----------------------------------------------------------------------------

# System Admin - Index
@sysadmin.route("/")
def index():
    stats = dict(log=app.config.get('log').stats(), device=app.config.get('devices').stats())
    recent_errors = app.config.get('log').list_records(
        cat = 'error',
        start = arrow.utcnow().shift(days=-7),
        limit = 10
    )
    return render_template('system/index.html', stats=stats, recent_errors=recent_errors)

# -----------------------------------------------------------------------------
# Device Management
# -----------------------------------------------------------------------------

# System Admin - Devices
@sysadmin.route("/devices")
def devices():
    app.config.get('devices').update()
    return render_template('system/devices.html')

# Register - preview device
@sysadmin.route("/devices/preview/<string:device_id>")
def device_register_preview(device_id):
    device = app.config.get('devices').get(device_id)
    form = ReadingForm(device_id=device.id)
    return render_template('system/preview.html', device=device, form=form)


# Register - configure device
@sysadmin.route("/devices/configure/and/register/<string:device_id>", methods=['GET','POST'])
def device_register_config(device_id):
    device = app.config.get('devices').get(device_id)
    form = DeviceSettingsForm(device_id=device.id, name=device.name) 
    # Save form data
    if form.is_submitted and form.validate_on_submit():
        # Save to database
        device.is_registered(True)
        device.set_name(name=form.name.data)
        # Show done page
        flash('Device registered', 'success')
        return redirect(url_for('.devices'))
    # Show config form page 
    return render_template('system/configure.html', device_id=device_id, device=device, form=form)

# System Admin - Unregister
@sysadmin.route("/devices/unregister/<string:device_id>", methods=['POST','GET'])
def device_unregister(device_id):
    unreg_form = AreYouSureForm()
    if unreg_form.validate_on_submit():
        device = app.config.get('devices').get(device_id)
        device.is_registered(False)
        flash('Device {} unregistered'.format(device_id), 'success')
        return redirect(url_for('.devices'))
    return render_template('system/unregister.html', device_id=device_id, unreg_form=unreg_form)

# -----------------------------------------------------------------------------
# Database Management
# -----------------------------------------------------------------------------

# System Admin - Database Functions
@sysadmin.route("/databases", methods=['GET','POST'])
def db():
    app.config['devices'].update()
    return render_template('system/db.html', form=None, log=app.config.get('log').stats())

# System Admin - Database Functions
@sysadmin.route("/databases/purge/by/device", methods=['GET','POST'])
def db_purge_by_device():
    app.config['devices'].update()
    form = DBPurgeDeviceReadingsForm() 
    form.devices.choices = [ (x.id, "{} ({}) - Registered: {}".format(x.name, x.id, x.is_registered())) for x in list(app.config['devices'].all) ]
    if form.validate_on_submit():
        if len(form.devices.data) > 0:
            try:
                app.config.get('devices').purge(
                    end=arrow.utcnow(),  
                    devices=form.devices.data
                )
                flash('Purged devices data', 'success')
            except ValueError as e:
                flash('Failed to purge devices data {}'.format(e), 'danger')
        else:
            flash('Nothing to purge. Please select at least one device', 'warning')
    form.verify.data = ""
    return render_template('system/db.html', form=form)

# System Admin - Database Functions
@sysadmin.route("/databases/purge/by/registration/status", methods=['GET','POST'])
def db_purge_by_reg_state():
    app.config['devices'].update()
    form = DBPurgeReadingsForm() 
    if form.validate_on_submit():
        if form.reged.data or form.unreg.data:
            try:
                app.config.get('devices').purge(
                    end=arrow.utcnow(),  
                    unregistered=form.unreg.data,
                    registered=form.reged.data,
                )
                flash('Purged data', 'success')
            except ValueError as e:
                flash('Failed to purge data {}'.format(e), 'danger')
        else:
            flash('Nothing selected to purge.', 'warning')
    form.verify.data = ""
    return render_template('system/db.html', form=form)

# System Admin - Database Functions
@sysadmin.route("/databases/purge/registry", methods=['GET','POST'])
def db_purge_registry():
    app.config['devices'].update()
    form = DBPurgeRegistryForm()
    if form.validate_on_submit():
        Path(settings.TINYDB['db_device_reg']).remove()
        flash('Purged registry', 'success')
    form.verify.data = ""
    return render_template('system/db.html', form=form)

# System Admin - Database Functions
@sysadmin.route("/databases/purge/logs", methods=['GET','POST'])
def db_purge_logs():
    app.config['devices'].update()
    form = DBPurgeLogsForm()
    form.cats.choices = app.config.get('log').get_categories()

    if form.validate_on_submit():
        if len(form.cats.data) > 0:
            app.config.get('log').purge(
                start=arrow.get(form.start.data),
                end=arrow.get(form.end.data),
                categories=form.cats.data
            )
            flash('Logs Purged', 'success')
        else:
            flash('Nothing to purge. Please select at least one category', 'warning')
    form.verify.data = ""
    return render_template('system/db.html', form=form, log=app.config.get('log').stats(), devices=None)


# -----------------------------------------------------------------------------
# Serial Viewer
# -----------------------------------------------------------------------------


# System Admin - Serial data viewer
@sysadmin.route("/serial", methods=['GET','POST'])
def serial():
    form = SerialTXForm()
    if request.method == 'POST':
        if form.validate():
            print('----->', form.message.data)
            return jsonify(dict(success=True))
        else:
            return "Form is invalid", 400
    if 'since' in request.values:
        slog = SerialLogger()
        start = arrow.get(request.values['since'])
        return jsonify(dict(messages=[ x for x in slog.list_lines(start=start) ]))
    else:
        return render_template('system/serial.html', form=form)


 

# -----------------------------------------------------------------------------
# Logs Viewer
# -----------------------------------------------------------------------------

# System Admin - Logs
@sysadmin.route("/logs", methods=['GET','POST'])
def logs():
    form = LogFilterForm()
    form.validate_on_submit()
    try:
        logdata = app.config.get('log').list_records(
            cat=form.cat.data, 
            start=form.start.data,
            end=form.end.data,
            limit=form.limit.data,
            offset=form.offset.data,
            orderby=form.orderby.data
        )
    except:
        logdata = []
    return render_template('system/logs.html', logdata=logdata, form=form)

# -----------------------------------------------------------------------------
# Backup Management
# -----------------------------------------------------------------------------

# System Admin - Backup index
@sysadmin.route("/backup/and/restore", methods=['GET','POST'])
def backup(del_file=None):
    backup_manager = BackupManager()
    backup_form = BackupForm()
    return render_template('system/backup.html', backup_form=backup_form, restore_form='NOT YET', backups_list=backup_manager.get_backups())

# System Admin - Backup index
@sysadmin.route("/backup/delete/<string:filename>", methods=['GET','POST'])
def backup_delete(filename):
    delete_form = AreYouSureForm()
    if delete_form.validate_on_submit():
        backup_manager = BackupManager()
        try:
            backup_manager.delete_backup(filename+".csv")
            flash("Backup deleted", 'success')
            return redirect(url_for('.backup'))
        except FileNotFoundError:
            flash("Failed to delete backup", 'danger')
    return render_template('system/backup.html', delete_form=delete_form, delete_file=filename)

# System Admin - Backup create
@sysadmin.route("/backup/create", methods=['POST']) 
def backup_create(): 
    backup_form = BackupForm()
    # Create Backup
    if backup_form.validate_on_submit():
        # Create backup 
        backup_manager = BackupManager()
        try:
            backup_manager.create(backup_form.messurement.data, backup_form.start.data, backup_form.end.data)
            flash('Backup created', 'success')
        except LookupError as e:
            flash('Backup failed {}'.format(e), 'danger')

    return redirect(url_for('.backup'))

# System Admin - Backup create
@sysadmin.route("/backup/upload/<string:filename>/to/remote", methods=['GET']) 
def backup_upload(filename): 
    flash('Not implemented yet', 'warning')
    return redirect(url_for('.backup'))

@sysadmin.route("/backup/download/<string:filename>")
def backup_download(filename):
    return send_from_directory(directory=app.config.get('BACKUP')['folder'], filename=filename+".csv")
   