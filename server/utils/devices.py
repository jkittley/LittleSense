import json
from collections import namedtuple
from tinydb import TinyDB, Query
from config import settings
from .logger import Logger
from .readings import Readings
from .metric import Metric
from .influx import get_InfluxDB
from .device import Device
from .exceptions import InvalidUTCTimestamp, InvalidFieldDataType, IllformedField, UnknownDevice, InvalidReadingsRequest
from unipath import Path
import arrow

log = Logger()

class Devices():
    """Devices Collection (Iterator)"""

    def __init__(self):
        self.all = []
        self.registered = []
        self.unregistered = []
        self._ifdb = get_InfluxDB()
        self.update()
       
    def update(self):
        """Refreshed cache of known devices from database"""
        devices_in_readings = self._ifdb.query('SHOW TAG VALUES FROM "{}" WITH KEY = "device_id"'.format(settings.INFLUX_READINGS)).get_points()
        self.all = [ self.get(d['value'], True) for d in devices_in_readings ]
        self.registered = list(filter(lambda x: x.is_registered(), self.all))
        self.unregistered = list(filter(lambda x: not x.is_registered(), self.all))

    def get(self, device_id:str, create_if_unknown:bool=False):
        """Get (or create) a specific Device

        args:
            device_id: The unique ID of the device.

        keyword args:
            create_if_unknown: If the device_id is not known then create a new Device.

        returns:
            Device: If device_id is found returns a Device. If no mathcing device found and create_if_unknown is False then returns None. However if create_if_unknown is True then return the newly created Device()
        """
        for x in self.all:
            if x.id == str(device_id).strip():
                return x
        if create_if_unknown:
            return Device(device_id, True)
        return None

    def stats(self):
        """Generate device related statistics

        returns:
            dict: total_readings, last_update, last_update_humanized, list of registered_devices

        """
        if self._ifdb is None:
            return
        try:
            counts = next(self._ifdb.query('SELECT count(*) FROM "{}"'.format(settings.INFLUX_READINGS)).get_points())
        except StopIteration:
            counts = {}
        if 'time' in counts.keys():
            del counts['time']
        try:
            last_upd = next(self._ifdb.query('SELECT * FROM "{}" ORDER BY time DESC LIMIT 1'.format(settings.INFLUX_READINGS)).get_points())
            last_upd = arrow.get(last_upd['time'])
            humanize = last_upd.humanize()
        except StopIteration:
            last_upd = "Never"
            humanize = "Never"
        return {
            "total_readings": counts,
            "last_update": last_upd.format('YYYY-MM-DD HH:mm:ss ZZ'),
            "last_update_humanized": humanize,
            "registered_devices": len(self.registered)
        }

    def purge(self, **kwargs):
        """Purge (delete) databases of requested content
        
        keyword args:
            registered (bool): Purge registered devices.
            unregistered (bool): Purge unregistered devices.
            registry (bool): Purge known device registry.
            start (str): DateTime string from when to purge data.
            end (str): DateTime string until when to purge data. 
        
        raises:
            ValueError: If ill defined purge
        """

        registered   = kwargs.get('registered', False)
        unregistered = kwargs.get('unregistered', False)
        device_ids   = kwargs.get('devices', [])

        default_start = arrow.utcnow().shift(years=-10)
        start = kwargs.get('start', default_start)
        default_end = arrow.utcnow().shift(minutes=-settings.PURGE['unreg_interval'])
        end = kwargs.get('end', default_end)

        to_process = None
        if registered and unregistered:
            to_process = self.all
        elif registered:
            to_process = self.registered
        elif unregistered:
            to_process = self.unregistered
        else:
            to_process = self.all.copy()
            for device in to_process:
                if device.id not in device_ids:
                    to_process.remove(device)

        if to_process is not None:
            for device in to_process:
                q = 'DELETE FROM "{messurement}" WHERE time > \'{start}\' AND time < \'{end}\' AND "device_id"=\'{device_id}\''.format(
                    messurement=settings.INFLUX_READINGS,
                    device_id=device.id,
                    start=start,
                    end=end
                )
                log.funcexec('Purged', registered=registered, unregistered=unregistered, to_process=[ d.id for d in to_process])
                self._ifdb.query(q)
        else:
            raise ValueError('Nothing specified to process')

 
    def to_dict(self, devices:list):
        """Converts list of Devices to list of dictionaries

        Args:
            devices: List of Device() objects

        Returns:
            list: List of dictionaries, each representing a Device()
        """
        return [ d.as_dict() for d in devices ]

    def as_dict(self, update:bool=False) -> dict:
        """Get Devices collection represented as a dictionary

        Args:
            update: Update cache before returning.

        Returns:
            dict: Dictionary containing three lists. All devices (all), Registered devices (registered) and Unregistered devices (unregistered)
        
        """
        if update:
            self.update()
        return {
            "all": self.to_dict(self.all),
            "registered": self.to_dict(self.registered),
            "unregistered": self.to_dict(self.unregistered)
        }

    def __str__(self):
        return "Device List. Contains {} devices".format(len(self))

    def __repr__(self):
        return "Devices()"

    def __len__(self):
        return len(self.all)

    def __getitem__(self, index):
        return self.all[index]

    def __iter__(self):
        return (d for d in self.all)
   
