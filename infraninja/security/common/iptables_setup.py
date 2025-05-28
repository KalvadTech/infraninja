from importlib.resources import files as resource_files
from pyinfra.api.deploy import deploy
from pyinfra.operations import files, iptables, server
from pyinfra.facts.server import Command
from pyinfra.context import host


@deploy("iptables Setup for Ubuntu")
def iptables_setup():
    # facts
    iptables_exists = host.get_fact(Command, command="command -v iptables")
    if not iptables_exists:
        return "Skip iptables setup - iptables command not found"

    # Ensure chains exist
    iptables.chain(
        name="Ensure FORWARD chain exists",
        chain="FORWARD",
        present=True,
    )
    iptables.chain(
        name="Ensure OUTPUT chain exists",
        chain="OUTPUT",
        present=True,
    )

    # Set policies for non-INPUT chains only
    iptables.chain(
        name="Set default policy for FORWARD to DROP",
        chain="FORWARD",
        policy="DROP",
    )
    iptables.chain(
        name="Set default policy for OUTPUT to ACCEPT",
        chain="OUTPUT",
        policy="ACCEPT",
    )

    # Clear FORWARD and OUTPUT rules only
    server.shell(
        name="Flush FORWARD and OUTPUT rules",
        commands="iptables -F FORWARD && iptables -F OUTPUT",
    )

    # Allow loopback traffic (MUST be first rule)
    iptables.rule(
        name="Allow loopback traffic",
        chain="INPUT",
        jump="ACCEPT",
        in_interface="lo",
    )

    # Allow established and related connections (MUST be early)
    iptables.rule(
        name="Allow established and related incoming traffic",
        chain="INPUT",
        jump="ACCEPT",
        extras="-m state --state ESTABLISHED,RELATED",
    )

    # Allow incoming SSH (CRITICAL - must be before any DROP rules)
    iptables.rule(
        name="Allow incoming SSH",
        chain="INPUT",
        jump="ACCEPT",
        protocol="tcp",
        destination_port=22,
    )

    # Security rules (these can safely drop traffic now)
    iptables.rule(
        name="Disallow port scanning",
        chain="INPUT",
        jump="DROP",
        protocol="tcp",
        extras="--tcp-flags ALL NONE",
    )
    iptables.rule(
        name="Disallow port scanning (XMAS scan)",
        chain="INPUT",
        jump="DROP",
        protocol="tcp",
        extras="--tcp-flags ALL ALL",
    )

    # Logging rule for dropped traffic (before final DROP policy)
    iptables.rule(
        name="Log dropped traffic",
        chain="INPUT",
        jump="LOG",
        log_prefix="iptables-dropped: ",
        extras="--log-level 4",
    )

    # Ensure the /etc/iptables directory exists
    files.directory(
        name="Create /etc/iptables directory",
        path="/etc/iptables",
        present=True,
    )

    # Save the rules to make them persistent
    server.shell(
        name="Save iptables rules",
        commands="iptables-save > /etc/iptables/rules.v4",
    )

    # Ensure the /var/log/iptables directory exists
    files.directory(
        name="Create iptables log directory",
        path="/var/log/iptables",
        present=True,
    )

    template_path = resource_files("infraninja.security.templates").joinpath(
        "iptables_logrotate.conf.j2"
    )

    files.template(
        name="Upload iptables logrotate configuration",
        src=str(template_path),
        dest="/etc/logrotate.d/iptables",
        mode="644",
    )

    server.service(
        name="Ensure iptables service is enabled and started",
        service="iptables",
        running=True,
        enabled=True,
    )

    server.service(
        name="Ensure iptables service is enabled and started",
        service="iptables",
        running=True,
        enabled=True,
    )
