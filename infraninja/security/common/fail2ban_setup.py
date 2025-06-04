from importlib.resources import files as resource_files
from pyinfra.api import deploy
from pyinfra.operations import files, server


@deploy("Fail2Ban Setup")
def fail2ban_setup():
    template_path = resource_files("infraninja.security.templates.ubuntu").joinpath(
        "fail2ban_setup_ubuntu.j2"
    )

    files.template(
        name="Upload Fail2Ban configuration",
        src=str(template_path),
        dest="/etc/fail2ban/jail.local",
    )

    # Enable and start the Fail2Ban service
    server.service(
        name="Enable and start Fail2Ban",
        service="fail2ban",
        running=True,
        enabled=True,
    )

    # Restart Fail2Ban to apply new settings
    server.service(
        name="Restart Fail2Ban to apply changes",
        service="fail2ban",
        restarted=True,
    )
