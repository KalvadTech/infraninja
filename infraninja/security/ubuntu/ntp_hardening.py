from pyinfra.api import deploy
from pyinfra.operations import files, server


@deploy("NTP Hardening")
def ntp_hardening():
    files.template(
        name="Upload NTP configuration",
        src="../infraninja/security/templates/ubuntu/ntp.conf.j2",
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
