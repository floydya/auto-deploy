from fabric import api
import jinja2

from ..path import Path

__all__ = ('Service',)


class Service:
    name = ''
    blueprints_path = ''
    type = ''
    is_global_service = True

    def __init__(self, server):
        self.server = server
        self.alias = self.name

    @property
    def is_installed(self):
        with api.settings(warn_only=True):
            if api.sudo(f'service --status-all | grep "{self.alias}"'):
                return True
        return False

    def install(self):
        api.sudo(f'apt-get install {self.alias}')

    def configure(self):
        return

    def start(self):
        api.sudo(f'service {self.alias} start')

    def stop(self):
        api.sudo(f'service {self.alias} stop')

    def remove(self):
        api.sudo(f'apt-get remove {self.alias}')

    def purge(self):
        api.sudo(f'apt-get purge --auto-remove {self.alias}')

    def restart(self):
        api.sudo(f'service {self.alias} restart')

    def soft_restart(self):
        self.restart()

    def create(self):
        self.install()
        self.configure()
        self.start()

    @staticmethod
    def _render_config(file_path, **context):
        path = Path(file_path)
        return jinja2.Environment(
            loader=jinja2.FileSystemLoader(str(path.parents[0].absolute()))
        ).get_template(path.name).render(context)


