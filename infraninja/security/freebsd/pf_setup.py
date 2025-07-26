from importlib.resources import files as resource_files

from pyinfra.api.deploy import deploy
from pyinfra.context import host
from pyinfra.facts.files import FindInFile
from pyinfra.facts.server import Command, LinuxDistribution
from pyinfra.operations import files, server
from pyinfra.operations.freebsd import service


@deploy("PF Firewall Setup for FreeBSD")
def pf_setup():
    """
    Set up PF firewall for FreeBSD systems.

    This function handles:
    - Creating a secure pf.conf configuration
    - Enabling and starting the PF service
    - Setting up logging for PF
    """
    # Check if we're on FreeBSD
    distro = host.get_fact(LinuxDistribution)
    distro_name = (distro.get("name", "") or "").lower() if distro else ""

    if "freebsd" not in distro_name and distro_name:
        raise ValueError(
            f"This deployment is designed for FreeBSD systems only. Detected: {distro_name}"
        )

    # Check if PF is available
    pf_exists = host.get_fact(Command, command="kldstat -q -m pf || echo not_loaded")
    if pf_exists == "not_loaded":
        # Load PF kernel module
        server.shell(
            name="Load PF kernel module",
            commands="kldload pf",
        )

    # Backup original pf.conf if it exists
    server.shell(
        name="Backup original pf.conf",
        commands=[
            "test -f /etc/pf.conf.bak || cp /etc/pf.conf /etc/pf.conf.bak 2>/dev/null || true"
        ],
        _sudo=True,
    )

    # Create basic PF rules file using template
    template_path = resource_files("infraninja.security.templates.freebsd").joinpath(
        "pf.conf.j2"
    )

    files.template(
        name="Create PF configuration file from template",
        src=str(template_path),
        dest="/etc/pf.conf",
        mode="644",
        _sudo=True,
    )

    # Check PF configuration syntax
    try:
        server.shell(
            name="Check PF configuration syntax",
            commands=["pfctl -nf /etc/pf.conf"],
            _sudo=True,
        )
    except Exception:
        # Restore backup if syntax check fails
        server.shell(
            name="Restore PF configuration backup due to syntax error",
            commands=["cp /etc/pf.conf.bak /etc/pf.conf"],
            _sudo=True,
        )
        raise Exception("PF configuration syntax check failed. Backup restored.")

    # Set up PF logging directory
    files.directory(
        name="Create PF log directory",
        path="/var/log/pf",
        present=True,
        _sudo=True,
    )

    # Set up newsyslog for PF logs (FreeBSD equivalent of logrotate)
    template_path = resource_files("infraninja.security.templates.freebsd").joinpath(
        "pf_newsyslog.conf.j2"
    )

    files.template(
        name="Create newsyslog configuration for PF",
        src=str(template_path),
        dest="/usr/local/etc/newsyslog.d/pf.conf",
        mode="644",
        _sudo=True,
    )

    # Add pf_enable to rc.conf if not already present
    pf_enabled = host.get_fact(
        FindInFile,
        path="/etc/rc.conf",
        pattern=r"^pf_enable=",
    )

    if not pf_enabled:
        files.line(
            name="Enable PF in rc.conf",
            path="/etc/rc.conf",
            line='pf_enable="YES"',
            present=True,
            _sudo=True,
        )

    # Add pflog_enable to rc.conf if not already present
    pflog_enabled = host.get_fact(
        FindInFile,
        path="/etc/rc.conf",
        pattern=r"^pflog_enable=",
    )

    if not pflog_enabled:
        files.line(
            name="Enable PF logging in rc.conf",
            path="/etc/rc.conf",
            line='pflog_enable="YES"',
            present=True,
            _sudo=True,
        )

    # Start or reload PF service
    service.service(
        name="Start PF service",
        srvname="pf",
        srvstate="started",
        _sudo=True,
    )

    service.service(
        name="Start PFLOG service",
        srvname="pflog",
        srvstate="started",
        _sudo=True,
    )

    # Reload PF with new rules
    server.shell(
        name="Reload PF rules",
        commands=["pfctl -f /etc/pf.conf"],
        _sudo=True,
    )

    return True
