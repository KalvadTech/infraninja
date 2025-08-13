from importlib.resources import files as resource_files

from pyinfra.api.deploy import deploy
from pyinfra.context import host
from pyinfra.facts.server import LinuxDistribution
from pyinfra.operations import files, server
from pyinfra.operations.freebsd import service


@deploy("BSM (Basic Security Module) Setup")
def bsm_setup():
    """
    Set up BSM (Basic Security Module) for FreeBSD system activity monitoring.

    BSM is FreeBSD's equivalent to Linux auditd. This function configures BSM
    with custom audit classes and events for comprehensive system monitoring,
    sets up log rotation via newsyslog, and enables the audit service.
    Provides essential logging for security compliance and forensics.

    .. code:: python

        from infraninja.security.freebsd.bsm_setup import bsm_setup
        bsm_setup()

    :returns: True if BSM setup completed successfully
    :rtype: bool
    :raises ValueError: If called on non-FreeBSD systems

    .. note::
        BSM requires the auditd daemon to be enabled in rc.conf.
        The audit trail files are stored in /var/audit by default.

    .. warning::
        Enabling BSM audit can generate significant amounts of log data.
        Ensure adequate disk space and proper log rotation is configured.
    """
    # Verify this is FreeBSD
    distro = host.get_fact(LinuxDistribution)
    distro_name = str(distro.get("name", "")).lower() if distro else ""
    if distro_name != "freebsd":
        raise ValueError("This deployment is designed for FreeBSD systems only")

    # Get template paths using importlib.resources
    template_dir = resource_files("infraninja.security.templates.freebsd")
    audit_control_path = template_dir.joinpath("audit_control.j2")
    audit_user_path = template_dir.joinpath("audit_user.j2")
    newsyslog_path = template_dir.joinpath("bsm_newsyslog.conf.j2")

    # Ensure audit directory exists
    files.directory(
        name="Create audit directory",
        path="/var/audit",
        present=True,
        mode="750",
        user="root",
        group="wheel",
    )

    # Upload BSM audit_control configuration from template
    files.template(
        name="Upload BSM audit_control configuration",
        src=str(audit_control_path),
        dest="/etc/security/audit_control",
        backup=True,
        create_remote_dir=True,
    )

    # Upload BSM audit_user configuration from template
    files.template(
        name="Upload BSM audit_user configuration",
        src=str(audit_user_path),
        dest="/etc/security/audit_user",
        backup=True,
        create_remote_dir=True,
    )

    # Apply log rotation configuration for BSM via newsyslog
    files.template(
        name="Upload BSM newsyslog configuration",
        src=str(newsyslog_path),
        dest="/etc/newsyslog.conf.d/bsm.conf",
        create_remote_dir=True,
    )

    # Enable auditd in rc.conf
    files.line(
        name="Enable auditd in rc.conf",
        path="/etc/rc.conf",
        line='auditd_enable="YES"',
        present=True,
    )

    # Enable audit flags in rc.conf for comprehensive logging
    files.line(
        name="Set audit flags in rc.conf",
        path="/etc/rc.conf",
        line='audit_flags="lo,aa"',
        present=True,
    )

    # Start and enable the audit service
    service.service(
        srvname="auditd",
        srvstate="started",
    )

    # Restart auditd to apply new configuration
    service.service(
        srvname="auditd",
        srvstate="restarted",
    )

    # Initialize or update audit configuration
    # First check if audit is enabled and get current state
    server.shell(
        name="Refresh audit configuration",
        commands=["audit -s 2>/dev/null || audit -i 2>/dev/null || true"],
        _ignore_errors=True,
    )

    return True
