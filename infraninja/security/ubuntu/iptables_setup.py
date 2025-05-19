from importlib.resources import files as resource_files
from pyinfra.api import deploy
from pyinfra.operations import files, iptables, server, systemd


@deploy("iptables Setup for Ubuntu")
def iptables_setup():
    # Ensure chains exist before flushing
    iptables.chain(
        name="Ensure INPUT chain exists",
        chain="INPUT",
        present=True,
    )
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

    # Flush existing rules within chains
    iptables.rule(
        name="Flush existing rules in INPUT chain",
        chain="INPUT",
        jump="ACCEPT",
        present=False,
    )
    iptables.rule(
        name="Flush existing rules in FORWARD chain",
        chain="FORWARD",
        jump="ACCEPT",
        present=False,
    )
    iptables.rule(
        name="Flush existing rules in OUTPUT chain",
        chain="OUTPUT",
        jump="ACCEPT",
        present=False,
    )

    # Set default policies
    iptables.chain(
        name="Set default policy for INPUT",
        chain="INPUT",
        policy="DROP",
    )
    iptables.chain(
        name="Set default policy for FORWARD",
        chain="FORWARD",
        policy="DROP",
    )
    iptables.chain(
        name="Set default policy for OUTPUT",
        chain="OUTPUT",
        policy="ACCEPT",
    )

    # Allow loopback traffic
    iptables.rule(
        name="Allow loopback traffic",
        chain="INPUT",
        jump="ACCEPT",
        in_interface="lo",
    )

    # Allow established and related incoming traffic
    iptables.rule(
        name="Allow established and related incoming traffic",
        chain="INPUT",
        jump="ACCEPT",
        extras="-m state --state ESTABLISHED,RELATED",
    )

    # Allow incoming SSH
    iptables.rule(
        name="Allow incoming SSH",
        chain="INPUT",
        jump="ACCEPT",
        protocol="tcp",
        destination_port=22,
    )

    # Disallow port scanning
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

    # Logging rules for incoming traffic
    iptables.rule(
        name="Log incoming traffic",
        chain="INPUT",
        jump="LOG",
        log_prefix="iptables-input: ",
    )

    # Save the rules to make them persistent
    server.shell(
        name="Save iptables rules",
        commands="iptables-save > /etc/iptables/rules.v4",
    )

    # Ensure the /etc/iptables directory exists
    files.directory(
        name="Create /etc/iptables directory",
        path="/etc/iptables",
        present=True,
    )

    # Enable iptables-persistent to restore rules on reboot
    systemd.service(
        name="Enable iptables-persistent to restore rules on reboot",
        service="netfilter-persistent",
        running=True,
        enabled=True,
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
