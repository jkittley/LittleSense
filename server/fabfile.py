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
from termcolor import colored
from unipath import Path, DIRS

env.user = settings.DEPLOY_USER

@task
def deploy():
    sync_files()
    set_permissions()
    install_venv_requirements()
    restart_web_services()
    restart_bg_services()
    update_crontab()

@task
def init():
    # OS
    add_ssh_key()
    update_server()
    install_os_packages()
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
    ## Initialise cron jobs to run background tasks
    update_crontab()
    set_env_vars()
    setup_receiver()
    restart_bg_services()
    # Final server reboot for luck
    restart_web_services()

# Restart webservices
@task
def restart_web_services():
    print_title('Restarting Web Service - nginx and gunicorn')
    sudo('systemctl daemon-reload')
    sudo('systemctl restart nginx')
    sudo('systemctl restart gunicorn')

# Restart database services
@task
def restart_db_services():
    print_title('Restarting Influxdb')
    sudo('systemctl restart influxdb')
    # sudo('systemctl restart grafana')

# Restart background services
@task
def restart_bg_services():
    print_title('Restarting background services i.e. receiver script')
    sudo('systemctl daemon-reload')
    sudo('systemctl restart receiver')


# Restart background services
@task
def services_status():
    print_title('journalctl since yeterday')
    sudo('journalctl --since yesterday')
    print_title('Systemctl status nginx')
    sudo('systemctl status nginx')
    print_title('Systemctl status gunicorn')
    sudo('systemctl status gunicorn')
    print_title('Systemctl status receiver')
    sudo('systemctl status receiver')


# ----------------------------------------------------------------------------------------
# Helper functions below
# ----------------------------------------------------------------------------------------

def print_title(title):
    pad = "-" * (80 - len(title) - 4)
    print (colored("-- {} {}".format(title,pad), 'blue', 'on_yellow'))

def print_error(message):
    print (colored(message, 'red'))

def print_success(message):
    print (colored(message, 'green'))

# ----------------------------------------------------------------------------------------
# Sub Tasks - OS
# ----------------------------------------------------------------------------------------

@task
def add_ssh_key():
    print_title('Adding SSH Key to remote')
    if settings.PUBLIC_SSH_KEY != "":
        user.add_ssh_public_key(env.user, settings.PUBLIC_SSH_KEY)
        print_success("Done")
    else:
        print_error("No SSH KEY DEFINED IN SETTINGS")

def update_server():
    print_title('Updating server')
    sudo('apt-get update -y')
    sudo('apt-get upgrade -y')

def install_os_packages():
    print_title('Installing OS packages')
    deb.install('nginx uwsgi python3-pip python3-dev python3-psycopg2')

#  Users and Groups
def add_grp_to_user():
    print_title('Adding {} to {}'.format(settings.DEPLOY_GRP, env.user))
    if not group.exists(settings.DEPLOY_GRP):
        group.create(settings.DEPLOY_GRP)
    sudo('adduser {username} {group}'.format(username=env.user, group=settings.DEPLOY_GRP))
    # user.modify(env.user, group=DEPLOY_GRP)

# Install Python 3.5
def install_python_35():
    print_title('Installing Python 3.5')
    sudo('apt install -y build-essential tk-dev libncurses5-dev libncursesw5-dev libreadline6-dev libdb5.3-dev libgdbm-dev libsqlite3-dev libssl-dev libbz2-dev libexpat1-dev liblzma-dev zlib1g-dev')
    with cd('/srv'):
        pyvstr = ".".join([ str(x) for x in settings.PYVERSION ])
        sudo('wget https://www.python.org/ftp/python/{0}/Python-{0}.tgz'.format(pyvstr))
        sudo('tar -xvf Python-{0}.tgz'.format(pyvstr))
        with cd('/srv/Python-{0}'.format(pyvstr)):
            sudo('./configure')
            sudo('make')
            sudo('make altinstall')

# Setup .local address for machine
def setup_dot_local():
    print_title('Setting up .local address')
    sudo('apt-get install -y avahi-daemon')

# ----------------------------------------------------------------------------------------
# Sub Tasks - Project
# ----------------------------------------------------------------------------------------

# Make project folders
def make_dirs():
    print_title('Making folders')
    for d in [settings.DIR_PROJ, settings.DIR_CODE, settings.DIR_LOGS, settings.DIR_ENVS, settings.DIR_SOCK]:
        exists = files.exists(d)
        print("File", d, "exists?", exists)
        if not exists:
            sudo('mkdir -p {}'.format(d))
            sudo('chown -R %s %s' % (env.user, d))
            sudo('chgrp -R %s %s' % (settings.DEPLOY_GRP, d))
    set_permissions()

