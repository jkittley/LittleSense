from config import settings
from .influx import get_InfluxDB
import arrow, json
from functools import wraps


class Logger():

    def __init__(self):
        self._ifdb = get_InfluxDB()

    def get_ifdb(self):
        if self._ifdb is not None:
            return self._ifdb
        else:
            self._ifdb = get_InfluxDB()
            return self._ifdb

    def stats(self):
        try:
            counts = next(self.get_ifdb().query('SELECT count(*) FROM "logger"').get_points())
        except StopIteration:
            counts = { 'count_message': 'No logs' } 
        return { "count": counts['count_message'] }

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
        if self.get_ifdb():
            self.get_ifdb().write_points([logmsg])
        
    def get_categories(self):
        return [
            ('debug', 'Debug'),
            ('error', 'Error'),
            ('interaction', 'Interaction'),
            ('funcexec', 'Function Execution'),
            ('device', 'Sensor Device'),
        ]

    def debug(self, msg, **kwargs):
        self._add_to_log('debug', msg, **kwargs)

    def error(self, msg, **kwargs):
        self._add_to_log('error', msg, **kwargs)

    def interaction(self, msg, **kwargs):
        self._add_to_log('interaction', msg, **kwargs)

    def funcexec(self, msg, **kwargs):
        self._add_to_log('funcexec', msg, **kwargs)

    def device(self, msg, **kwargs):
        self._add_to_log('device', msg, **kwargs)

    def list_records(self, **kwargs):
        if self.get_ifdb() is None:
            return
        cat   = kwargs.get('cat', '')
        limit = kwargs.get('limit', 50)
        start = kwargs.get('start', arrow.utcnow().shift(days=-1))
        end   = kwargs.get('end', arrow.utcnow())

        query = 'SELECT * FROM "logger" WHERE time > \'{0}\' and time < \'{1}\''.format(start, end)

        if cat is not None and cat is not '':
            query += ' AND "category"=\'{0}\''.format(cat)
        
        query += ' ORDER BY DESC'

        if limit is not None:
            query += ' LIMIT {}'.format(limit)
        
        return list(self.get_ifdb().query(query).get_points())
    

    def purge(self, **kwargs):
        default_start = arrow.utcnow().shift(years=-10)
        start = kwargs.get('start', default_start)
        default_end = arrow.utcnow().shift(minutes=-settings.PURGE['auto_interval'])
        end = kwargs.get('end', default_end)
        q = 'DELETE FROM "logger" WHERE time > \'{start}\' AND time < \'{end}\''.format(
            start=start,
            end=end
        )
        self.funcexec('Purged logs', start=start.format(), end=end.format())
        self.get_ifdb().query(q)
        return True


    def __iter__(self):
        for x in self.list_records():
            yield x