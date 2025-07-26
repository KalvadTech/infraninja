from importlib.resources import files as resource_files

from pyinfra.api.deploy import deploy
from pyinfra.context import host
from pyinfra.facts.server import LinuxDistribution
from pyinfra.operations import crontab, files, server
from pyinfra.operations.freebsd import service


@deploy("FreeBSD Lynis Setup")
def lynis_setup():
    """
    Set up Lynis security auditing tool for FreeBSD systems.

    Configures Lynis with FreeBSD-specific settings, sets up automated
    weekly security audits via cron, configures log rotation using newsyslog,
    and creates necessary directories. Uses FreeBSD paths and commands.

    .. code:: python

        from infraninja.security.freebsd.lynis_setup import lynis_setup
        lynis_setup()

    :returns: True if Lynis setup completed successfully
    :rtype: bool
    :raises ValueError: If called on non-FreeBSD systems

    .. note::
        Lynis should be installed via pkg before running this setup.
        On FreeBSD, Lynis is installed as /usr/local/bin/lynis.

    .. warning::
        Lynis audits can take significant time and may affect system performance.
        Schedule audits during off-peak hours.
    """
    # Verify this is FreeBSD
    distro = host.get_fact(LinuxDistribution)
    distro_name = str(distro.get("name", "")).lower() if distro else ""
    if distro_name != "freebsd":
        raise ValueError("This deployment is designed for FreeBSD systems only")

    # Get template paths using importlib.resources
    template_dir = resource_files("infraninja.security.templates.freebsd")
    config_path = template_dir.joinpath("lynis.prf.j2")
    script_path = template_dir.joinpath("lynis_audit_script.j2")
    newsyslog_path = template_dir.joinpath("lynis_newsyslog.conf.j2")

    # Create Lynis configuration directory
    files.directory(
        name="Create Lynis configuration directory",
        path="/usr/local/etc/lynis",
        present=True,
        mode="755",
        user="root",
        group="wheel",
    )

    # Upload Lynis configuration file
    files.template(
        name="Upload FreeBSD Lynis configuration",
        src=str(config_path),
        dest="/usr/local/etc/lynis/default.prf",
        backup=True,
        mode="644",
        user="root",
        group="wheel",
    )

    # Create Lynis log directory
    files.directory(
        name="Create Lynis log directory",
        path="/var/log/lynis",
        present=True,
        mode="755",
        user="root",
        group="wheel",
    )

    # Create Lynis reports directory
    files.directory(
        name="Create Lynis reports directory",
        path="/var/log/lynis/reports",
        present=True,
        mode="755",
        user="root",
        group="wheel",
    )

    # Upload Lynis audit script for FreeBSD
    files.template(
        name="Upload FreeBSD Lynis audit script",
        src=str(script_path),
        dest="/usr/local/bin/run_lynis_audit",
        mode="755",
        user="root",
        group="wheel",
    )

    # Set up log rotation using newsyslog
    files.template(
        name="Upload Lynis newsyslog configuration",
        src=str(newsyslog_path),
        dest="/etc/newsyslog.conf.d/lynis.conf",
        create_remote_dir=True,
    )

    # Add cron job for weekly Lynis audits (Sundays at 4 AM)
    crontab.crontab(
        name="Add Lynis weekly audit cron job",
        command="/usr/local/bin/run_lynis_audit",
        user="root",
        day_of_week="0",
        hour="4",
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

    # Create initial log files with proper permissions
    files.file(
        name="Create initial Lynis log file",
        path="/var/log/lynis/lynis.log",
        present=True,
        mode="644",
        user="root",
        group="wheel",
    )

    files.file(
        name="Create initial Lynis report file",
        path="/var/log/lynis/lynis-report.dat",
        present=True,
        mode="644",
        user="root",
        group="wheel",
    )

    # Update Lynis database
    server.shell(
        name="Update Lynis database",
        commands=["/usr/local/bin/lynis update info"],
        _ignore_errors=True,
    )

    # Run initial audit to test setup
    server.shell(
        name="Run initial Lynis audit test",
        commands=[
            "/usr/local/bin/lynis audit system --quick --quiet --no-colors "
            "--logfile /var/log/lynis/lynis.log "
            "--report-file /var/log/lynis/lynis-report.dat"
        ],
        _ignore_errors=True,
    )

    return True
