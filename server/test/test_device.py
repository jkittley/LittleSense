import pytest
import os
from utils import Device
from utils.exceptions import UnknownDevice, IllformedFieldName
from config import settings

os.environ["TESTING"] = "1"
print(settings.INFLUX_READINGS)
print(settings.INFLUX_LOGS)

def test_bad_field_id_to_components():
    device = Device('test', True)
    bad = [
        'float_c', 
        '_varname_unit', 
        'varname', 
        'float-varname-unit',
        'void_varname_unit'
    ]
    for field_id in bad:
        with pytest.raises(IllformedFieldName):
            device._field_id_components(field_id)


def test_good_field_id_to_components():
    device = Device('test', True)
    good = [ 
        ('float_var_name_unit', 'float', 'var name', 'unit'),
        ('float_varname_unit', 'float', 'varname', 'unit'),
        ('int_varname_unit', 'int', 'varname', 'unit'),
        ('str_varname_unit', 'str', 'varname', 'unit'),
        ('string_varname_unit', 'string', 'varname', 'unit'),
        ('bool_varname_unit', 'bool', 'varname', 'unit'),
    ]
    for field_id, dtype, name, unit in good:
        d, n, u = device._field_id_components(field_id)
        assert d.lower() == dtype.lower()
        assert n.lower() == name.lower()
        assert u.lower() == unit.lower()