# =============================================================================
# This script is designed to be run periodically using crontab. The purpose
# of this script is perform maintenance tasks e.g. auto delete old data
# =============================================================================

import os
from config import settings
from crontab import CronTab
import click, arrow
from utils import Logger

log = Logger()

class Maintenance():

    @staticmethod
    def task_purge_logs():
        log.funcexec('Purging log data')
        log.purge(log=True, end=arrow.utcnow().shift(days=-settings.PURGE['days_to_keep_log']))
       
    @staticmethod
    def task_purge_unregistered_devices_data():
        log.funcexec('Auto deleting unregistered devices data')
        from utils import Devices
        devices = Devices()
        devices.purge(unregistered=True, end=arrow.utcnow().shift(minutes=-settings.PURGE['unreg_keep_for']))

    @staticmethod
    def task_auto_backup():
        print('Automatically backing up data')
        log.funcexec('Automatically backing up data')
        from utils import BackupManager
        manager = BackupManager()
        manager.create(settings.INFLUX_READINGS, arrow.utcnow().shift(days=settings.BACKUP['days'], hours=settings.BACKUP['hours']))

    @staticmethod
    def update_crontab():
        print("Updating cronjobs")

        this_script = os.path.realpath(__file__)
        my_cron = CronTab(user=settings.DEPLOY_USER)  
        my_cron.remove_all()

        # Data backup  
        if settings.BACKUP['frequency'] != 'never':
            task = 'task_auto_backup'
            job = my_cron.new(command='{venv}bin/python {script} --task {task}'.format(venv=settings.DIR_VENV, script=this_script, task=task))
            if settings.BACKUP['frequency'] == 'weekly':
                job.setall('0 * * * 0')
            elif settings.BACKUP['frequency'] == 'daily':
                job.setall('0 0 * * *')
            elif settings.BACKUP['frequency'] == 'hourly':
                job.setall('0 * * * *')
            my_cron.write()

        # Purge Unregisted device data
        if settings.PURGE['unreg_interval'] is not None:
            task = 'task_purge_unregistered_devices_data'
            job = my_cron.new(command='{venv}bin/python {script} --task {task}'.format(venv=settings.DIR_VENV, script=this_script, task=task))
            job.minute.every(settings.PURGE['unreg_interval'])
            my_cron.write()

        # Purge logs
        if settings.PURGE['days_to_keep_log'] is not None:
            task = 'task_purge_logs'
            job = my_cron.new(command='{venv}bin/python {script} --task {task}'.format(venv=settings.DIR_VENV, script=this_script, task=task))
            job.setall('0 0 * * *')
            my_cron.write()

        # ===== Add custom tasks execution below this line ======= #




# ------------ Do not edit below this line ----------------
@click.command()
@click.option('--task', default='update_crontab', help='Task to run')
def main(task):
    log.funcexec('Crontab called for task: {}'.format(task))
    method_to_call = getattr(Maintenance, task)
    method_to_call()
    
if __name__ == "__main__":
    main(None)