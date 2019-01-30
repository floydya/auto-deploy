import os

from fabric.api import env, task
from .server import *
from .services import enabled

server = Server([service for service in enabled])
abs_dir_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

env.user = '{{ cookiecutter.root_user }}'
env.hosts = ['{{ cookiecutter.remote_ip }}']
env.key_filename = '{{ cookiecutter.private_ssh_key }}'


@task
def deploy():
    server.install()
