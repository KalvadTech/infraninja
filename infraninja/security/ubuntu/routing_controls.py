from pyinfra.api.deploy import deploy
from pyinfra.operations import server


@deploy("Apply Routing Controls")
def routing_controls():
    server.service(service="apparmor", running=True, enabled=True)
    server.service(service="auditd", running=True, enabled=True)

    server.sysctl(
        name="Enable positive source/destination address checks",
        key="net.ipv4.conf.all.rp_filter",
        value=1,
        persist=True,
    )

    server.shell(name="Reload sysctl settings", commands=["sysctl -p"])
