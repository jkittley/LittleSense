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
        "auto_interval": 15, # How many minutes between purging the database of unregistered device data
        "keep_unreg_for": 30 # How many minutes of unregistered device data to keep i.e. only purge is older than x mins
    }

    SECRET_KEY = "AVeryPrivateSecret"
    SECURITY_PASSWORD_SALT = "jdsfhbasdjkfhasldjkfhasiuy324783y58934"
    BACKUP = {
        "folder" : "backups/"
    }
    REMOTE_BACKUP = None


class LocalSetting(DefaultSetting):
    LOCAL = True
    DEBUG = True

class RemotelSetting(DefaultSetting):
    LOCAL = False
    DEBUG = False

    ROOT_NAME = "noise"
    ROOT_PATH = "/srv/projects/noise"

    REMOTE_BACKUP = {
        "host": '192.168.1.188',
        "user": 'pi',
        "pass": 'firebird30',
        "dir": 'srv/test_backup'
    }

settings = RemotelSetting()
if 'LOCAL' in os.environ and os.environ['LOCAL'] == '1':
    settings = LocalSetting()