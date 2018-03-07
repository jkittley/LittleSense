import os
from .secure import SecureSettings

class DefaultSetting(SecureSettings):
    # Enable debuging reports. This should only be true when running locally 
    # as it makes the system vunerable to attach.
    LOCAL = False
    DEBUG = LOCAL
    # The public facing name of the web interface
    SITE_NAME = "Sensor Store"
    # A system friendly version of the SITE_NAME. Only use aplphanumeric 
    # characters and underscores (no spaces). This is used for a nubmer of 
    # thing including the root folder name.
    ROOT_NAME = "noise"
    # Show link to settings page on dashbaord
    SHOW_SETTINGS_LINK = True
    # Details of the Influx database
    INFLUX = {
        "dbname": "device_readings",
        "host": "localhost",
        "port": 8086,
        "user": "root",
        "pass": "root"
    } 
    # Details of the TinyDB databases
    TINYDB = {
        "db_device_reg": "databases/devices.json"
    }
    # Saved Dashboard locations
    DASHBOARDS_PATH = "databases/dashboards"    

    # Settings for how best to purge (remove old) data from the databases. 
    # Unregistered sensor data is cleaned every 'unreg_interval' minutes and 
    # and anything older than 'unreg_keep_for' minutes is removed. The Log data
    # is purged at midnight everyday and records 'days_to_keep_log' days kept.
    PURGE = {
        "unreg_interval": 30, 
        "unreg_keep_for": 30, 
        "days_to_keep_log": 7 
    }
    # Automatic and Manual backup settings.
    # folder - relative path to backup folder location
    # frequency - 'weekly', 'daily', 'hourly' or 'never'
    BACKUP = {
        "folder" : "backups/",
        "frequency": 'weekly'
    }
    # BACKUP_SERVER - if is not None then these details are used to upload 
    # backups to another server for safe keeping. 
    BACKUP_SERVER = {
        "host": None,
        "user": None,
        "pass": None,
        "dir": None
    }
    # Path to a public SSH key for the machine doing the deployment. Set to
    # None if not required, but it will save a lot of usename and password
    # inputting.
    PUBLIC_SSH_KEY = '/Users/jacob/.ssh/id_rsa.pub'
    # Deployment (remote) server settings
    DEPLOY_USER  = 'pi'
    DEPLOY_GRP   = 'www-data'
    DIR_PROJ = "/srv/{0}/".format(ROOT_NAME)
    DIR_CODE = "{0}src/".format(DIR_PROJ)
    DIR_LOGS = "{0}logs/".format(DIR_PROJ)
    DIR_ENVS = "{0}envs/".format(DIR_PROJ)
    DIR_VENV = "{0}{1}/".format(DIR_ENVS, ROOT_NAME)
    DIR_SOCK = "{0}sockets/".format(DIR_PROJ)
    # Python Version
    PYVERSION = (3,5,3)
    PYVFULL = ".".join([str(x) for x in PYVERSION])
    PYVMM = ".".join([str(x) for x in PYVERSION[:2]])


class LocalSetting(DefaultSetting):
    LOCAL = True
    DEBUG = True

class RemotelSetting(DefaultSetting):
    LOCAL = False
    DEBUG = False
    BACKUP_SERVER =  {
            "host": '192.168.1.188',
            "user": 'pi',
            "pass": 'firebird30',
            "dir": 'srv/test_backup'
        }

# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# DO NOT EDIF BELOW THIS LINE
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------

settings = None
if 'LOCAL' in os.environ and os.environ['LOCAL'] == '1':
    settings = LocalSetting()
else:
    settings = RemotelSetting()