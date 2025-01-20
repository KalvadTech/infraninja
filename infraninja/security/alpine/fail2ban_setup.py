from pyinfra.api import deploy
from pyinfra.operations import files, openrc
from pyinfra import host
from pyinfra.facts.files import Directory, File


@deploy("Fix and configure Fail2Ban on Alpine Linux")
def fail2ban_setup_alpine():
    # Check if fail2ban is installed
    if host.get_fact(File, path="/usr/bin/fail2ban-server") is None:
        host.noop("Skip Fail2Ban setup - fail2ban is not installed")
        return

    # Upload Fail2Ban configuration file from template
    files.template(
        name="Upload Fail2Ban config from template",
        src="../infraninja/security/templates/alpine/fail2ban_setup_alpine.j2",
        dest="/etc/fail2ban/jail.local",
    )

    # Ensure the Fail2Ban log directory exists
    if host.get_fact(Directory, path="/var/log/fail2ban") is None:
        files.directory(
            name="Create Fail2Ban log directory",
            path="/var/log/fail2ban",
            present=True,
        )

    # Check if OpenRC and the fail2ban service file exist
    if host.get_fact(File, path="/etc/init.d/fail2ban") is None:
        host.noop("Skip service setup - fail2ban service not found")
    else:
        # Enable and start Fail2Ban service
        openrc.service(
            name="Enable and start Fail2Ban",
            service="fail2ban",
            running=True,
            enabled=True,
        )