# Sync project fioles to server
def sync_files():
    print_title('Synchronising project code')
    rsync_project(   
        remote_dir=settings.DIR_CODE,
        local_dir='./',
        exclude=("fabfile.py","*.pyc",".git","*.db", "*.log", "*.csv" '__pychache__', '*.md','*.DS_Store',"backups/", "databases/tinydb/*.json"),
        extra_opts="--filter 'protect *.csv' --filter 'protect *.json' --filter 'protect *.db'",
        delete=True
    )

# Set folder permissions
def set_permissions():
    print_title('Setting folder and file permissions')
    sudo('chmod -R %s %s' % ("u=rwx,g=rwx,o=r", settings.DIR_CODE))
    sudo('chmod -R %s %s' % ("u=rwx,g=rw,o=r", settings.DIR_LOGS))
    sudo('chmod -R %s %s' % ("u=rwx,g=rwx,o=r", settings.DIR_ENVS))

# Create a new environments
def create_virtualenv():
    print_title('Creating Python {} virtual environment'.format(settings.PYVMM))
    sudo('pip3 install virtualenv')
    if files.exists(settings.DIR_VENV):
        print("Virtual Environment already exists")
        return
    run('virtualenv -p python{0} {1}'.format(settings.PYVMM, settings.DIR_VENV))
    sudo('chgrp -R %s %s' % (settings.DEPLOY_GRP, settings.DIR_VENV))

# Install Python requirments
def install_venv_requirements():
    print_title('Installing remote virtual env requirements')
    with virtualenv(settings.DIR_VENV):
        install_requirements('{0}requirements/remote.txt'.format(settings.DIR_CODE), use_sudo=False)
       

# ----------------------------------------------------------------------------------------
# Sub Tasks - Web Server
# ----------------------------------------------------------------------------------------

# Seup Nginx web service routing
def setup_nginx():
    print_title('Installing Nginx')
    deb.install('nginx')

    server_hosts = [env.hosts[0], "raspberrypi.local", "{}.local".format(settings.ROOT_NAME)]
    server_hosts.append( socket.gethostbyname(env.host) )
    server_hosts = set(server_hosts)

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
        SERVER_NAMES="|".join(server_hosts),
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
    if not files.exists(sites_enabled):
        sudo('ln -s %s %s' % (sites_available, sites_enabled))
    # This removes the default configuration profile for Nginx
    if files.exists('/etc/nginx/sites-enabled/default'):
        sudo('rm -v /etc/nginx/sites-enabled/default')
    # Firewall settings
    # sudo("ufw allow 'Nginx Full'")


# Setup Gunicorn to serve web application
def setup_gunicorn():
    print_title('Installing Gunicorn')
    with virtualenv(settings.DIR_VENV):
        install('gunicorn', use_sudo=False)

    gunicorn_conf = '''[Unit]
        Description=gunicorn daemon
        After=network.target

        [Service]
        User={USER}
        Group={GRP}
        WorkingDirectory={PATH}
        Restart=always
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
    sudo('systemctl enable gunicorn')
    sudo('systemctl start gunicorn')
   



# ----------------------------------------------------------------------------------------
# Sub Tasks - Database
# ----------------------------------------------------------------------------------------

# Install influx DB database and Grafana inspection tools.
def install_influx():
    print_title('Setting up InfluxDB')
    sudo('apt-get update -y')
    sudo('apt install apt-transport-https curl')
    sudo('curl -sL https://repos.influxdata.com/influxdb.key | sudo apt-key add -')
    sudo('echo "deb https://repos.influxdata.com/debian jessie stable" | sudo tee /etc/apt/sources.list.d/influxdb.list')
    sudo('apt-get update -y')
    sudo('apt-get install -y influxdb')


# ----------------------------------------------------------------------------------------
# Sub Tasks - Init Project
# ----------------------------------------------------------------------------------------

# Update the crontab
def update_crontab():
    print_title('Updating Crontab')
    script = '{}cronjobs.py'.format(settings.DIR_CODE)
    sudo('{venv}bin/python {script}'.format(venv=settings.DIR_VENV, script=script))

# Set environmental variables
def set_env_vars():
    print_title('Updating ENV variables')
    with virtualenv(settings.DIR_VENV):
        run('export LOCAL=0')

# Setup listing
def setup_receiver():
    print_title('Setting up receiver script - for radios')
    conf = '''[Unit]
        Description=Radio receiver daemon
        After=network.target

        [Service]
        User={USER}
        Group={GRP}
        Restart=always
        WorkingDirectory={PATH}
        ExecStart={VIRTUALENV_PATH}/bin/python receiver.py

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
    
    service = "/etc/systemd/system/receiver.service"
    files.append(service, conf, use_sudo=True)
    sudo('systemctl enable receiver')
    sudo('systemctl start receiver')




