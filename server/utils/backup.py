import os, arrow
from config import settings
from unipath import Path
from utils import Logger
# import pysftp

class BackupManager():

    def __init__(self):
        self.log = Logger()
        pass

    def delete_backup(self, filename):
        delpath = Path(settings.BACKUP['folder']).child(filename)
        if delpath.exists():
            delpath.remove()
            return True, "'{}' deleted".format(filename)
        return False, "Failed to delete: '{}'".format(filename)

    def get_backups(self):
        out = []
        for p in Path(settings.BACKUP['folder']).listdir(pattern="*.csv"):
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

        if not Path(settings.BACKUP['folder']).exists():
            Path(settings.BACKUP['folder']).mkdir()

        save_name = "{messurement}_{start}_to_{end}.csv".format(
            messurement=messurement,
            start=start.format('YYYY-MM-DD_HH-mm-ss'),
            end=end.format('YYYY-MM-DD_HH-mm-ss')
        )
        save_path = '{0}/{1}'.format(settings.BACKUP['folder'], save_name).replace('//','/')

        command = "influx -username '{user}' -password '{pswd}' -database '{dbname}' -host '{host}' -port {port} -execute \"SELECT * FROM \"{dbname}\".\"\".\"{messurement}\" WHERE time > '{start}' and time < '{end}'\" -format 'csv' > {save_path} ".format(
            user=settings.INFLUX['user'],
            pswd=settings.INFLUX['pass'],
            dbname=settings.INFLUX['dbname'],
            host=settings.INFLUX['host'],
            port=settings.INFLUX['port'],
            messurement=messurement,
            start=start,
            end=end,
            save_path=save_path
        )
        # print (command)
        message = os.system(command)
        # print (message)
        if message == 0:
            self.log.funcexec('Backup created for {0}'.format(messurement), savedas=save_name)
            return save_name, None
        else:
            self.log.funcexec('Backup failed for {0}'.format(messurement), error=message)
            return None, message

    # def sftp(self, filename):
    #     path = '{0}/{1}'.format(BACKUP_FOLDER, filename).replace('//','/')
    #     with pysftp.Connection(BACKUP_REMOTE_HOST, username=BACKUP_REMOTE_USER, password=BACKUP_REMOTE_PASS) as sftp:
    #         with sftp.cd(BACKUP_REMOTE_DIR):    # temporarily chdir to public
    #             sftp.put(path)  # upload file to public/ on remote
    #             return True, "Uploaded {0} to {1}{2}".format(path, BACKUP_REMOTE_HOST, BACKUP_REMOTE_DIR)
    #     return False, "Failed to upload"