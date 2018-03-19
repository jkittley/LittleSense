class Metric():
    def __init__(self, device_id, field_id, aggregation):
        self.device_id = device_id.strip().lower()
        self.field_id = field_id.strip().lower()
        self.aggregation = aggregation.strip().lower()

    @classmethod
    def fromString(cls, string):
        "Initialize from a string"
        parts = string.split(',')
        if len(parts) != 3:
            raise ValueError('Metric must be comma seporated device_id,field_id,aggregation')
        return cls(*parts)

    def __str__(self):
        return "Metric ({},{},{})".format(self.device_id, self.field_id, self.aggregation)
    
    def __repr__(self):
        return "Metric({},{},{})".format(self.device_id, self.field_id, self.aggregation)

    def __getitem__(self, key):
        return getattr(self, key)