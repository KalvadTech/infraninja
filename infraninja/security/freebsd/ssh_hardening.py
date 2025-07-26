from pyinfra.api.deploy import deploy
from pyinfra.context import host
from pyinfra.facts.files import FindInFile
from pyinfra.operations import files, server
from pyinfra.operations.freebsd import service


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

        self.ssh_config = (
            ssh_config if ssh_config is not None else self.DEFAULT_SSH_CONFIG.copy()
        )

    @deploy("SSH Hardening")
    def deploy(self):
        config_changed = False

        for option, value in self.ssh_config.items():
            # Find existing lines first
            matching_lines = host.get_fact(
                FindInFile,
                path="/etc/ssh/sshd_config",
                pattern=rf"^{option}.*$",
            )

            print(f"Checking for {option} in /etc/ssh/sshd_config: {matching_lines}")

            if matching_lines:
                # Option exists, check if value matches desired value
                existing_line = matching_lines[0]
                desired_line = f"{option} {value}"

                if existing_line.strip() != desired_line:
                    # Value doesn't match, replace it
                    change = files.replace(
                        name=f"Configure SSH: {option} (update value)",
                        path="/etc/ssh/sshd_config",
                        text=f"^{existing_line}$",
                        replace=desired_line,
                        _ignore_errors=True,
                    )
                    if change.changed:
                        config_changed = True
                        print(
                            f"Updated {option}: '{existing_line}' -> '{desired_line}'"
                        )
                else:
                    print(f"{option} already set to correct value: {value}")
            else:
                # Option doesn't exist, append it to the end of the file
                change = server.shell(
                    name=f"Configure SSH: {option} (append new)",
                    commands=[f"echo '{option} {value}' >> /etc/ssh/sshd_config"],
                )
                if change.changed:
                    config_changed = True
                    print(f"Added new option {option}: {value}")

        if config_changed:
            # Restart SSH service to apply changes
            service.service(
                name="Restart SSH service",
                srvname="sshd",
                srvstate="restarted",
                _ignore_errors=True,
            )
            host.noop("SSH configuration updated and service restarted.")
