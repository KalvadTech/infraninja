from importlib.resources import files as resource_files

from pyinfra.api.deploy import deploy
from pyinfra.operations import files, server


@deploy("Auditd Setup")
def auditd_setup():
    """
    Set up auditd (Linux Audit System) for system activity monitoring.

    Configures auditd with custom audit rules for comprehensive system
    monitoring, sets up log rotation, and enables the audit service.
    Provides essential logging for security compliance and forensics.

    .. code:: python

        from infraninja.security.common.auditd_setup import auditd_setup
        auditd_setup()

    :returns: None
    :rtype: None

    .. note::
        On Fedora systems, auditd may require a manual reboot to fully
        apply new rules due to service restart restrictions.
    """
    # Get template paths using importlib.resources
    template_dir = resource_files("infraninja.security.templates.ubuntu")
    rules_path = template_dir.joinpath("auditd_rules.j2")
    logrotate_path = template_dir.joinpath("auditd_logrotate.j2")

    # Upload auditd rules from template
    files.template(
        name="Upload custom audit.rules",
        src=str(rules_path),
        dest="/etc/audit/rules.d/audit.rules",
        create_remote_dir=True,
    )

    # Apply log rotation configuration for auditd from template
    files.template(
        name="Upload auditd logrotate config",
        src=str(logrotate_path),
        dest="/etc/logrotate.d/audit",
    )

    server.service(
        name="Enable and start auditd",
        service="auditd",
        running=True,
        enabled=True,
    )

    # TODO: fedora doesnt allow you to do manual restart of auditd nor reload, possibly have to set a restart flag for reboot required

    server.service(
        name="Restart auditd to apply new rules",
        service="auditd",
        restarted=True,
    )
