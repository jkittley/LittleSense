from config.general import INFLUX_DBNAME
from influxdb import InfluxDBClient
from influxdb.exceptions import InfluxDBClientError
import arrow, json



class Logger():

    def __init__(self):
        try:
            self._ifdb = InfluxDBClient('localhost', 8086, 'root', 'root', INFLUX_DBNAME)
            self._ifdb.create_database(INFLUX_DBNAME)
        except:
            self._ifdb = None

    def stats(self):
        try:
            counts = next(self._ifdb.query('SELECT count(*) FROM "logger"').get_points())
        except StopIteration:
            counts = {} 
        return {
            "count": counts['count_message']
        }

    def _add_to_log(self, cat, message, **data):
        logmsg = {
            "measurement": "logger",
            "tags": {
                "category": cat
            },
            "time": arrow.utcnow().format(),
            "fields": {
                "message": str(message)
            }
        }
        if len(data) > 0:
            logmsg['fields']['extra'] = json.dumps(data)

        # Save Reading
        if self._ifdb:
            self._ifdb.write_points([logmsg])
        
    def get_categories(self):
        return [
            ('debug', 'Debug'),
            ('error', 'Error'),
            ('interaction', 'Interaction'),
            ('funcexec', 'Function Execution')
        ]

    def debug(self, msg, **kwargs):
        self._add_to_log('debug', msg, **kwargs)

    def error(self, msg, **kwargs):
        self._add_to_log('error', msg, **kwargs)

    def interaction(self, msg, **kwargs):
        self._add_to_log('interaction', msg, **kwargs)

    def funcexec(self, msg, **kwargs):
        self._add_to_log('funcexec', msg, **kwargs)

    def list_records(self, **kwargs):
        if self._ifdb is None:
            return
        cat   = kwargs.get('cat', None)
        limit = kwargs.get('limit', 5000)
        start = kwargs.get('start', arrow.utcnow().shift(years=-10))
        end   = kwargs.get('end', arrow.utcnow())

        print(kwargs)

        query = 'SELECT * FROM "logger" WHERE time > \'{0}\' and time < \'{1}\''.format(start, end)

        if cat is not None:
            query += ' AND "category"=\'{0}\''.format(cat)
        
        query += ' ORDER BY DESC'

        if limit is not None:
            query += ' LIMIT {}'.format(limit)
        
        return self._ifdb.query(query).get_points()
    
    def __iter__(self):
        for x in self.list_records():
            yield x