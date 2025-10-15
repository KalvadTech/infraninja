"""SSH hardening action"""

from typing import Any

from pyinfra import host
from pyinfra.facts.files import FindInFile
from pyinfra.facts.server import OsRelease
from pyinfra.operations import files, server

from infraninja.actions.base import Action


class SSHHardeningAction(Action):
    """
    Comprehensive SSH hardening across multiple operating systems.

    Provides SSH security configuration by modifying SSH daemon settings to
    enhance security. Automatically detects the operating system and applies
    appropriate service restart commands for Linux and FreeBSD systems.

    Example:
        .. code:: python

            from infraninja.actions.ssh_hardening import SSHHardeningAction

            # Use default configuration
            action = SSHHardeningAction()
            action.execute()

            # With custom configuration
            action = SSHHardeningAction(
                permit_root_login="no",
                password_authentication="no",
                x11_forwarding="no"
            )
            action.execute()
    """

    slug = "ssh-hardening"
    name = {
        "en": "SSH Hardening",
        "ar": "تعزيز SSH",
        "fr": "Durcissement SSH",
    }
    tags = ["security", "ssh", "hardening"]
    category = "security"
    color = "#E74C3C"
    logo = "fa-shield-alt"
    description = {
        "en": "Harden SSH configuration by applying security best practices across all supported operating systems",
        "ar": "تعزيز تكوين SSH من خلال تطبيق أفضل ممارسات الأمان عبر جميع أنظمة التشغيل المدعومة",
        "fr": "Renforcer la configuration SSH en appliquant les meilleures pratiques de sécurité sur tous les systèmes d'exploitation pris en charge",
    }
    os_available = [
        "ubuntu",
        "debian",
        "alpine",
        "freebsd",
        "rhel",
        "centos",
        "fedora",
        "arch",
    ]

    def __init__(
        self,
        permit_root_login: str = "prohibit-password",
        password_authentication: str = "no",  # noqa: S107
        x11_forwarding: str = "no",
    ):
        """
        Initialize SSH hardening action with SSH configuration parameters.

        Args:
            permit_root_login: PermitRootLogin setting (default: "prohibit-password")
            password_authentication: PasswordAuthentication setting (default: "no")
            x11_forwarding: X11Forwarding setting (default: "no")
        """
        super().__init__()

        # Build SSH configuration from parameters
        self.ssh_config = {
            "PermitRootLogin": permit_root_login,
            "PasswordAuthentication": password_authentication,
            "X11Forwarding": x11_forwarding,
        }

    def execute(self) -> Any:
        """
        Execute SSH hardening configuration.

        Applies SSH security settings by modifying /etc/ssh/sshd_config.
        Updates existing configuration lines or adds new ones as needed.
        Restarts the SSH service after configuration changes using the
        appropriate method for the detected operating system.

        Returns:
            Result of the deployment operation
        """
        config_changed = False

        for option, value in self.ssh_config.items():
            # Find existing lines first
            matching_lines = host.get_fact(
                FindInFile,
                path="/etc/ssh/sshd_config",
                pattern=rf"^{option}.*$",
            )

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
            else:
                # Option doesn't exist, append it to the end of the file
                change = server.shell(
                    name=f"Configure SSH: {option} (append new)",
                    commands=[f"echo '{option} {value}' >> /etc/ssh/sshd_config"],
                )
                if change.changed:
                    config_changed = True

        if config_changed:
            self._restart_ssh_service()
            host.noop("SSH configuration updated and service restarted.")

        return config_changed

    def _restart_ssh_service(self):
        """
        Restart SSH service based on the detected operating system.

        Uses FreeBSD-specific service restart for FreeBSD systems,
        and standard systemd/service commands for Linux systems.
        """
        os_id = host.get_fact(OsRelease).get("id")

        if os_id == "freebsd":
            # FreeBSD requires specific service command syntax
            from pyinfra.operations.freebsd import service as freebsd_service  # noqa: PLC0415

            freebsd_service.service(
                name="Restart SSH service (FreeBSD)",
                srvname="sshd",
                srvstate="restarted",
            )
        else:
            # Linux systems (Debian, Ubuntu, RHEL, CentOS, Alpine, Arch, etc.)
            server.service(
                name="Restart SSH service",
                service="sshd",
                running=True,
                restarted=True,
            )
