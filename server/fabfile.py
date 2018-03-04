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

from config import remote
from config import general
from config import secure

PUBLIC_SSH_KEY = '/Users/jacob/.ssh/id_rsa.pub'


@task
def deploy():
    sync_files()
    set_permissions()
    install_venv_requirements()
    restart_web_services()

@task
def init():

    if PUBLIC_SSH_KEY != "":
        user.add_ssh_public_key(env.user, PUBLIC_SSH_KEY)

    ## Basic
    # sudo('apt-get update')
    # sudo('apt-get upgrade')
    # deb.install('nginx uwsgi python3-pip python3-dev python3-psycopg2')
    # add_grp_to_user()
    # install_python_35()
    
    ## Setup Project
    # make_dirs()
    # sync_files()
    # set_permissions()
    # create_virtualenv()
    # install_venv_requirements()
    # set_permissions()

    ## Web server
    # setup_nginx()
    # setup_gunicorn()
    # restart_web_services()

    ## Database & Requirements
    # install_influx()
    # restart_db_services()

# ----------------------------------------------------------------------------------------
# Helper functions below
# ----------------------------------------------------------------------------------------

USER_GRP = 'www-data'

DIR_PROJ = "/srv/{0}/".format(remote.ROOT_NAME)
DIR_CODE = "{0}src/".format(DIR_PROJ)
DIR_LOGS = "{0}logs/".format(DIR_PROJ)
DIR_ENVS = "{0}envs/".format(DIR_PROJ)
DIR_VENV = "{0}{1}/".format(DIR_ENVS, remote.ROOT_NAME)
DIR_SOCK = "{0}sockets/".format(DIR_PROJ)

PYVERSION = (3,5,3)
PYVFULL = ".".join([str(x) for x in PYVERSION])
PYVMM = ".".join([str(x) for x in PYVERSION[:2]])


# OS

def install_python_35():
    sudo('apt install build-essential tk-dev libncurses5-dev libncursesw5-dev libreadline6-dev libdb5.3-dev libgdbm-dev libsqlite3-dev libssl-dev libbz2-dev libexpat1-dev liblzma-dev zlib1g-dev')
    with cd('/srv'):
        sudo('wget https://www.python.org/ftp/python/{0}/Python-{0}.tgz'.format(PYVERSION))
        sudo('tar -xvf Python-{0}.tgz'.format(PYVERSION))
        with cd('/srv/Python-{0}'.format(PYVERSION)):
            sudo('./configure')
            sudo('make')
            sudo('make altinstall')

#  Users and Groups

def add_grp_to_user():
    if not group.exists(USER_GRP):
        group.create(USER_GRP)
    sudo('adduser {username} {group}'.format(username=env.user, group=USER_GRP))
    # user.modify(env.user, group=USER_GRP)

# Files and folders

def make_dirs():
    for d in [DIR_PROJ, DIR_CODE, DIR_LOGS, DIR_ENVS, DIR_SOCK]:
        exists = files.exists(d)
        print("File", d, "exists?", exists)
        if not exists:
            sudo('mkdir -p {}'.format(d))
            sudo('chown -R %s %s' % (env.user, d))
            sudo('chgrp -R %s %s' % (USER_GRP, d))

    set_permissions()
    
def set_permissions():
    # src
    sudo('chmod -R %s %s' % ("u=rwx,g=rwx,o=r", DIR_CODE))
    # Logs
    sudo('chmod -R %s %s' % ("u=rwx,g=rw,o=r", DIR_LOGS))
    # Envs
    sudo('chmod -R %s %s' % ("u=rwx,g=rwx,o=r", DIR_ENVS))

def sync_files():
    rsync_project(   
        remote_dir=DIR_CODE,
        local_dir='./',
        exclude=("fabfile.py","*.pyc",".git","*.db", "*.log" '__pychache__', '*.md','*.DS_Store'),
        delete=True
    )

# Virtual environments

def create_virtualenv():
    if files.exists(DIR_VENV):
        print("Virtual Environment already exists")
        return
    run('virtualenv -p python{0} {1}'.format(PYVMM, DIR_VENV))
    sudo('chgrp -R %s %s' % (USER_GRP, DIR_VENV))

def install_venv_requirements():
    with virtualenv(DIR_VENV):
        install_requirements('{0}requirements/remote.txt'.format(DIR_CODE), use_sudo=False)

def set_env_vars():
    with virtualenv(DIR_VENV):
        run('export LOCAL=0')

# Databases

def install_influx():
    # sudo('wget http://ftp.us.debian.org/debian/pool/main/i/influxdb/influxdb_1.1.1+dfsg1-4+b2_armhf.deb')
    # sudo('dpkg -i influxdb_1.1.1+dfsg1-4+b2_armhf.deb')

    sudo('wget http://ftp.us.debian.org/debian/pool/main/i/influxdb/influxdb_1.0.2+dfsg1-1+b2_armhf.deb')
    sudo('dpkg -i influxdb_1.0.2+dfsg1-1+b2_armhf.deb')

    sudo('wget http://ftp.us.debian.org/debian/pool/main/g/grafana/grafana-data_2.6.0+dfsg-3_all.deb') 
    sudo('apt-get install -f')
    sudo('dpkg -i grafana-data_2.6.0+dfsg-3_all.deb')
    sudo('apt-get install -f')

    sudo('wget http://ftp.us.debian.org/debian/pool/main/g/grafana/grafana_2.6.0+dfsg-3_armhf.deb')
    sudo('dpkg -i grafana_2.6.0+dfsg-3_armhf.deb')
    sudo('apt-get install -f')

    

    # Enable and start grafana
    sudo('systemctl enable grafana')
    sudo('systemctl start grafana')

def restart_db_services():
    sudo('systemctl restart influxdb')
    sudo('systemctl restart grafana')

# Webserver

def setup_nginx():
    # deb.install('nginx')

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
        SERVER_NAMES=env.hosts[0],
        PROJECT_NAME=remote.ROOT_NAME,
        PROJECT_PATH=DIR_CODE,
        STATIC_FILES_PATH=DIR_CODE,
        VIRTUALENV_PATH=DIR_VENV,
        SOCKET_FILES_PATH=DIR_SOCK
    )

    print(nginx_conf)    
    sites_available = "/etc/nginx/sites-available/%s" % remote.ROOT_NAME
    sites_enabled = "/etc/nginx/sites-enabled/%s" % remote.ROOT_NAME
    files.append(sites_available, nginx_conf, use_sudo=True)
    
    if not files.exists(sites_available):
        sudo('ln -s %s %s' % (sites_available, sites_enabled))

    # This removes the default configuration profile for Nginx
    if files.exists('/etc/nginx/sites-enabled/default'):
        sudo('rm -v /etc/nginx/sites-enabled/default')

    # sudo("ufw allow 'Nginx Full'")


def setup_gunicorn():
    with virtualenv(DIR_VENV):
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
            APP_NAME=remote.ROOT_NAME,
            PROJECT_NAME=remote.ROOT_NAME,
            PATH=DIR_CODE,
            USER=env.user,
            GRP=USER_GRP,
            VIRTUALENV_PATH=DIR_VENV,
            SOCKET_FILES_PATH=DIR_SOCK
        )
    gunicorn_service = "/etc/systemd/system/gunicorn.service"
    files.append(gunicorn_service, gunicorn_conf, use_sudo=True)
    sudo('systemctl start gunicorn')
    sudo('systemctl enable gunicorn')


@task
def restart_web_services():
    sudo('systemctl daemon-reload')
    sudo('systemctl restart nginx')
    sudo('systemctl restart gunicorn')



