import arrow

class Readings():
    """Datatype for returned readings from readings query
    
    Args:
        readings: List of readings
        device_id: Device ID
        time_start: Readings earliest date and time
        time_end: Readings latest date and time
        time_interval: Readings interval in seconds
        fillmode: Reading fill mode
        fields_data: List of dicts each represnting a field

    """
    
    def __init__(self, readings:list, device_id:str, time_start:str, time_end:str, time_interval:int, fillmode:str, query_fields:dict):
        self.device_ids = [device_id]
        self.readings = sorted(readings, key=lambda k: k['time']) 
        self.time_start = arrow.get(time_start)
        self.time_end = arrow.get(time_end)
        self.time_interval = time_interval
        self.fillmode = fillmode
        self.query_fields = query_fields

    def all(self, **kwargs):
        """Return all readings as a dictionary:
        
        Keyword Args:
            format (str): How the readings should be formatted. Options: list ot by_time

        Returns: Readings as a dictionary::
    
            { 
                "device_ids": (list) List of device ids which contributed to these readings,
                "start": (str) Readings earliest date and time,
                "end": (str) Readings latest date and time,
                "count": (int) Numbner of readings,
                "fields": [
                    see device.fields()
                ],
                "field_ids": (list) Field ids,
                'readings': Readings as either a list of dicts (list) or as a dict where key=time and val=dict(field->val)
            }
            
        """
        # Format readings
        if kwargs.get('format', 'list') == 'by_time':
            formatted_readings = { r['time']:r for r in self.readings }
        else:
            formatted_readings = self.readings

        return { 
            "device_ids": self.device_ids,
            "start": self.time_start.format(),
            "end": self.time_end.format(),
            "count": len(self.readings),
            "fields": { k:f.as_dict() for k, f in self.query_fields.items() },
            "field_ids": list(self.query_fields.keys()),
            'readings': formatted_readings
        }

    def timestamps(self):
        """Get list of timestamps in results
        
        Returns:
            list: List of string date time stamps
        """
        return [ r['time'] for r in self.readings ]

    def merge_with(self, other):
        """Merge another Readings object into this one.

        Args:
            other (Reading): Readings objects to consume
        """
        if self.time_start != other.time_start or self.time_end != other.time_end:
            raise ValueError('Cannot merge readings with differing timings')
        if self.time_interval != other.time_interval:
            raise ValueError('Cannot merge readings with differing intervals')
        if self.fillmode == other.fillmode == "null" and len(self.readings) != len(other.readings):
            raise IndexError('When fill modes are null, the number of readings should match. They do not')
       
        # Remove limit
        self.limit = None
        
        # Merge ids
        self.device_ids = list(set(self.device_ids + other.device_ids))

        # Merge field datas
        self.query_fields.update(other.query_fields)
    
        # Merge readings
        fields_default = { k:None for k, _ in self.query_fields.items() }
        print(fields_default)

        self_readings_by_time  = self.all(format="by_time")['readings']
        other_readings_by_time = other.all(format="by_time")['readings']
        self_times  = list(self_readings_by_time.keys())
        other_times = list(other_readings_by_time.keys())
        merged = {}
        
        for t in set(self_times + other_times):
            merged.setdefault(t, fields_default.copy())

            if t in self_times:
                merged[t].update(self_readings_by_time[t])
            if t in other_times:
                merged[t].update(other_readings_by_time[t]) 
                
        self.readings = [ reads for _, reads in merged.items() ]

    def __str__(self):
        return "Readings Result Object"

    def __repr__(self):
        return "Readings(readings, device_id, time_start, time_end, time_interval, fillmode, limit, query_fields)"