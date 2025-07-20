"""
NTP Security Patch - Restricts queries in /etc/ntp.conf
"""

from pyinfra.api.deploy import deploy
from pyinfra.context import host
from pyinfra.facts.files import File, FindInFile
from pyinfra.operations import files, server


# Simple deployment function
@deploy("Deploy NTP Security Patch")
def deploy_ntp_security_patch():
    """Deploy NTP security patch."""

    # Deploy directly rather than calling the decorated method
    config_path = "/etc/ntp.conf"

    # Skip if config doesn't exist
    if not host.get_fact(File, path=config_path):
        host.noop(f"NTP config not found at {config_path}")
        return None

    # Check if already configured
    if host.get_fact(FindInFile, path=config_path, pattern=r"^restrict.*noquery.*$"):
        host.noop("NTP restrict noquery already configured")
        return None

    # Add restrict noquery line
    files.line(
        name="Add restrict noquery",
        path=config_path,
        line="restrict default noquery",
        present=True,
    )

    # Restart NTP service
    server.service(
        name="Restart NTP",
        service="ntpd",
        running=True,
        restarted=True,
        _ignore_errors=True,
    )
