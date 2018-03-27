from .field import Field


class Metric():
    """Data type for reading query metric."""

    AGGR_FUNC_NUMERIC = ['mean', 'mode', 'median', 'count', 'sum', 'max', 'min', 'first', 'last']
    AGGR_FUNC_STRING  = ['count', 'first', 'last']
    AGGR_FUNC_BOOLEAN = ['count', 'first', 'last']

    def __init__(self, device, field, aggregation_function:str=None):
        """Create a new metric data type.

        Args:
            device (utils.Device): Device
            field (utils.Field): Field
            aggregation_function (str): Aggregation function.

        """
        self.device = device
        self.field = field
        if aggregation_function is None and self.field.is_numeric:
            self.aggregation_function = self.AGGR_FUNC_NUMERIC[0]
        elif aggregation_function is None and self.field.is_boolean:
            self.aggregation_function = self.AGGR_FUNC_BOOLEAN[0]
        elif aggregation_function is None and self.field.is_string:
            self.aggregation_function = self.AGGR_FUNC_STRING[0]
        elif aggregation_function is None:
            raise ValueError('Unknown field data type')
        else:
            self.aggregation_function = aggregation_function

    @classmethod
    def fromString(cls, string:str):
        """Initialize from a string e.g. device_id,field_id,aggregation"""

        from .device import Device

        parts = string.split(',')
        if len(parts) != 3:
            raise ValueError('Metric must be comma seporated device_id,field_id,aggregation')

        device   = Device(parts[0].strip())
        field    = Field.fromString(parts[1])
        aggrfunc = parts[2].strip()
        return cls(device, field, aggrfunc)

    def __str__(self):
        return "Metric ({},{},{})".format(self.device.id, self.field.id, self.aggregation_function)
    
    def __repr__(self):
        return "Metric({},{},{})".format(self.device.id, self.field.id, self.aggregation_function)

    def __getitem__(self, key):
        return getattr(self, key)