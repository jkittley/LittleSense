.. include:: global.rst

Periodic Tasks
==============
Some times you want to run periodic tasks. |project| for example, periodically cleans the log files and deletes old backups. If you want to add your own periodic task then open up cronjobs.py in the server folder and add a new static method in the Maintenance class.

.. code:: python

    @staticmethod
    def my_custom_task():
        # Your code here
        pass

Next we need to tell the server to add the task you have created to the cron background manager. Near the bottom of the Maintenance class there is a function called "update_crontab". At the bottom add the following code:

.. code:: python

    @staticmethod
    def update_crontab():

        ...

        task = 'my_custom_task'
        job = my_cron.new(command='{venv}bin/python {script} --task {task}'.format(
            venv=settings.DIR_VENV, 
            script=this_script, 
            task=task)
        )
        job.setall('0 0 * * *')
        my_cron.write()

The section ```job.setall('0 0 * * *')``` is where you tell the cron service when and how ofter you want your task to run. See the [Python Crontab}(https://github.com/doctormo/python-crontab)_ for more information on how to set these values.