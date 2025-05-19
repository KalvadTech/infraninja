# filepath: /home/xoity/Desktop/work/infraninja/infraninja/security/common/disable_services.py
from pyinfra.context import host
from pyinfra.api.deploy import deploy
from pyinfra.facts.server import LinuxDistribution
from pyinfra.operations import server


class ServiceDisabler:
    """
    Generalized class to disable common/unwanted services on any Linux distro using pyinfra operations.

    Args:
        services (list): List of services to disable. Default is a set of common services.

    Usage:
        service_disabler = ServiceDisabler(services=["service1", "service2"])
        service_disabler.deploy()
    """

    DEFAULT_SERVICES = [
        "avahi-daemon",
        "cups",
        "bluetooth",
        "rpcbind",
        "vsftpd",
        "telnet",
    ]

    def __init__(self, services=None):
        self.services = services or self.DEFAULT_SERVICES.copy()

    @deploy("Disable unwanted/common services")
    def deploy(self):
        # Get detailed distribution information
        distro = host.get_fact(LinuxDistribution)
        distro_name = distro.get("name", "")
        if distro_name:
            distro_name = distro_name.lower()
        distro_id = distro.get("release_meta", {}).get("ID", "")
        if distro_id:
            distro_id = distro_id.lower()

        host.noop(f"Disabling services on: {distro_name} (ID: {distro_id})")

        for service in self.services:
            # Use server.service operation which automatically detects the appropriate init system
            # Disable service regardless of distro
            server.service(
                name=f"Disable {service}",
                service=service,
                running=False,
                enabled=False,
                _ignore_errors=True,
            )

            host.noop(f"Disabled service: {service} on {distro_name}")

        return True
