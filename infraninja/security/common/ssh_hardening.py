from pyinfra.api.deploy import deploy
from pyinfra.context import host
from pyinfra.facts.files import FindInFile
from pyinfra.operations import files, server

#


class SSHHardener:
    """
    Class-based SSH hardening for infraninja and pyinfra deploys.

    Provides comprehensive SSH security configuration by modifying SSH daemon
    settings to enhance security. Automatically detects existing configuration
    and updates or adds new security settings as needed.

    .. code:: python

        from infraninja.security.common.ssh_hardening import SSHHardener
        SSHHardener().deploy()

        # With custom configuration
        custom_config = {
            "PermitRootLogin": "no",
            "PasswordAuthentication": "no",
            "X11Forwarding": "no",
            "MaxAuthTries": "3"
        }
        SSHHardener(ssh_config=custom_config).deploy()
    """

    DEFAULT_SSH_CONFIG = {
        "PermitRootLogin": "prohibit-password",
        "PasswordAuthentication": "no",
        "X11Forwarding": "no",
    }

    def __init__(self, ssh_config=None):
        """
        Initialize SSHHardener with default or custom SSH configuration.

        :param ssh_config: Custom SSH configuration options to apply
        :type ssh_config: dict, optional
        """

        self.ssh_config = ssh_config or self.DEFAULT_SSH_CONFIG.copy()

    @deploy("SSH Hardening")
    def deploy(self):
        """
        Deploy SSH hardening configuration.

        Applies SSH security settings by modifying /etc/ssh/sshd_config.
        Updates existing configuration lines or adds new ones as needed.
        Restarts the SSH service after configuration changes.

        :returns: None
        :rtype: None
        """
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
            server.service(
                name="Restart SSH service",
                service="sshd",
                running=True,
                restarted=True,
                _ignore_errors=True,
            )
            host.noop("SSH configuration updated and service restarted.")
