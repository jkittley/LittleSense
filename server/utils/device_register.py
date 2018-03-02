from tinydb import TinyDB, Query
from config.general import DB_DEVICE_REGISTRATION

class DeviceRegister():
    
    def __init__(self):
        self._db = TinyDB(DB_DEVICE_REGISTRATION)

    def get_record(self, device_id):
        try:
            return self._db.search(Query().device_id == device_id)[0]
        except IndexError:
            return None

    def add_as_unregistered(self, device_id):
        data = {
            'device_id': device_id, 
            'name': "Unregistered",
            "registered": False
        }
        self._db.upsert(data, Query().device_id == device_id)

    def register_device(self, device_id, name=None):
        data = {
            'device_id': device_id, 
            "registered": True
        }
        if name is not None:
            data['name'] = name
        self._db.upsert(data, Query().device_id == device_id)
        return True 

    def add_seen_fields(self, device_id, field_names):
        self._db.update({
            'device_id': device_id, 
            'fields': field_names
        })
    
    def get_seen_fields(self, device_id):
        record = self._db.get(Query().device_id == device_id)
        return record.fields