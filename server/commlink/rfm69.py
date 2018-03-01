# =============================================================================
# RFM 69 RADIO
# =============================================================================

from commlink import CommLink

class RFM69(CommLink):

    def rx(self, utc, device_id, data, **kwargs):
        self._save_reading(utc, device_id, data)

