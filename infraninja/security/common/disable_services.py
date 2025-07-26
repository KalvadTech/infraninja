from pyinfra.api.deploy import deploy
from pyinfra.context import host
from pyinfra.facts.server import LinuxDistribution
from pyinfra.operations import server


class ServiceDisabler:
    """
    Generalized class to disable common/unwanted services on any Linux distro.

    Provides a flexible way to disable services that are commonly not needed
    or could pose security risks. Uses pyinfra operations to ensure services
    are both stopped and disabled from starting at boot.

    .. code:: python

        from infraninja.security.common.disable_services import ServiceDisabler

        # Use default services list
        ServiceDisabler().deploy()

        # Use custom services list
        custom_services = ["service1", "service2", "unwanted-daemon"]
        ServiceDisabler(services=custom_services).deploy()

    :param services: List of services to disable
    :type services: list, optional
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
        """
        Initialize ServiceDisabler with custom or default services list.

        :param services: List of service names to disable
        :type services: list, optional
        """
        self.services = services or self.DEFAULT_SERVICES.copy()

    @deploy("Disable unwanted/common services")
    def deploy(self):
        """
        Deploy service disabling configuration.

        Disables all services in the services list by stopping them and
        preventing them from starting at boot. Detects the Linux distribution
        and logs the process for each service.

        :returns: True if deployment completed successfully
        :rtype: bool
        """
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
            server.service(
                name=f"Disable {service}",
                service=service,
                running=False,
                enabled=False,
                _ignore_errors=True,
            )

            host.noop(f"Disabled service: {service} on {distro_name}")

        return True
