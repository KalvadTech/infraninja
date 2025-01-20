from pyinfra import host
from pyinfra.api import deploy
from pyinfra.facts.server import LinuxName
from pyinfra.operations import openrc, systemd, server

# Get the OS type
os = host.get_fact(LinuxName)

# List of services to disable if present
common_services = ["avahi-daemon", "cups", "bluetooth", "rpcbind", "vsftpd", "telnet"]


@deploy("Disable useless services common")
def disable_useless_services_common():
    for service in common_services:
        if os == "Ubuntu":
            try:
                if server.shell(
                    name=f"Check {service} status on Ubuntu",
                    commands=[f"systemctl is-active {service}"],
                    _ignore_errors=True
                ):
                    systemd.service(
                        name=f"Disable {service}",
                        service=service,
                        running=False,
                        enabled=False,
                        _ignore_errors=True
                    )
                    host.noop(f"Disabled service: {service} on Ubuntu")
                else:
                    host.noop(f"Skip {service} - not active on Ubuntu")
            except Exception as e:
                host.noop(f"Failed to handle {service} on Ubuntu: {str(e)}")

        elif os == "Alpine":
            try:
                if server.shell(
                    name=f"Check {service} status on Alpine",
                    commands=[f"rc-service {service} status"],
                    _ignore_errors=True
                ):
                    openrc.service(
                        name=f"Disable {service}",
                        service=service,
                        running=False,
                        enabled=False,
                        _ignore_errors=True
                    )
                    host.noop(f"Disabled service: {service} on Alpine")
                else:
                    host.noop(f"Skip {service} - not active on Alpine")
            except Exception as e:
                host.noop(f"Failed to handle {service} on Alpine: {str(e)}")
        else:
            host.noop(f"Skip {service} - unsupported OS: {os}")

    return True
