import os

class DefaultSetting():
    DEBUG = False
    SITE_NAME = "Sensor Store"
    
    INFLUX = {
        "dbname": "device_readings",
        "host": "localhost",
        "port": 8086,
        "user": "root",
        "pass": "root"
    } 
    TINYDB = {
        "db_device_reg": "databases/devices.json"
    }
    PURGE = {
        "unreg_interval": 30, # How many minutes between purging the database of unregistered device data
        "unreg_keep_for": 30, # How many minutes of unregistered device data to keep i.e. only purge is older than x mins
        "days_to_keep_log": 7 # Number of days to keep log
    }

    SECRET_KEY = "AVeryPrivateSecret"
    SECURITY_PASSWORD_SALT = "jdsfhbasdjkfhasldjkfhasiuy324783y58934"
    BACKUP = {
        "folder" : "backups/",
        "frequency": 'weekly',  # Backups frquency can be: 'weekly', 'daily', 'hourly' or 'never'
    }
    REMOTE_BACKUP = None
    PUBLIC_SSH_KEY = ""

    # Deply settings
    DEPLOY_USER  = 'pi'
    USER_GRP = 'www-data'
    ROOT_NAME = "noise"
    ROOT_PATH = "/srv/projects/noise"
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

    REMOTE_BACKUP = {
        "host": '192.168.1.188',
        "user": 'pi',
        "pass": 'firebird30',
        "dir": 'srv/test_backup'
    }

    PUBLIC_SSH_KEY = '/Users/jacob/.ssh/id_rsa.pub'


settings = RemotelSetting()
if 'LOCAL' in os.environ and os.environ['LOCAL'] == '1':
    settings = LocalSetting()