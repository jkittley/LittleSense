

class IllformedFieldName(SyntaxError):
    """Thrown when a field name is not correctly formed"""
     

class UnknownFieldName(LookupError):
    """Thrown when a field name is not know to be assosiated with a device"""
    
class InvalidFieldDataType(LookupError):
    """Thrown when a field name contains an unkown data type"""

class InvalidUTCTimestamp(ValueError):
    """Thrown when the passed UTC string cannot be parsed"""
