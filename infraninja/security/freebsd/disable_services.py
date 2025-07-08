from pyinfra.api.deploy import deploy
from pyinfra.context import host
from pyinfra.operations.freebsd import service


class FreeBSDServiceDisabler:
    """
    FreeBSD-specific class to disable common/unwanted services using pyinfra FreeBSD operations.

    Args:
        services (list): List of services to disable. Default is a set of common FreeBSD services.

    Usage:
        service_disabler = ServiceDisabler(services=["service1", "service2"])
        service_disabler.deploy()
    """

    DEFAULT_SERVICES = [
        "avahi_daemon",
        "cupsd",
        "bluetooth",
        "rpcbind",
        "vsftpd",
        "telnetd",
        "sendmail",
    ]

    def __init__(self, services=None):
        self.services = self.DEFAULT_SERVICES.copy() if services is None else services

    @deploy("Disable Unwanted Services on FreeBSD")
    def deploy(self):
        host.noop("Disabling services on FreeBSD")

        for service_name in self.services:

            @deploy(f"Disable unwanted/common service: {service_name}")
            def disable():
                service.service(
                    srvname=service_name,
                    srvstate="stopped",
                    _ignore_errors=True,
                )
                host.noop(f"Disabled service: {service_name} on FreeBSD")

            disable()

        return True
