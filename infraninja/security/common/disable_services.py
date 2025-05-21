# filepath: /home/xoity/Desktop/work/infraninja/infraninja/security/common/disable_services.py
from pyinfra.context import host
from pyinfra.api.deploy import deploy
from pyinfra.facts.server import LinuxDistribution, Which
from pyinfra.operations import openrc, systemd, sysvinit, runit, server


class ServiceDisabler:
    """
    Generalized class to disable common/unwanted services on any Linux distro using pyinfra operations.

    Args:
        services (list): List of services to disable. Default is a set of common services.
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
        id_like = distro.get("release_meta", {}).get("ID_LIKE", "")
        if id_like:
            id_like = id_like.lower()

        host.noop(f"Disabling services on: {distro_name} (ID: {distro_id})")

        for service in self.services:
            disabled = False

            # Debian-based distributions (Ubuntu, Debian, Mint, etc.)
            if (
                distro_name
                and any(d in distro_name for d in ["ubuntu", "debian", "mint"])
            ) or (id_like and any(d in id_like for d in ["debian", "ubuntu"])):
                if host.get_fact(Which, command="systemctl"):
                    systemd.service(
                        name=f"Disable {service} (Debian/Ubuntu)",
                        service=service,
                        running=False,
                        enabled=False,
                        _ignore_errors=True,
                    )
                    disabled = True

            # Alpine Linux uses OpenRC
            elif distro_name and "alpine" in distro_name:
                openrc.service(
                    name=f"Disable {service} (Alpine)",
                    service=service,
                    running=False,
                    enabled=False,
                    _ignore_errors=True,
                )
                disabled = True

            # RedHat family
            elif (
                distro_name
                and any(
                    d in distro_name
                    for d in ["fedora", "rhel", "centos", "rocky", "alma"]
                )
            ) or (id_like and "rhel" in id_like):
                systemd.service(
                    name=f"Disable {service} (RHEL/CentOS/Fedora)",
                    service=service,
                    running=False,
                    enabled=False,
                    _ignore_errors=True,
                )
                disabled = True

            # Arch Linux and derivatives
            elif any(
                d in (distro_name or "") for d in ["arch", "manjaro", "endeavouros"]
            ) or "arch" in (id_like or ""):
                systemd.service(
                    name=f"Disable {service} (Arch)",
                    service=service,
                    running=False,
                    enabled=False,
                    _ignore_errors=True,
                )
                disabled = True

            # Void Linux uses runit
            elif distro_name and "void" in distro_name:
                runit.service(
                    name=f"Disable {service} (Void)",
                    service=service,
                    running=False,
                    enabled=False,
                    _ignore_errors=True,
                )
                disabled = True

            # Generic fallbacks based on available commands (LAST RESORT)
            else:
                if host.get_fact(Which, command="systemctl"):
                    systemd.service(
                        name=f"Disable {service} (systemd)",
                        service=service,
                        running=False,
                        enabled=False,
                        _ignore_errors=True,
                    )
                    disabled = True
                elif host.get_fact(Which, command="rc-service"):
                    openrc.service(
                        name=f"Disable {service} (OpenRC)",
                        service=service,
                        running=False,
                        enabled=False,
                        _ignore_errors=True,
                    )
                    disabled = True
                elif host.get_fact(Which, command="sv"):
                    runit.service(
                        name=f"Disable {service} (runit)",
                        service=service,
                        running=False,
                        enabled=False,
                        _ignore_errors=True,
                    )
                    disabled = True
                elif host.get_fact(Which, command="service") or any(
                    host.get_fact(Which, command=cmd)
                    for cmd in ["update-rc.d", "chkconfig", "rc-update"]
                ):
                    sysvinit.service(
                        name=f"Disable {service} (SysVinit)",
                        service=service,
                        running=False,
                        enabled=False,
                        _ignore_errors=True,
                    )
                    disabled = True
                else:
                    # Fallback: try to stop via shell
                    server.shell(
                        name=f"Attempt to stop {service} (fallback)",
                        commands=[
                            f"systemctl stop {service} 2>/dev/null || "
                            f"service {service} stop 2>/dev/null || "
                            f"rc-service {service} stop 2>/dev/null || "
                            f"sv down {service} 2>/dev/null"
                        ],
                        _ignore_errors=True,
                    )
                    disabled = True

            if disabled:
                host.noop(f"Disabled service: {service} on {distro_name}")
            else:
                host.noop(
                    f"Could not determine how to disable: {service} on {distro_name}"
                )

        return True
