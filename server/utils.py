from collections import namedtuple
from tinydb import TinyDB, Query


class Devices():
    
    def __init__(self, app):
        self.app = app
        self.ifdb = app.config['IFDB']
        self._all = []
        self._registered = []
        self._unregistered = []
        if self.ifdb is not None:
            self.update()

        self.Device = namedtuple('Device', ['id', 'name', 'registered', 'last_upd', 'last_upd_keys'])
        
    def get(self, update=False):
        if update:
            self.update()
        return [ self.Device(**x) for x in self._all ]

    def registered(self, update=False):
        if update:
            self.update()
        return [ self.Device(**x) for x in self._registered ]

    def unregistered(self, update=False):
        if update:
            self.update()
        return [ self.Device(**x) for x in self._unregistered ]

    def as_dict(self, update=False):
        if update:
            self.update()
        return {
            "all": self._all,
            "registered": self._registered,
            "unregistered": self._unregistered
        }

    def field_names(self, **kwargs):
        # if self.ifdb == None:
        #     return []
        q = 'SHOW FIELD KEYS FROM "reading"'
        field_names = self.ifdb.query(q).get_points()
        # print(field_names)
        return [ dict(name=f['fieldKey'], type=f['fieldType']) for f in field_names ]
        

    def update(self):
        
        devices = self.ifdb.query('SHOW TAG VALUES FROM "reading" WITH KEY = "device_id"').get_points()
        last_upds = self.ifdb.query('SELECT * FROM "reading" GROUP BY * ORDER BY DESC LIMIT 1')
    
        db = TinyDB(self.app.config.get('DB_DEVICE_REGISTRATION'))
        
        all_devices = []
        
        for device in devices:
            device_id = device['value']

            last_upd = list(last_upds.get_points(tags={'device_id': device_id}))[0]
            last_upd_keys = []
            for k, v in last_upd.items():
                if v is not None:
                    last_upd_keys.append(k)

            try:
                registration_record = db.search(Query().device_id == device_id)[0]
                registered = True
                name = registration_record['name']
            except IndexError:
                registration_record = None
                registered = False
                name = "Unregistered"

            all_devices.append(dict( 
                id=device_id,
                name=name,
                last_upd=last_upd,
                last_upd_keys=last_upd_keys,
                registered=registered
            ))
            
        self._all=all_devices
        self._registered=list(filter(lambda x: x['registered'], all_devices))
        self._unregistered= list(filter(lambda x: not x['registered'], all_devices))
        
    def __str__(self):
        return "Devices"

    