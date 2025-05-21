from importlib.resources import files as resource_files
from pyinfra.api import deploy
from pyinfra.operations import files, crontab


@deploy("chkrootkit Setup")
def chkrootkit_setup():
    template_dir = resource_files("infraninja.security.templates.ubuntu")
    script_path = template_dir.joinpath("chkrootkit_scan_script.j2")
    logrotate_path = template_dir.joinpath("chkrootkit_logrotate.j2")

    files.template(
        name="Upload chkrootkit scan script",
        src=str(script_path),
        dest="/usr/local/bin/run_chkrootkit_scan",
        mode="755",
    )

    # Set up a cron job to run the chkrootkit scan script weekly (on Sundays at 2 AM)
    crontab.crontab(
        name="Add chkrootkit cron job for weekly scans",
        command="/usr/local/bin/run_chkrootkit_scan",
        user="root",
        day_of_week="0",
        hour="2",
        minute="0",
    )

    # Ensure log directory exists for chkrootkit
    files.directory(
        name="Create chkrootkit log directory",
        path="/var/log/chkrootkit",
        present=True,
    )

    # Apply log rotation settings for chkrootkit logs from template
    files.template(
        name="Upload chkrootkit logrotate configuration",
        src=str(logrotate_path),
        dest="/etc/logrotate.d/chkrootkit",
    )
