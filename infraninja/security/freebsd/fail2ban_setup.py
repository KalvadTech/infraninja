from importlib.resources import files as resource_files

from pyinfra.api.deploy import deploy
from pyinfra.context import host
from pyinfra.facts.server import LinuxDistribution
from pyinfra.operations import files
from pyinfra.operations.freebsd import service


@deploy("Fail2ban Setup for FreeBSD")
def fail2ban_setup():
    """
    Set up Fail2ban on FreeBSD systems.

    This function handles:
    - Configuring Fail2ban with secure defaults
    - Setting up jails for SSH and other common services
    - Enabling and starting the Fail2ban service

    Note: This function assumes Fail2ban is already installed.
    """
    # Check if we're on FreeBSD
    distro = host.get_fact(LinuxDistribution)
    distro_name = (distro.get("name", "") or "").lower() if distro else ""

    if "freebsd" not in distro_name and distro_name:
        raise ValueError(
            f"This deployment is designed for FreeBSD systems only. Detected: {distro_name}"
        )

    # Create fail2ban configuration directory if it doesn't exist
    files.directory(
        name="Create fail2ban configuration directory",
        path="/usr/local/etc/fail2ban",
        present=True,
    )

    # Create jail.local file with custom settings using template
    template_path = resource_files("infraninja.security.templates.freebsd").joinpath(
        "jail.local.j2"
    )

    files.template(
        name="Create jail.local configuration from template",
        src=str(template_path),
        dest="/usr/local/etc/fail2ban/jail.local",
        mode="644",
        _sudo=True,
    )

    # Create fail2ban pf action file using template
    files.directory(
        name="Create fail2ban action.d directory",
        path="/usr/local/etc/fail2ban/action.d",
        present=True,
        _sudo=True,
    )

    template_path = resource_files("infraninja.security.templates.freebsd").joinpath(
        "pf_action.conf.j2"
    )

    files.template(
        name="Create pf action file from template",
        src=str(template_path),
        dest="/usr/local/etc/fail2ban/action.d/pf.conf",
        mode="644",
        _sudo=True,
    )

    # Note: The fail2ban table is already defined in the pf.conf template
    # No need to add it manually here

    # Enable fail2ban in rc.conf
    files.line(
        name="Enable fail2ban in rc.conf",
        path="/etc/rc.conf",
        line='fail2ban_enable="YES"',
        present=True,
    )

    # Start or restart fail2ban
    service.service(
        name="Restart fail2ban service",
        srvname="fail2ban",
        srvstate="restarted",
    )

    return True
