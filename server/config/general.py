SITE_NAME = "Sensor Store"

INFLUX_DBNAME = "device_readings"
INFLUX_HOST = "localhost"
INFLUX_PORT = ""

DB_DEVICE_REGISTRATION = "databases/devices.json"

# How many minutes between purging the database of unregistered device data
AUTO_PURGE_UNREG_INTERVAL = 15
# How many minutes of unregistered device data to keep i.e. only purge is older than x mins
AUTO_PURGE_UNREG_KEEP = 30

BACKUP_FOLDER = "backups/"