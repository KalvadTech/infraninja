from pyinfra.context import host
from pyinfra.api.deploy import deploy
from pyinfra.operations import files, server
from pyinfra.facts.files import FindInFile
from pyinfra.facts.server import LinuxDistribution


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

    # SSH service names by distribution
    SSH_SERVICE_NAMES = {
        # Debian-based distros use 'ssh'
        "ubuntu": "ssh",
        "debian": "ssh",
        # Default to 'sshd' for everything else
        "default": "sshd",
    }

    def __init__(self, ssh_config=None):
        """
        Initialize SSHHardener with default or custom SSH configuration.

        Args:
            ssh_config (dict): Custom SSH configuration options.
        """

        self.ssh_config = ssh_config or self.DEFAULT_SSH_CONFIG.copy()

    def _get_ssh_service_name(self):
        """
        Determine the correct SSH service name based on the distribution.

        Returns:
            str: The SSH service name for the current distribution.
        """
        distro_info = host.get_fact(LinuxDistribution)
        if not distro_info:
            return self.SSH_SERVICE_NAMES["default"]

        distro_name = distro_info.get("name", "")
        if distro_name:
            distro_name = distro_name.lower()

        # Check for specific distributions
        for distro, service_name in self.SSH_SERVICE_NAMES.items():
            if distro in distro_name:
                return service_name

        # Default to 'sshd'
        return self.SSH_SERVICE_NAMES["default"]

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
            # Get correct SSH service name for this distribution
            ssh_service = self._get_ssh_service_name()

            # Restart SSH service to apply changes
            server.service(
                name="Restart SSH service",
                service=ssh_service,
                running=True,
                restarted=True,
                _ignore_errors=True,
            )
            host.noop("SSH configuration updated and service restarted.")
