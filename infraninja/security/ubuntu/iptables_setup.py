from importlib.resources import files as resource_files
from pyinfra.api import deploy
from pyinfra.operations import files, iptables, server, systemd
from pyinfra.facts.server import Command, LinuxDistribution
from pyinfra.context import host



@deploy("iptables Setup for Ubuntu")
def iptables_setup():

    #facts
    iptables_exists = host.get_fact(Command, command="command -v iptables")
    if not iptables_exists:
        return "Skip iptables setup - iptables command not found"
    
    # Get detailed distribution information
    distro = host.get_fact(LinuxDistribution)
    distro_name = distro.get("name", "")
    distro_id = distro.get("release_meta", {}).get("ID", "").lower()
    id_like = distro.get("release_meta", {}).get("ID_LIKE", "").lower()


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

    # Get service manager information
    distro_name = distro_name.lower() if distro_name else ""

    # Install iptables-persistent if not installed (for Debian-based systems)
    if "ubuntu" in distro_name or "debian" in distro_name or "debian" in id_like:
        server.shell(
            name="Install iptables-persistent if not present",
            commands="apt-get install -y iptables-persistent || true",
        )
        # Enable iptables-persistent to restore rules on reboot
        systemd.service(
            name="Enable iptables-persistent to restore rules on reboot",
            service="netfilter-persistent",
            running=True,
            enabled=True,
        )
    # For systemd-based systems
    elif host.get_fact(Command, command="command -v systemctl"):
        systemd.service(
            name="Enable and start iptables service",
            service="iptables",
            running=True,
            enabled=True,
        )
    # For systems using openrc (like Alpine)
    elif host.get_fact(Command, command="command -v rc-service"):
        server.shell(
            name="Enable iptables service with OpenRC",
            commands="rc-update add iptables default",
        )
    # Fallback for other systems - just ensure rules are saved
    else:
        server.shell(
            name="Create restore script for iptables",
            commands=[
                "echo '#!/bin/sh' > /etc/network/if-pre-up.d/iptables",
                "echo 'iptables-restore < /etc/iptables/rules.v4' >> /etc/network/if-pre-up.d/iptables",
                "chmod +x /etc/network/if-pre-up.d/iptables",
            ],
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
