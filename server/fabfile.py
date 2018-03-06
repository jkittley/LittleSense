#encoding:UTF-8

# =============================================================================
# This script is for deployment and should only be run usinf the fabric command
# 
# Calling "fab deploy:192.168.0.101" will deploy this code to a remote host at 
# IP Address 192.168.0.101.
# 
# =============================================================================
import socket

from os import getcwd, sep, remove
from fabric.api import cd, lcd, task
from fabric.operations import run, local, prompt, put, sudo
from fabric.network import needs_host
from fabric.state import env, output
from fabric.contrib import files
from fabric.contrib.project import rsync_project

from fabtools import user, group, require, deb
from fabtools.python import virtualenv, install_requirements, install

from config import settings

env.user = settings.DEPLOY_USER


@task
def deploy():
    sync_files()
    set_permissions()
    install_venv_requirements()
    restart_web_services()
    update_crontab()

@task
def init():
    # If there is an SSH Key then upload to remote
    if settings.PUBLIC_SSH_KEY != "":
        user.add_ssh_public_key(env.user, settings.PUBLIC_SSH_KEY)
    ## OS updates, config and user setup
    sudo('apt-get update')
    # sudo('apt-get upgrade')
    deb.install('nginx uwsgi python3-pip python3-dev python3-psycopg2')
    add_grp_to_user()
    install_python_35()
    setup_dot_local()
    ## Setup Project
    make_dirs()
    sync_files()
    set_permissions()
    create_virtualenv()
    install_venv_requirements()
    set_permissions()
    ## Web server
    setup_nginx()
    setup_gunicorn()
    restart_web_services()
    ## Database & Requirements
    install_influx()
    restart_db_services()
    # Initialise cron jobs to run background tasks
    update_crontab()


# ----------------------------------------------------------------------------------------
# Helper functions below
# ----------------------------------------------------------------------------------------

# Install Python 3.5
def install_python_35():
    sudo('apt install build-essential tk-dev libncurses5-dev libncursesw5-dev libreadline6-dev libdb5.3-dev libgdbm-dev libsqlite3-dev libssl-dev libbz2-dev libexpat1-dev liblzma-dev zlib1g-dev')
    with cd('/srv'):
        sudo('wget https://www.python.org/ftp/python/{0}/Python-{0}.tgz'.format(settings.PYVERSION))
        sudo('tar -xvf Python-{0}.tgz'.format(settings.PYVERSION))
        with cd('/srv/Python-{0}'.format(settings.PYVERSION)):
            sudo('./configure')
            sudo('make')
            sudo('make altinstall')

# Update the crontab
def update_crontab():
    script = '{}cronjobs.py'.format(settings.DIR_CODE)
    sudo('{venv}bin/python {script}'.format(venv=settings.DIR_VENV, script=script))

# Setup .local address for machine
def setup_dot_local():
    sudo('apt-get install avahi-daemon')

#  Users and Groups
def add_grp_to_user():
    if not group.exists(settings.DEPLOY_GRP):
        group.create(settings.DEPLOY_GRP)
    sudo('adduser {username} {group}'.format(username=env.user, group=settings.DEPLOY_GRP))
    # user.modify(env.user, group=DEPLOY_GRP)

# Make project folders
def make_dirs():
    for d in [settings.DIR_PROJ, settings.DIR_CODE, settings.DIR_LOGS, settings.DIR_ENVS, settings.DIR_SOCK]:
        exists = files.exists(d)
        print("File", d, "exists?", exists)
        if not exists:
            sudo('mkdir -p {}'.format(d))
            sudo('chown -R %s %s' % (env.user, d))
            sudo('chgrp -R %s %s' % (settings.DEPLOY_GRP, d))
    set_permissions()

# Set folder permissions
def set_permissions():
    # src
    sudo('chmod -R %s %s' % ("u=rwx,g=rwx,o=r", settings.DIR_CODE))
    # Logs
    sudo('chmod -R %s %s' % ("u=rwx,g=rw,o=r", settings.DIR_LOGS))
    # Envs
    sudo('chmod -R %s %s' % ("u=rwx,g=rwx,o=r", settings.DIR_ENVS))

# Sync project fioles to server
def sync_files():
    rsync_project(   
        remote_dir=settings.DIR_CODE,
        local_dir='./',
        exclude=("fabfile.py","*.pyc",".git","*.db", "*.log", "*.csv" '__pychache__', '*.md','*.DS_Store',"backups/"),
        extra_opts="--filter 'protect *.csv' --filter 'protect *.json' --filter 'protect *.db'",
        delete=True
    )

# Create a new environments
def create_virtualenv():
    if files.exists(settings.DIR_VENV):
        print("Virtual Environment already exists")
        return
    run('virtualenv -p python{0} {1}'.format(settings.PYVMM, settings.DIR_VENV))
    sudo('chgrp -R %s %s' % (settings.DEPLOY_GRP, settings.DIR_VENV))

# Install Python requirments
def install_venv_requirements():
    with virtualenv(settings.DIR_VENV):
        install_requirements('{0}requirements/remote.txt'.format(settings.DIR_CODE), use_sudo=False)

