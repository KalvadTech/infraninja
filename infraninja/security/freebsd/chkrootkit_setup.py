from importlib.resources import files as resource_files

from pyinfra.api.deploy import deploy
from pyinfra.context import host
from pyinfra.facts.server import LinuxDistribution
from pyinfra.operations import crontab, files
from pyinfra.operations.freebsd import service


@deploy("FreeBSD chkrootkit Setup")
def chkrootkit_setup():
    """
    Set up chkrootkit rootkit scanner for FreeBSD systems.

    Configures chkrootkit with automated weekly scans via cron, proper log
    rotation using newsyslog (FreeBSD's log rotation system), and creates
    necessary directories. Uses FreeBSD-specific paths and commands.

    .. code:: python

        from infraninja.security.freebsd.chkrootkit_setup import chkrootkit_setup
        chkrootkit_setup()

    :returns: True if chkrootkit setup completed successfully
    :rtype: bool
    :raises ValueError: If called on non-FreeBSD systems

    .. note::
        chkrootkit should be installed via pkg before running this setup.
        On FreeBSD, chkrootkit is installed as /usr/local/bin/chkrootkit.

    .. warning::
        chkrootkit scans can be resource-intensive and may generate false
        positives. Review scan results carefully before taking action.
    """
    # Verify this is FreeBSD
    distro = host.get_fact(LinuxDistribution)
    distro_name = str(distro.get("name", "")).lower() if distro else ""
    if distro_name != "freebsd":
        raise ValueError("This deployment is designed for FreeBSD systems only")

    # Get template paths using importlib.resources
    template_dir = resource_files("infraninja.security.templates.freebsd")
    script_path = template_dir.joinpath("chkrootkit_scan_script.j2")
    newsyslog_path = template_dir.joinpath("chkrootkit_newsyslog.conf.j2")

    # Upload chkrootkit scan script for FreeBSD
    files.template(
        name="Upload FreeBSD chkrootkit scan script",
        src=str(script_path),
        dest="/usr/local/bin/run_chkrootkit_scan",
        mode="755",
        user="root",
        group="wheel",
    )

    # Create chkrootkit log directory
    files.directory(
        name="Create chkrootkit log directory",
        path="/var/log/chkrootkit",
        present=True,
        mode="755",
        user="root",
        group="wheel",
    )

    # Set up log rotation using newsyslog (FreeBSD's log rotation system)
    files.template(
        name="Upload chkrootkit newsyslog configuration",
        src=str(newsyslog_path),
        dest="/etc/newsyslog.conf.d/chkrootkit.conf",
        create_remote_dir=True,
    )

    # Add cron job for weekly chkrootkit scans (Sundays at 2 AM)
    crontab.crontab(
        name="Add chkrootkit weekly cron job",
        command="/usr/local/bin/run_chkrootkit_scan",
        user="root",
        day_of_week="0",
        hour="2",
        minute="0",
    )

    # Ensure cron service is enabled and running
    files.line(
        name="Enable cron in rc.conf",
        path="/etc/rc.conf",
        line='cron_enable="YES"',
        present=True,
    )

    # Restart cron to pick up new job using FreeBSD service operation
    service.service(
        name="Restart cron service",
        srvname="cron",
        srvstate="restarted",
    )

    # Create initial empty log file with proper permissions
    files.file(
        name="Create initial chkrootkit log file",
        path="/var/log/chkrootkit/chkrootkit.log",
        present=True,
        mode="644",
        user="root",
        group="wheel",
    )

    return True
