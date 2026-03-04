"""NFTables setup action"""

from typing import Any

from infraninja.actions.base import Action


class NFTablesSetup(Action):
    slug = "nftables-setup"
    name = {"en": "NFTables Setup", "fr": "Configuration de NFTables"}
    tags = ["security", "firewall", "nftables", "network"]
    category = "security"
    color = "#C0392B"
    logo = "fa-fire"
    description = {
        "en": "Configure NFTables firewall rules as a modern replacement for IPTables"
    }
    os_available = [
        "ubuntu",
        "debian",
        "alpine",
        "rhel",
        "centos",
        "fedora",
        "arch",
    ]

    def execute(self) -> Any:
        from infraninja.security.common.nftables_setup import nftables_setup

        return nftables_setup()