# Set environmental variables
def set_env_vars():
    with virtualenv(settings.DIR_VENV):
        run('export LOCAL=0')

# Install influx DB database and Grafana inspection tools.
def install_influx():
    # sudo('wget http://ftp.us.debian.org/debian/pool/main/i/influxdb/influxdb_1.1.1+dfsg1-4+b2_armhf.deb')
    # sudo('dpkg -i influxdb_1.1.1+dfsg1-4+b2_armhf.deb')

    sudo('wget http://ftp.us.debian.org/debian/pool/main/i/influxdb/influxdb_1.0.2+dfsg1-1+b2_armhf.deb')
    sudo('dpkg -i influxdb_1.0.2+dfsg1-1+b2_armhf.deb')

    # sudo('wget http://ftp.us.debian.org/debian/pool/main/g/grafana/grafana-data_2.6.0+dfsg-3_all.deb') 
    # sudo('apt-get install -f')
    # sudo('dpkg -i grafana-data_2.6.0+dfsg-3_all.deb')
    # sudo('apt-get install -f')

    # sudo('wget http://ftp.us.debian.org/debian/pool/main/g/grafana/grafana_2.6.0+dfsg-3_armhf.deb')
    # sudo('dpkg -i grafana_2.6.0+dfsg-3_armhf.deb')
    # sudo('apt-get install -f')

    # Enable and start grafana
    # sudo('systemctl enable grafana')
    # sudo('systemctl start grafana')

# Restart database services
def restart_db_services():
    sudo('systemctl restart influxdb')
    # sudo('systemctl restart grafana')

# Seup Nginx web service routing
def setup_nginx():
    deb.install('nginx')
    nginx_conf = '''
        # the upstream component nginx needs to connect to
        upstream django {{
            server unix:/tmp/{PROJECT_NAME}.sock;
        }}

        # configuration of the server
        server {{

            # Block all names not in list i.e. prevent HTTP_HOST errors
            if ($host !~* ^({SERVER_NAMES})$) {{
                return 444;
            }}

            listen      80;
            server_name {SERVER_NAMES};
            charset     utf-8;

            # max upload size
            client_max_body_size 75M;   # adjust to taste

            # Static files
            #location /static {{
            #    alias {PROJECT_PATH}static; 
            #}}

            location = /favicon.ico {{ access_log off; log_not_found off; }}

            # Finally, send all non-media requests to the server.
            location / {{
                include proxy_params;
                proxy_pass http://unix:{SOCKET_FILES_PATH}{PROJECT_NAME}.sock;
        }}
    }}'''.format(
        SERVER_NAMES="{0}|{1}.local|raspberrypi.local".format(env.hosts[0], settings.ROOT_NAME),
        PROJECT_NAME=settings.ROOT_NAME,
        PROJECT_PATH=settings.DIR_CODE,
        STATIC_FILES_PATH=settings.DIR_CODE,
        VIRTUALENV_PATH=settings.DIR_VENV,
        SOCKET_FILES_PATH=settings.DIR_SOCK
    )  
    sites_available = "/etc/nginx/sites-available/%s" % settings.ROOT_NAME
    sites_enabled = "/etc/nginx/sites-enabled/%s" % settings.ROOT_NAME
    files.append(sites_available, nginx_conf, use_sudo=True)
    # Link to sites enabled
    if not files.exists(sites_available):
        sudo('ln -s %s %s' % (sites_available, sites_enabled))
    # This removes the default configuration profile for Nginx
    if files.exists('/etc/nginx/sites-enabled/default'):
        sudo('rm -v /etc/nginx/sites-enabled/default')
    # Firewall settings
    # sudo("ufw allow 'Nginx Full'")

# Setup Gunicorn to serve web application
def setup_gunicorn():
    with virtualenv(settings.DIR_VENV):
        install('gunicorn', use_sudo=False)

    gunicorn_conf = '''[Unit]
        Description=gunicorn daemon
        After=network.target

        [Service]
        User={USER}
        Group={GRP}
        WorkingDirectory={PATH}
        ExecStart={VIRTUALENV_PATH}/bin/gunicorn --workers 3 --bind unix:{SOCKET_FILES_PATH}{PROJECT_NAME}.sock webapp:app

        [Install]
        WantedBy=multi-user.target
        '''.format(
            APP_NAME=settings.ROOT_NAME,
            PROJECT_NAME=settings.ROOT_NAME,
            PATH=settings.DIR_CODE,
            USER=env.user,
            GRP=settings.DEPLOY_GRP,
            VIRTUALENV_PATH=settings.DIR_VENV,
            SOCKET_FILES_PATH=settings.DIR_SOCK
        )
    
    gunicorn_service = "/etc/systemd/system/gunicorn.service"
    files.append(gunicorn_service, gunicorn_conf, use_sudo=True)
    sudo('systemctl start gunicorn')
    sudo('systemctl enable gunicorn')

# Restart webservices
@task
def restart_web_services():
    sudo('systemctl daemon-reload')
    sudo('systemctl restart nginx')
    sudo('systemctl restart gunicorn')



