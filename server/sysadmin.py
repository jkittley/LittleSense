# =============================================================================
# This script is uses the Flask microframework to create a blueprint to extend 
# webapp.py with the admin panel functionality.
# =============================================================================

from flask import Blueprint, render_template, abort, redirect, url_for, flash, send_from_directory
from forms import DeviceSettingsForm, DBPurgeForm, AreYouSureForm, LogFilterForm, BackupForm
import arrow
from flask import current_app as app
from utils import Device, Devices, Logger, BackupManager, DashBoards

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
    return render_template('system/preview.html', device=device)


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
    purge_form = DBPurgeForm()
    if purge_form.validate_on_submit():
        # Purge

        if purge_form.reged.data or purge_form.unreg.data or purge_form.registry.data:
            success = app.config.get('devices').purge(
                end=arrow.utcnow(),  
                unregistered=purge_form.unreg.data,
                registered=purge_form.reged.data,
                registry=purge_form.registry.data
            )
            if success:
                flash('Purged devices data', 'success')
            else:
                flash('Failed to purge devices data', 'danger')

        if purge_form.logs.data:
            app.config.get('log').purge()
            flash('Logs Purged', 'success')

    
    # Always clear verify
    purge_form.verify.data = ""
    return render_template('system/db.html', purge_form=purge_form)

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
        success, msg = backup_manager.delete_backup(filename+".csv")
        if success:
            flash(msg, 'success')
            return redirect(url_for('.backup'))
        else:
            flash(msg, 'danger')
    return render_template('system/backup.html', delete_form=delete_form, delete_file=filename)

# System Admin - Backup create
@sysadmin.route("/backup/create", methods=['POST']) 
def backup_create(): 
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
    return redirect(url_for('.backup'))

# System Admin - Backup create
@sysadmin.route("/backup/upload/<string:filename>/to/remote", methods=['GET']) 
def backup_upload(filename): 
    flash('Not implemented yet', 'warning')
    return redirect(url_for('.backup'))

@sysadmin.route("/backup/download/<string:filename>")
def backup_download(filename):
    return send_from_directory(directory=app.config.get('BACKUP')['folder'], filename=filename+".csv")
   