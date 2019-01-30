import time

from fabric import api, contrib
from .base import Service

__all__ = ('ProjectService',)


class ProjectService(Service):
    user = '{{ cookiecutter.root_user }}'
    name = '{{ cookiecutter.project_name }}'
    repository = '{{ cookiecutter.gitlab_repo_url }}'
    branch = '{{ cookiecutter.gitlab_branch }}'
    domain = '{{ cookiecutter.domain }}'
    is_global_service = False

    def __init__(self, *args, **kwargs):
        super(ProjectService, self).__init__(*args, **kwargs)

        self.ssh_path = f'/root/.ssh/{self.name}_rsa'
        self.project_path = f'/root/{self.name}'

    def generate_ssh_config(self):
        api.run('touch ~/.ssh/config')
        contrib.files.append(
            '~/.ssh/config',

            'Host gitlab.com\n'
            '   PubkeyAuthentication yes\n'
            f'   IdentityFile {self.ssh_path}\n'
            'IdentitiesOnly yes\n'
        )

    def clone(self):
        print('Installing ssh key for your repository.')
        time.sleep(2)
        if not self.server.path_exists(self.ssh_path):
            api.run(f'ssh-keygen -t rsa -b 4096 -f {self.ssh_path}')

        api.run(
            '''
            curl --request POST --header "PRIVATE-TOKEN: {{ cookiecutter.gitlab_your_private_token }}" \
                --header "Content-Type: application/json" \
                --data '{"title": "My deploy key", "key": "'$(cat {ssh_path}.pub)'", "can_push": "false"}' \
                "https://gitlab.example.com/api/v4/projects/5/deploy_keys/"
            '''.format(ssh_path=self.ssh_path)
        )
        self.generate_ssh_config()
        api.run(
            f'git clone -b {self.branch} {self.repository} {self.project_path}'
        )

    def copy_service_file(self):
        conf = self._render_config(f'blueprints/{self.name}.service')
        self.server.copy(
            conf,
            f'{self.name}.service',
            '/etc/systemd/system'
        )

    def create_project_directory(self):
        self.server.create_directory(self.project_path, self.user)

    def pull(self):
        api.sudo(f'git -C {self.project_path} pull origin {self.branch}')

    def restart(self):
        api.sudo(f'systemctl restart {self.name}.service')

    @staticmethod
    def update_firewall():
        api.run(f'ufw allow 80/tcp')
        api.run(f'ufw allow 443/tcp')

    def install(self):
        self.create_project_directory()
        self.clone()
        self.copy_service_file()
        api.sudo(f'systemctl enable {self.name}.service')
        self.update_firewall()

    def start(self):
        api.sudo(f'systemctl start {self.name}.service')

    def stop(self):
        api.sudo(f'systemctl stop {self.name}.service')

    def restart(self):
        api.sudo(f'systemctl restart {self.name}.service')
