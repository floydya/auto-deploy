from fabric import api
from .base import Service

__all__ = ('DockerService',)


class DockerService(Service):
    name = 'docker'
    type = 'container-manager'

    def __init__(self, *args, **kwargs):
        super(DockerService, self).__init__(*args, **kwargs)

    def install(self):
        api.sudo('apt-get install docker docker-compose')
