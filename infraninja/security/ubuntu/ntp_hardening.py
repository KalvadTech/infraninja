from importlib.resources import files as resource_files

from pyinfra.api import deploy
from pyinfra.operations import files, server


@deploy("NTP Hardening")
def ntp_hardening():
    template_path = resource_files("infraninja.security.templates.common").joinpath(
        "ntp.conf.j2"
    )

    files.template(
        name="Upload NTP configuration",
        src=str(template_path),
        dest="/etc/ntp.conf",
        user="root",
        group="root",
        mode="644",
    )

    # Restart the NTP service to apply changes
    server.service(
        name="Restart NTP service",
        service="ntp",
        running=True,
        restarted=True,
    )
