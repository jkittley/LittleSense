import pytest
from utils import Device
from utils.exceptions import UnknownDevice

def test_unknow_device():
    with pytest.raises(UnknownDevice):
        Device('unknown_device_id')

