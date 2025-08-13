from importlib.resources import files as resource_files

from pyinfra.api.deploy import deploy
from pyinfra.context import host
from pyinfra.facts.server import LinuxDistribution
from pyinfra.operations import crontab, files, server
from pyinfra.operations.freebsd import service


@deploy("FreeBSD rkhunter Setup")
def rkhunter_setup():
    """
    Set up rkhunter (Rootkit Hunter) for FreeBSD systems.

    Configures rkhunter with FreeBSD-specific settings, sets up automated
    daily scans via cron, configures log rotation using newsyslog, and
    initializes the rkhunter database. Uses FreeBSD paths and commands.

    .. code:: python

        from infraninja.security.freebsd.rkhunter_setup import rkhunter_setup
        rkhunter_setup()

    :returns: True if rkhunter setup completed successfully
    :rtype: bool
    :raises ValueError: If called on non-FreeBSD systems

    .. note::
        rkhunter should be installed via pkg before running this setup.
        On FreeBSD, rkhunter is installed as /usr/local/bin/rkhunter.

    .. warning::
        rkhunter may generate false positives on FreeBSD systems.
        Review scan results carefully and whitelist legitimate files.
    """
    # Verify this is FreeBSD
    distro = host.get_fact(LinuxDistribution)
    distro_name = str(distro.get("name", "")).lower() if distro else ""
    if distro_name != "freebsd":
        raise ValueError("This deployment is designed for FreeBSD systems only")

    # Get template paths using importlib.resources
    template_dir = resource_files("infraninja.security.templates.freebsd")
    config_path = template_dir.joinpath("rkhunter.conf.j2")
    script_path = template_dir.joinpath("rkhunter_scan_script.j2")
    newsyslog_path = template_dir.joinpath("rkhunter_newsyslog.conf.j2")

    # Create rkhunter configuration directory
    files.directory(
        name="Create rkhunter configuration directory",
        path="/usr/local/etc/rkhunter",
        present=True,
        mode="755",
        user="root",
        group="wheel",
    )

    # Upload rkhunter configuration file
    files.template(
        name="Upload FreeBSD rkhunter configuration",
        src=str(config_path),
        dest="/usr/local/etc/rkhunter.conf",
        backup=True,
        mode="644",
        user="root",
        group="wheel",
    )

    # Create rkhunter log directory
    files.directory(
        name="Create rkhunter log directory",
        path="/var/log/rkhunter",
        present=True,
        mode="755",
        user="root",
        group="wheel",
    )

    # Create secure rkhunter temporary directory
    files.directory(
        name="Create rkhunter temporary directory",
        path="/var/tmp/rkhunter",
        present=True,
        mode="700",
        user="root",
        group="wheel",
    )

    # Create rkhunter database directory
    files.directory(
        name="Create rkhunter database directory",
        path="/var/lib/rkhunter/db",
        present=True,
        mode="755",
        user="root",
        group="wheel",
    )

    # Create rkhunter internationalization directory
    files.directory(
        name="Create rkhunter i18n directory",
        path="/var/lib/rkhunter/db/i18n",
        present=True,
        mode="755",
        user="root",
        group="wheel",
    )

    # Upload rkhunter scan script for FreeBSD
    files.template(
        name="Upload FreeBSD rkhunter scan script",
        src=str(script_path),
        dest="/usr/local/bin/run_rkhunter_scan",
        mode="755",
        user="root",
        group="wheel",
    )

    # Set up log rotation using newsyslog
    files.template(
        name="Upload rkhunter newsyslog configuration",
        src=str(newsyslog_path),
        dest="/etc/newsyslog.conf.d/rkhunter.conf",
        create_remote_dir=True,
    )

    # Initialize rkhunter database
    server.shell(
        name="Initialize rkhunter database",
        commands=["/usr/local/bin/rkhunter --propupd"],
        _ignore_errors=True,
    )

    # Update rkhunter database
    server.shell(
        name="Update rkhunter database",
        commands=["/usr/local/bin/rkhunter --update"],
        _ignore_errors=True,
    )

    # Add cron job for daily rkhunter scans (daily at 3 AM)
    crontab.crontab(
        name="Add rkhunter daily cron job",
        command="/usr/local/bin/run_rkhunter_scan",
        user="root",
        hour="3",
        minute="0",
    )

    # Ensure cron service is enabled and running
    files.line(
        name="Enable cron in rc.conf",
        path="/etc/rc.conf",
        line='cron_enable="YES"',
        present=True,
    )

    # Restart cron to pick up new job
    service.service(
        name="Restart cron service",
        srvname="cron",
        srvstate="restarted",
    )

    # Create initial log file with proper permissions
    files.file(
        name="Create initial rkhunter log file",
        path="/var/log/rkhunter/rkhunter.log",
        present=True,
        mode="644",
        user="root",
        group="wheel",
    )

    # Run initial check to populate logs
    server.shell(
        name="Run initial rkhunter check",
        commands=[
            "/usr/local/bin/rkhunter --check --skip-keypress --report-warnings-only"
        ],
        _ignore_errors=True,
    )

    return True
