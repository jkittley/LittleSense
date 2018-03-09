import os, arrow, csv
from config import settings
from unipath import Path
from .logger import Logger
from .influx import get_InfluxDB

class BackupManager():

    def __init__(self):
        self.log = Logger()
        pass

    def get_backups_folder(self):
        backup_folder = Path(settings.BACKUP['folder'])
        if not backup_folder.exists():
            backup_folder.mkdir()
        return backup_folder

    def delete_backup(self, filename):
        delpath = self.get_backups_folder().child(filename)
        if delpath.exists():
            delpath.remove()
            return True, "'{}' deleted".format(filename)
        return False, "Failed to delete: '{}'".format(filename)

    def get_backups(self):
        out = []
        for p in self.get_backups_folder().listdir(pattern="*.csv"):
            parts = p.stem.split('_')
            out.append({
                'filename': p.name,
                'stem': p.stem,
                'dataset': parts[0],
                'start': "{} {}".format(parts[1], parts[2].replace('-',':')),
                'end': "{} {}".format(parts[4], parts[5].replace('-',':'))
            })
            out = sorted(out, key=lambda k: k['start'], reverse=True) 
        return out
         

    def create(self, messurement, start=arrow.utcnow().shift(days=-1), end=arrow.utcnow()):
        # If datetime passed rather than arrow
        start = arrow.get(start)
        end = arrow.get(end)

        save_name = "{messurement}_{start}_to_{end}.csv".format(
            messurement=messurement,
            start=start.format('YYYY-MM-DD_HH-mm-ss'),
            end=end.format('YYYY-MM-DD_HH-mm-ss')
        )
        backup_folder = self.get_backups_folder()
        save_path = backup_folder.child(save_name)

        # Build Query
        q = 'SELECT * FROM "{messurement}" WHERE {timespan}'.format(
            timespan="time > '{start}' AND time <= '{end}'".format(start=start, end=end),
            messurement=messurement
        )
        # print (q)
        ifdb = get_InfluxDB()
        readings = ifdb.query(q).get_points()
        readings = list(readings)

        if len(readings) > 0:        
            with open(save_path.absolute(), 'w') as csvfile:
                csvwriter = csv.DictWriter(csvfile, 
                    fieldnames=list(readings[0].keys()),
                    delimiter=',',
                    quotechar='"', 
                    quoting=csv.QUOTE_MINIMAL
                )
                csvwriter.writeheader()
                for reading in readings:
                    csvwriter.writerow(dict(reading))

                self.log.funcexec('Backup created for {0}'.format(messurement), savedas=save_name)
                return save_name, None
        else:
            message = "No data to backup"
            self.log.funcexec('Backup failed for {0}'.format(messurement), error=message)
            return None, message


    
    # def sftp(self, filename):
    #     path = '{0}/{1}'.format(BACKUP_FOLDER, filename).replace('//','/')
    #     with pysftp.Connection(BACKUP_REMOTE_HOST, username=BACKUP_REMOTE_USER, password=BACKUP_REMOTE_PASS) as sftp:
    #         with sftp.cd(BACKUP_REMOTE_DIR):    # temporarily chdir to public
    #             sftp.put(path)  # upload file to public/ on remote
    #             return True, "Uploaded {0} to {1}{2}".format(path, BACKUP_REMOTE_HOST, BACKUP_REMOTE_DIR)
    #     return False, "Failed to upload"