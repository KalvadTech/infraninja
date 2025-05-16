from importlib.resources import files as resource_files
from pyinfra.context import host
from pyinfra.api.deploy import deploy
from pyinfra.operations import files, server
from pyinfra.facts.server import Command

@deploy("nftables Setup Linux")
def nftables_setup():
    template_path = resource_files("infraninja.security.templates").joinpath(
        "nftables_rules.nft.j2"
    )

    nft_exists = host.get_fact(Command, command="command -v nft")
    if not nft_exists:
        return

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

    server.service(
        name="Enable nftables service",
        service="nftables",
        running=True,
        enabled=True,
    )
