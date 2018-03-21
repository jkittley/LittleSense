from config import settings
from .influx import get_InfluxDB
import arrow, json, math
from functools import wraps

class Logger():
    """Custom logger with InfluxDB backend"""

    def __init__(self):
        self._ifdb = get_InfluxDB()

    def _get_ifdb(self):
        if self._ifdb is not None:
            return self._ifdb
        else:
            self._ifdb = get_InfluxDB()
            return self._ifdb

    def stats(self):
        """Get statistics about the current logs
        
        Returns:
            dict: Dictionary containing overall record 'count' and counts for each of the 'categories'

        """
        cat_counts = {}
        for cat, _ in self.get_categories():
            q = "SELECT count(message) FROM \"{}\" WHERE \"category\"='{}'".format(settings.INFLUX_LOGS, cat)
            try:
                c = next(self._get_ifdb().query(q).get_points())['count']
                cat_counts[cat] = c
            except StopIteration:
                pass
        return { "count": self.__len__(), "categories": cat_counts }

    def _add_to_log(self, cat, message, **data):
        logmsg = {
            "measurement": settings.INFLUX_LOGS,
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
        if self._get_ifdb():
            self._get_ifdb().write_points([logmsg])
        
    def get_categories(self):
        """Get list of categories and human readable names.
        
        Returns:
            list: List of tuples (category_id, fiendly name)

        """
        return [
            ('debug', 'Debug'),
            ('error', 'Error'),
            ('interaction', 'Interaction'),
            ('funcexec', 'Function Execution'),
            ('device', 'Sensor Device'),
            ('comms', 'Communication e.g. Radio'),
        ]

    def comms(self, msg:str, **kwargs):
        """Get list of categories and human readable names.
        
        Args:
            msg: Message to record

        Keyword Args:
            *: All keyworord arguments which are JSON serialisable are recorded as sublimental information.

        """
        self._add_to_log('comms', msg, **kwargs)

    def debug(self, msg:str, **kwargs):
        """See comms()"""
        self._add_to_log('debug', msg, **kwargs)

    def error(self, msg:str, **kwargs):
        """See comms()"""
        self._add_to_log('error', msg, **kwargs)

    def interaction(self, msg:str, **kwargs):
        """See comms()"""
        self._add_to_log('interaction', msg, **kwargs)

    def funcexec(self, msg:str, **kwargs):
        """See comms()"""
        self._add_to_log('funcexec', msg, **kwargs)

    def device(self, msg:str, **kwargs):
        """See comms()"""
        self._add_to_log('device', msg, **kwargs)

    def list_records(self, **kwargs):
        """List log records.
        
        Keyword Args:
            cat (str): Category
            limit (int): Limit results
            offset (int): Results offset
            start (str): UTC Datetime formatted as string - Results period start
            end (str): UTC Datetime formatted as string - Results period end
            orderby (str): Formatted as field and order e.g. time ASC or time DESC
        
        Returns:
            dict: Dictionary of results and pagination::

            {
                total: Total number of records,
                page_start: Page starts at result x,
                page_end: Page ends at result x,
                num_pages: Total number of pages,
                page_num: Current page number,
                results: List of results
            }

        """
        if self._get_ifdb() is None:
            return
        cat     = kwargs.get('cat', '')
        offset  = int(kwargs.get('offset', 0))
        limit   = int(kwargs.get('limit', 50))
        start   = kwargs.get('start', arrow.utcnow().shift(days=-1))
        end     = kwargs.get('end', arrow.utcnow())
        orderby = kwargs.get('orderby', None)

        # Build Query
        query = 'SELECT * FROM "{0}" WHERE time >= \'{1}\' and time <= \'{2}\''.format(settings.INFLUX_LOGS, start, end)
        if cat is not None and cat is not '':
            query += ' AND "category"=\'{0}\''.format(cat)
        
        total_records = len(list(self._get_ifdb().query(query).get_points()))
        
        if orderby is not None:
            query += ' ORDER BY '+orderby
        else:
            query += ' ORDER BY time DESC'

        if limit is not None:
            query += ' LIMIT {}'.format(limit)
        if offset > 0:
            query += ' OFFSET {}'.format(offset)
        
        results = list(self._get_ifdb().query(query).get_points())
        
        num_pages = math.ceil(total_records / max(1, limit))
        page_num  = math.ceil(min(num_pages, 1 + offset / limit))
    
        return dict(
                total=total_records,
                page_start=offset,
                page_end=offset+len(results),
                num_pages=num_pages,
                page_num=page_num,
                results=results
                )
    

    def purge(self, **kwargs):
        """Purge (delete) log records.
        
        Keyword Args:
            start (str): UTC Datetime formatted as string - Period start
            end (str): UTC Datetime formatted as string - Period end
            categories (list): List pf category ids to delete
                
        """

        default_start = arrow.utcnow().shift(years=-10)
        start = kwargs.get('start', default_start)
        default_end = arrow.utcnow()
        end = kwargs.get('end', default_end)
        cats = kwargs.get('categories', [])
        q = 'DELETE FROM "{messurement}" WHERE time > \'{start}\' AND time < \'{end}\''.format(
            messurement=settings.INFLUX_LOGS,
            start=start,
            end=end
        )
        # No categories specified e.g. cron task
        if len(cats) == 0:
            self.funcexec('Purged logs', start=start.format(), end=end.format())
            self._get_ifdb().query(q)
        # With categories
        else:
            for cat in cats:
                self._get_ifdb().query("{} AND \"category\"='{}'".format(q, cat))
           

    def __len__(self):
        try:
            counts = next(self._get_ifdb().query('SELECT count(*) FROM "{}"'.format(settings.INFLUX_LOGS)).get_points())
            return counts['count_message']
        except:
            return 0

    def __iter__(self):
        return (x for x in self.list_records())

    def __str__(self):
        return "Custom Logger"

    def __repr__(self):
        return "Logger()"