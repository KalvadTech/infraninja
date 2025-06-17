from importlib.resources import files as resource_files
from pyinfra.context import host
from pyinfra.operations import files
from pyinfra.facts.server import Hostname, Command
from pyinfra.api.deploy import deploy


@deploy("Update MOTD")
def motd():
    # Get hostname using the correct fact syntax
    hostname = host.get_fact(Hostname)

    # Define the command that will get the last access time
    last_access_cmd = (
        "last -n 1 | grep -v 'reboot' | head -n 1 | awk '{print $4,$5,$6,$7}'"
    )

    # Get the last login time using the correct fact syntax
    last_login = host.get_fact(Command, last_access_cmd)

    # Get template path using importlib.resources
    template_path = resource_files("infraninja.security.templates").joinpath("motd.j2")

    # Create the MOTD file using template with all needed variables
    files.template(
        name="Deploy MOTD file",
        src=str(template_path),
        dest="/etc/motd",
        hostname=hostname,
        last_login=last_login,
    )
