import os, arrow
from config.general import INFLUX_DBNAME, INFLUX_HOST, BACKUP_FOLDER
from config.secure import INFLUX_USER, INFLUX_PASS
from unipath import Path

READINGS = "reading"
LOGS = "logs"
BACKUP_MESSUREMENTS = [
    (READINGS, "Readings"),
    (LOGS, "Logs")
]

class Backup():

    def __init__(self):
        pass

    def get_messurement(self):
        return 

    def create(self, messurement, start=arrow.utcnow().shift(days=-1), end=arrow.utcnow()):
        # If datetime passed rather than arrow
        start = arrow.get(start)
        end = arrow.get(end)

        if not Path(BACKUP_FOLDER).exists():
            Path(BACKUP_FOLDER).mkdir()

        save_name = "{messurement}_{start}_to_{end}.csv".format(
            messurement=messurement,
            start=start.format('YYYY-MM-DD_HH-mm-ss'),
            end=end.format('YYYY-MM-DD_HH-mm-ss')
        )
        save_path = '{0}/{1}'.format(BACKUP_FOLDER, save_name).replace('//','/')

        command = "influx -username '{user}' -password '{pswd}' -database '{dbname}' -host '{host}' -execute \"SELECT * FROM \"{dbname}\".\"\".\"{messurement}\" WHERE time > '{start}' and time < '{end}'\" -format 'csv' > {save_path} ".format(
            user=INFLUX_USER,
            pswd=INFLUX_PASS,
            dbname=INFLUX_DBNAME,
            host=INFLUX_HOST,
            messurement=messurement,
            start=start,
            end=end,
            save_path=save_path
        )
        # print (command)
        message = os.system(command)
        # print (message)
        if message == 0:
            return save_name, None
        else:
            return None, message