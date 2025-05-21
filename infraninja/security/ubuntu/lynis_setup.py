from importlib.resources import files as resource_files
from pyinfra.api.deploy import deploy
from pyinfra.operations import files, crontab


@deploy("Lynis Setup")
def lynis_setup():
    template_dir = resource_files("infraninja.security.templates.ubuntu")
    config_path = template_dir.joinpath("lynis_setup_ubuntu.j2")
    audit_path = template_dir.joinpath("lynis_audit_script_ubuntu.j2")
    logrotate_path = template_dir.joinpath("lynis_logrotate_ubuntu.j2")

    # Upload Lynis configuration file from template
    files.template(
        name="Upload Lynis configuration for detailed reporting",
        src=str(config_path),
        dest="/etc/lynis/lynis.cfg",
    )

    # Upload the Lynis audit wrapper script from template and make it executable
    files.template(
        name="Upload Lynis audit wrapper script",
        src=str(audit_path),
        dest="/usr/local/bin/run_lynis_audit",
        mode="755",
    )

    # Set up a cron job to run the Lynis audit script weekly (on Sundays at midnight)
    crontab.crontab(
        name="Add Lynis cron job for weekly audits",
        command="/usr/local/bin/run_lynis_audit",
        user="root",
        day_of_week="7",
        hour="0",
        minute="0",
    )

    # Ensure log directory exists for Lynis
    files.directory(
        name="Create Lynis log directory",
        path="/var/log/lynis",
        present=True,
    )

    # Apply log rotation settings for Lynis reports from template
    files.template(
        name="Upload Lynis logrotate configuration",
        src=str(logrotate_path),
        dest="/etc/logrotate.d/lynis",
    )
