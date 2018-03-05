# =============================================================================
# This script is designed to be run periodically using crontab. The purpose
# of this script is perform maintenance tasks e.g. auto delete old data
# =============================================================================

import os
from config import settings
from crontab import CronTab
from fabfile import DIR_VENV
import click



def task_cap_log_length():
    print("Capping log length")

def task_auto_delete_unregistered_devices_data():
    print("Auto deleting unregistered devices data")

def task_auto_backup():
    print('Automatically backing up data')

# 
# 
# 

def update_crontab():
    print("Updating cronjobs")
    
    # this_script = os.path.realpath(__file__)

    # my_cron = CronTab(user='pi')    
    # job = my_cron.new(command='{venv}python /home/jay/writeDate.py'.format(venv=DIR_VENV, script=this_script))
    # job.minute.every()


@click.command()
@click.option('--task', default=None, help='Task to run')
def main(task):
    print(task)
    method_to_call = getattr(task, 'update_crontab')
    print (method_to_call)


if __name__ == "__main__":
    main()