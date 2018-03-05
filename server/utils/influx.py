from influxdb import InfluxDBClient, DataFrameClient
from influxdb.exceptions import InfluxDBClientError
from requests.exceptions import RequestException
from config import settings

INFLUX_READINGS = "reading"
INFLUX_LOGS = "logs"
INFLUX_MESSUREMENTS = [
    (INFLUX_READINGS, "Readings"),
    (INFLUX_LOGS, "Logs")
]


def get_InfluxDB():
    try:
        ifdb = InfluxDBClient(settings.INFLUX['host'], settings.INFLUX['port'], settings.INFLUX['user'], settings.INFLUX['pass'], settings.INFLUX['dbname'])
        ifdb.create_database(settings.INFLUX['dbname'])

        # Test connection
        _ = ifdb.query('SHOW FIELD KEYS FROM "reading"')
        return ifdb
    except RequestException as e:
        print(e)
        return None

def get_DataframeClient():
    return DataFrameClient(settings.INFLUX['host'], settings.INFLUX['port'], settings.INFLUX['user'], settings.INFLUX['pass'], settings.INFLUX['dbname'])
   