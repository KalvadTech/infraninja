from importlib.resources import files as resource_files

from pyinfra.api.deploy import deploy
from pyinfra.context import host
from pyinfra.facts.server import Command
from pyinfra.operations import files, server


@deploy("nftables Setup Linux")
def nftables_setup():
    """
    Set up nftables firewall with modern packet filtering rules.

    Configures nftables as a modern replacement for iptables with
    improved performance and syntax. Creates a comprehensive ruleset
    from templates and enables the nftables service for persistence.

    .. code:: python

        from infraninja.security.common.nftables_setup import nftables_setup
        nftables_setup()

    :returns: None if successful, error message if nft command not found
    :rtype: None or str

    .. note::
        nftables is the modern successor to iptables and provides
        better performance and more flexible rule management.
    """
    template_path = resource_files("infraninja.security.templates").joinpath(
        "nftables_rules.nft.j2"
    )

    nft_exists = host.get_fact(Command, command="command -v nft")
    if not nft_exists:
        return "Skip nftables setup - nft not found"

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
