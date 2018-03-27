import pytest
import os
from utils import Field
from utils.exceptions import IllformedField
from config import settings


def test_bad():
    bad = [
        ['number', 'light_level', 'lux', 52],
        ['float', 'light level', 'lux', 52],
        ['float', 'light_level', 'lu x', 52],
        ['float', 'light_level', 'lu x', None],
        ['float', 'light_level', 'lu x', "String"],
    ]
    for test_data in bad:
        with pytest.raises(IllformedField):
            Field(*test_data)
        
def test_good():
    good = [
        ['float', 'light_level', 'lux', 52], 
        ['int', 'height', 'cm', 12], 
        ['string', 'vegtable', 'cm', 'potato'], 
        ['str', 'vegtable', 'cm', 'potato'], 
        ['string', 'height', 'cm', 12], 
        ['str', 'height', 'cm', 12], 
        ['bool', 'height', 'cm', True], 
        ['boolean', 'height', 'cm', False], 
        ['bool', 'height', 'cm', 0], 
        ['boolean', 'height', 'cm', 1],
        ['bool', 'height', 'cm', '0'], 
        ['boolean', 'height', 'cm', '1'],
    ]
    for test_data in good:
        Field(*test_data)