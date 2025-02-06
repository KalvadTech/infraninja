from pyinfra import host
from pyinfra.operations import files, server
from pyinfra.facts.server import Hostname
from pyinfra.api import deploy


@deploy("Update MOTD")
def motd():
    # Get hostname using the correct fact syntax
    hostname = host.get_fact(Hostname)

    server.shell(
        name="Update last access time",
        commands=["last -n 1 | grep -v reboot | head -n 1 | awk '{print $4,$5,$6,$7}'"],
    )

    # Create the MOTD file using template
    files.template(
        name="Deploy MOTD file",
        src="infraninja/security/templates/motd.j2",  # Updated path
        dest="/etc/motd",
        hostname=hostname,
    )

    # Define the command that will get the last access time
    last_access_cmd = (
        "last -n 1 | grep -v 'reboot' | head -n 1 | awk '{print $4,$5,$6,$7}'"
    )

    # Execute the command to ensure it's in the MOTD
    server.shell(
        name="Update last access time in MOTD",
        commands=[f'echo "Last Jinn Access: $({last_access_cmd})" >> /etc/motd'],
    )
