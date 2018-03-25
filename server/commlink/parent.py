# =============================================================================
# Parent class for all communication links.
# =============================================================================

import json
import arrow
from tinydb import TinyDB, Query
from utils import Device, Logger
from utils.exceptions import UnknownDevice
from uuid import getnode as get_mac_address

class InvaidPacketFormatter(Exception):
    pass

class CommLink:
    
    def __init__(self, packet_formatter_func, save_reading_func, **kwargs):
        self.COMMLINK_NAME = "NONE"
        self.MAC_ADDRESS = get_mac_address()
        self.verbose = bool(kwargs.get('verbose', False))
        self.debug = bool(kwargs.get('debug', False))
        self.save_reading = save_reading_func
        self.packet_formatter = self._validate_formatter(packet_formatter_func)
        self.log = Logger()

    # Functions which must be implememnted by children

    def initialise(self, **kwargs):
        raise NotImplementedError()

    def receive(self, **kwargs):
        raise NotImplementedError()

    def shutdown(self, **kwargs):
        raise NotImplementedError()

    # Helper functions for children 

    def _validate_formatter(self, func):
        self._report('Validating formatter function')
        # try:
        #     arrow_timestamp, string_name, dictionary = func(dict())
        # except ValueError as e:
        #     raise InvaidPacketFormatter('Failed to test. Does the function return three values?', e)
        # except Exception as e:
        #     raise InvaidPacketFormatter('Failed to test. Is the input a dictionary?', e)
        # if type(arrow_timestamp) != arrow.arrow.Arrow:
        #     raise InvaidPacketFormatter('UTC timestamp must be Arrow')
        # if type(string_name) != str:
        #     raise InvaidPacketFormatter('Device ID must be a string')
        # if type(dictionary) != dict:
        #     raise InvaidPacketFormatter('Formatted output must be a dictionary')
        return func

    def _report(self, *args, **kwargs):
        if self.verbose:
            as_string = ', '.join([ str(x) for x in args ])
            print(as_string, kwargs)
            if self.debug:
                self.log.debug(as_string, **kwargs)

    def _error(self, *args, **kwargs):
        as_string = ', '.join([ str(x) for x in args ])
        self.log.error(as_string, **kwargs)
        if self.verbose:
            print(as_string, kwargs)
  