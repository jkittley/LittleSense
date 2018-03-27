import re

class FieldValue():
    """Field Value
    
    Attributes:
        field: (utils.Field): Field of messurement
        value (any): The value of the reading  
    """
    
    def __init__(self, field, value:any=None):
        """Create a field object

        Args:
            field: The name of the field
            value: The unit of messurement
        
        """
        self.field = field
        self._set_value(value)
     
    def _set_value(self, value:any):
        """Set the field value
        
        Args:
            value: The value of the messurement. Will be automatically parsed based on the specified data type.
        
        Raises:
            ValueError: If value does not match data type.

        """
        try:
            if self.field.dtype in self.field.DATA_TYPES_NUMERIC:
                self.value = None if value is None else float(value)
            if self.field.dtype in self.field.DATA_TYPES_ALPHANUMERIC:
                self.value = None if value is None else str(value).strip()
            if self.field.dtype in self.field.DATA_TYPES_BOOLEAN:
                self.value = None if value is None else bool(value)
        except Exception as e:
            raise ValueError('Cannot parse value {} - {}'.format(value, str(e)))

    def __str__(self):
        return "Reading for Device {}, Field {} = {}".format(self.device.id, self.field.id, self.value)

    def __repr__(self):
        return "Reading(Device, Field, value)"
