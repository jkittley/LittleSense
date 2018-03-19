import arrow

class Readings():

    def __init__(self, readings, device_id, time_start, time_end, time_interval, fillmode, limit, fields_data):
        self.device_ids = [device_id]
        self.readings = sorted(list(readings.get_points()), key=lambda k: k['time']) 
        self.time_start = arrow.get(time_start)
        self.time_end = arrow.get(time_end)
        self.time_interval = time_interval
        self.fillmode = fillmode
        self.limit = limit
        self.fields_data = fields_data

    def all(self, **kwargs):
        # Format readings
        print('----', kwargs.get('format', 'list'))
        if kwargs.get('format', 'list') == 'by_time':
            formatted_readings = { r['time']:r for r in self.readings }
        else:
            formatted_readings = self.readings

        return { 
            "device_ids": self.device_ids,
            "start": self.time_start.format(),
            "end": self.time_end.format(),
            "count": len(self.readings),
            "fields": self.fields_data,
            "field_ids": list(self.fields_data.keys()),
            'readings': formatted_readings
        }

    def timestamps(self):
        return [ r['time'] for r in self.readings ]

    def merge_with(self, other):
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
        self.fields_data.update(other.fields_data)
    
        # Merge readings
        fields_default = { k:None for k, v in self.fields_data.items() }
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
