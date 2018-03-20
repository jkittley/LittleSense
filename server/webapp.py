# =============================================================================
# This script is uses the Flask microframework to create a web interface for 
# inspection and configuration of the sensor network.
# =============================================================================

import json
import arrow
from flask import render_template, Flask, request, abort, redirect, url_for, flash
from config import settings
from utils import Device, Devices, Logger, DashBoards, influx_connected
from utils.exceptions import UnknownDevice
from sysadmin import sysadmin
from api import api_bp as api_blueprint

app = Flask(__name__)
log = None

# -----------------------------------------------------------------------------
# Setup
# -----------------------------------------------------------------------------

# Settings
app.config.from_object(settings)

# -----------------------------------------------------------------------------
# Dashboard
# -----------------------------------------------------------------------------

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

# -----------------------------------------------------------------------------
# System Admin
# -----------------------------------------------------------------------------

app.register_blueprint(sysadmin, url_prefix='/system')

# -----------------------------------------------------------------------------
# Web API
# -----------------------------------------------------------------------------

app.register_blueprint(api_blueprint, url_prefix='/api')

# -----------------------------------------------------------------------------
# App intiailisation and contexts
# -----------------------------------------------------------------------------


@app.before_first_request
def init_devices():
    if influx_connected():
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
    if not influx_connected():
        return "<h1>No Device Database Connection</h1>"
    log = Logger()

@app.context_processor
def context_basics():
    log.interaction(request.url)
    return dict(config=app.config, devices=app.config.get('devices'))

# -----------------------------------------------------------------------------
# Main run i.e. what happens when you type python webapp.py
# -----------------------------------------------------------------------------

if __name__ == '__main__':
    if settings.LOCAL:
        app.run()
    else:
        app.run(host='0.0.0.0')