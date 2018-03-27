import re
from .exceptions import IllformedField

class Field():
    """Field
    
    Attributes:
        DATA_TYPES_NUMERIC (list): List of acceptable numeric data types
        DATA_TYPES_ALPHANUMERIC (list): List of acceptable alphanumeric (string) data types
        DATA_TYPES_BOOLEAN (list): List of acceptable boolean data types
        DATA_TYPES: List of all acceptable data types
        id (str): Uniquie field identifier e.g. float_light_level_lux
        dtype (str): Type of data being added
        name (str): The name of the field
        unit (str): The unit of messurement
        
    """
    
    DATA_TYPES_NUMERIC = ["float", "int"]
    DATA_TYPES_ALPHANUMERIC = ["string", "str"]
    DATA_TYPES_BOOLEAN = ["bool", "boolean"]
    DATA_TYPES = DATA_TYPES_NUMERIC + DATA_TYPES_ALPHANUMERIC + DATA_TYPES_BOOLEAN
    
    def __init__(self, dtype:str, name:str, unit:str):
        """Create a field object

        Args:
            dtype: Type of data being added
            name: The name of the field
            unit: The unit of messurement

        """
        self._set_dtype(dtype)
        self._set_name(name)
        self._set_unit(unit)
        
    @classmethod
    def fromDict(cls, dictionary:dict):
        """Create Field() from dictionary.

        Args:
            dictionary: A dictionary containing keys: dtype, name and unit.

        """
        # Check the dictionary has required keys
        for key in ['dtype','name','unit']:
            if key not in dictionary:
                raise IllformedField('Key: {} missing'.format(key))

        # Create class 
        cls(dictionary['dtype'],dictionary['name'],dictionary['unit'])

    @classmethod
    def fromString(cls, field_string):
        """Create Field() from string e.g. float_light_level_lux.
        
        """
        field_string = field_string.lower().strip()
        parts = field_string.split('_')
  
        # Enough parts?
        if len(parts) < 3:
            raise IllformedField('Too few elements')

        # Are any of the elements blank
        for p in parts:
            if len(p) == 0:
                raise IllformedField('Blank Elements')
 
        return cls(parts[0], "_".join(parts[1:-1]), parts[-1])

               
    def _set_dtype(self, dtype:str):
        """Set the data type of the field.
        
        Args:
            dtype: Data type as string. Accepts "float", "string", "bool" and a number of other aliases, but always sets to one of the listed three.

        Raises:
            utils.exceptions.IllformedField: If unknown data type.
        
        """
        dtype = dtype.lower().strip()
        if dtype not in self.DATA_TYPES:
            raise IllformedField('Unknown Data type {}'.format(dtype))
        if dtype in self.DATA_TYPES_NUMERIC:
            self.dtype = self.DATA_TYPES_NUMERIC[0]
        if dtype in self.DATA_TYPES_ALPHANUMERIC:
            self.dtype = self.DATA_TYPES_ALPHANUMERIC[0]
        if dtype in self.DATA_TYPES_BOOLEAN:
            self.dtype = self.DATA_TYPES_BOOLEAN[0]
    

    def _set_name(self, name):
        """Set the field name
        
        Args:
            name: The name of the field.
        
        Raises:
            utils.exceptions.IllformedField: If name contains chars other than in A-Z, a-z, 0-9 and underscore (no spaces).

        """
        if not re.match("^[A-Za-z0-9_]*$", name):
            raise IllformedField('Invalid name "{}". Must only contain chars A to Z, 0 to 9 and underscores'.format(name))
        self.name = name.strip()
        self.friendly = name.capitalize().replace('_', ' ')
    
    def _set_unit(self, unit):
        """Set the unit of messurement.
        
        Args:
            name: The unit of messurement.
        
        Raises:
            utils.exceptions.IllformedField: If unit contains chars other than in A-Z, a-z, 0-9 and underscore (no spaces).

        """
        if not re.match("^[A-Za-z0-9_]*$", unit):
            raise IllformedField('Invalid unit "{}". Must only contain chars A to Z, 0 to 9 and underscores'.format(unit))
        self.unit = unit.strip()


    def as_dict(self):
        """Get representation as dictionary.
                
        Returns:
           dict: Dictionary of core field values i.e. dtype, name, unit, value, is_numeric, is_boolean and is_string.

        """
        return {
            'dtype': self.dtype,
            'name': self.name,
            'friendly': self.friendly,
            'unit': self.unit,
            'is_numeric': self.is_numeric,
            'is_boolean': self.is_boolean,
            'is_string': self.is_string
        }

    @property
    def id(self):
        return "{}_{}_{}".format(self.dtype, self.name, self.unit)

    @property
    def is_numeric(self):
        return self.dtype in self.DATA_TYPES_NUMERIC

    @property
    def is_string(self):
        return self.dtype in self.DATA_TYPES_ALPHANUMERIC

    @property
    def is_boolean(self):
        return self.dtype in self.DATA_TYPES_BOOLEAN

    def __str__(self):
        return "Field {}".format(self.id)

    def __repr__(self):
        return "Field({},{},{})".format(self.dtype, self.name, self.unit)
