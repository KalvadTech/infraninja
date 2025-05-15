from importlib.resources import files as resource_files
from pyinfra.context import host
from pyinfra.api.deploy import deploy
from pyinfra.facts.server import LinuxName
from pyinfra.operations import files, openrc, server, systemd

os = host.get_fact(LinuxName)


@deploy("nftables Setup for Alpine Linux")
def nftables_setup_alpine():
    template_path = resource_files("infraninja.security.templates.common").joinpath(
        "nftables_rules.nft.j2"
    )

    # Ensure the /etc/nftables directory exists
    files.directory(
        name="Create /etc/nftables directory",
        path="/etc/nftables",
        present=True,
    )

    # Upload nftables rules file
    files.template(
        name="Upload nftables rules from template",
        src=str(template_path),
        dest="/etc/nftables/ruleset.nft",
        mode="644",
    )

    # Apply nftables rules
    server.shell(
        name="Apply nftables rules",
        commands="nft -f /etc/nftables/ruleset.nft",
    )


# Enable nftables to restore rules on reboot based on OS
if os == "Ubuntu":
    systemd.service(
        name="Enable nftables service",
        service="nftables",
        running=True,
        enabled=True,
    )
elif os == "Alpine":
    openrc.service(
        name="Enable nftables service",
        service="nftables",
        running=True,
        enabled=True,
    )
