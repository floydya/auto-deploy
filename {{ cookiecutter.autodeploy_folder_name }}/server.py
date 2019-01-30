import io, os

from fabric import api, contrib, operations

from .path import Path

__all__ = ('FileSystem', 'Server')


class FileSystem:

    def path_prepared(self, path: Path) -> bool:
        if self.path_exists(path):
            to_remove = operations.prompt(
                f'{path} already exists. Remove it?',
                default='Y'
            )
            if to_remove.lower() == 'y' or not to_remove:
                api.sudo(f'rm -rf {path}')
            else:
                return False
        return True

    def create_directory(self, path: Path, username: str, permissions=770):
        if not self.path_prepared(path):
            return
        api.sudo(f'mkdir {path}')
        self.set_permissions(username, path, permissions)

    @staticmethod
    def path_exists(path: Path) -> bool:
        return contrib.files.exists(path)

    @staticmethod
    def set_permissions(username: str, path: Path, permissions: int = 777):
        api.sudo(f'chmod -R {permissions} {path}'.replace('\\', '/'))
        api.sudo(f'chown -R {username}:{username} {path}'.replace('\\', '/'))

    @staticmethod
    def copy(data: str, name: str, destination: Path):
        file = io.StringIO(str(data))
        file.name = name
        file.filename = name

        api.sudo(f'rm -rf {destination}/{name}')
        api.put(file, f'{destination}/{name}', use_sudo=True)


class Server(FileSystem):

    def __init__(self, services):
        self.services = services
        self.process_services()

    def process_services(self):
        self.services = [service(server=self) for service in self.services]
        self._services = {x.name: x for x in self.services}

        for service in self.services:
            setattr(self, service.type, service)

    @staticmethod
    def create_user(username: str):
        with api.settings(warn_only=True):
            result = api.sudo(f'id -u {username}')
            if result.return_code != 1:
                print(f'The user {username} already exists.')
            else:
                api.sudo(f'adduser --disabled-password {username}')

    @staticmethod
    def enable_service(name: str):
        api.sudo('systemctl daemon-reload')
        api.sudo(f'systemctl enable {name}.service')

        with api.settings(warn_only=True):
            api.sudo(f'systemctl restart {name}.service')

    def install_services(self):
        for service in self.services:
            service.install()

    def restart_services(self):
        with api.settings(warn_only=True):
            for service in self.services:
                service.restart()

    @staticmethod
    def preconfigure():
        api.sudo('locale-gen en_US')
        api.sudo('locale-gen en_US.UTF-8')
        api.sudo('update-locale')

        api.sudo('apt-get update')
        api.sudo('''
            apt-get install htop git \
                gettext libtiff5-dev libjpeg8-dev zlib1g-dev \
                libfreetype6-dev liblcms2-dev libwebp-dev libpq-dev \
                build-essential libssl-dev libffi-dev tcl
        ''')

    def install(self):
        self.preconfigure()
        self.install_services()
        self.restart_services()
