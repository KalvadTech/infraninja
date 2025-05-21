from pyinfra.context import host
from pyinfra.api.deploy import deploy
from pyinfra.operations import files, server
from pyinfra.facts.files import FindInFile


class SSHHardener:
    """
    Class-based SSH hardening for infraninja and pyinfra deploys.

    Usage:
        from infraninja.security.common.ssh_hardening import SSHHardener
        SSHHardener().deploy()
    """

    DEFAULT_SSH_CONFIG = {
        "PermitRootLogin": "prohibit-password",
        "PasswordAuthentication": "no",
        "X11Forwarding": "no",
    }

    def __init__(self, ssh_config=None):
        """
        Initialize SSHHardener with default or custom SSH configuration.

        Args:
            ssh_config (dict): Custom SSH configuration options.
        """

        self.ssh_config = ssh_config or self.DEFAULT_SSH_CONFIG.copy()

    @deploy("SSH Hardening")
    def deploy(self):
        config_changed = False

        for option, value in self.ssh_config.items():
            # Find existing lines first
            matching_lines = host.get_fact(
                FindInFile,
                path="/etc/ssh/sshd_config",
                pattern=rf"^#?\s*{option}\s+.*$",
            )

            if matching_lines:
                change = files.replace(
                    name=f"Configure SSH: {option}",
                    path="/etc/ssh/sshd_config",
                    text=f"^{matching_lines[0]}$",
                    replace=f"{option} {value}",
                    _ignore_errors=True,
                )
                if change.changed:
                    config_changed = True
            else:
                # Append if not found
                files.line(
                    path="/etc/ssh/sshd_config", line=f"{option} {value}", present=True
                )
                config_changed = True

        if config_changed:
            # Restart SSH service to apply changes
            server.service(
                name="Restart SSH service",
                service="sshd",
                running=True,
                restarted=True,
                _ignore_errors=True,
            )
            host.noop("SSH configuration updated and service restarted.")
