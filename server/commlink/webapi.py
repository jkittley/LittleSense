# =============================================================================
# RFM 69 RADIO
# =============================================================================

from commlink import CommLink
from datetime import datetime

class WebAPI(CommLink):

    def rx(self, data):
        errors = []

        if 'utc' not in data:
            errors.append('utc missing')
        else:
            try:
                utc = datetime.strptime(data['utc'], "%c")
            except ValueError:
                errors.append('Invalid datetime format show be: {}'.format(datetime.utcnow().strftime('%c')))

        if 'device_id' not in data:
            errors.append('device_id missing')
        else:
            device_id = data['device_id'].lower().strip()
    
        field_data = {}
        field_count = 0
        for x in data:
            if x.startswith('r_'):
                try:
                    field_data[x.replace('r_','')] = float(data[x])
                    field_count += 1
                    continue
                except:
                    pass
                try:
                    field_data[x.replace('r_','')] = str(data[x])
                    field_count += 1
                    continue
                except:
                    pass

        if field_count == 0:
            errors.append('no field data')

        if len(errors) > 0:
            return self._build_response(success=False, errors=errors)
        else:
            print(device_id, utc, field_data)
            self._save_reading(utc, device_id, field_data)
            return self._build_response(success=True)
          
                
      


