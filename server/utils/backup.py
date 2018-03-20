import os, arrow, csv
from arrow.arrow import Arrow
from typing import List, Dict
from config import settings
from unipath import Path
from .logger import Logger
from .influx import get_InfluxDB



class BackupManager():
    """This class manages all thing relating to backups."""

    def __init__(self):
        self.log = Logger()
        pass

    def get_backups_folder(self) -> Path:
        """Get the path to the local backup folder. Automatically creates folder if does not exist.

        Returns:
            path: List of Paths 
        """
        backup_folder = Path(settings.BACKUP['folder'])
        if not backup_folder.exists():
            backup_folder.mkdir()
        return backup_folder

    def delete_backup(self, filename: str):
        """Delete specified backup files.

        Args:
            filename: The name of the backup file to delete. This cannont be a path and must be in the backups folder.

        Raises:
            FileNotFoundError
        """
        delpath = self.get_backups_folder().child(filename)
        if delpath.exists():
            delpath.remove()
            return True
        raise FileNotFoundError("Failed to delete: '{}'".format(filename))

    def get_backups(self) -> List[Dict]:
        """List backup files which exist locally.

        Returns:
            List of dictionarys containing filename, stem, dataset, start and end.
        """
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
         

    def create(self, messurement:str, start:Arrow=arrow.utcnow().shift(days=-1), end:Arrow=arrow.utcnow()) -> str:
        """Create a new backup locally.

        Args:
            messurement: The messurement type i.e. 'readings' or 'logs'.
            start: Arrow Datetime start of backup period.
            end: Arrow Datetime end of backup period.
        
        Returns:
            Saved file name

        Raises:
            LookupError if no data to backup
        """
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
                return save_name
        else:
            message = "No data to backup"
            self.log.funcexec('Backup failed for {0}'.format(messurement), error=message)
            raise LookupError(message)

    def __str__(self):
        return "Backup Manager"

    def __repr__(self):
        return "BackupManager()"
    
