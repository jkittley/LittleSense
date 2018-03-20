class Metric():
    """Data type for reading query metric
    """

    def __init__(self, device_id:str, field_id:str, aggregation:str):
        self.device_id = device_id.strip().lower()
        self.field_id = field_id.strip().lower()
        self.aggregation = aggregation.strip().lower()

    @classmethod
    def fromString(cls, string:str):
        """Initialize from a string e.g. device_id,field_id,aggregation"""
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