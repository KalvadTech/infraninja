"""IPTables setup action"""

from typing import Any

from pyinfra import host
from pyinfra.facts.server import OsRelease

from infraninja.actions.base import Action


class IPTablesSetup(Action):
    slug = "iptables-setup"
    name = {"en": "IPTables Setup", "fr": "Configuration d'IPTables"}
    tags = ["security", "firewall", "iptables", "network"]
    category = "security"
    color = "#E74C3C"
    logo = "fa-fire"
    description = {
        "en": "Configure IPTables firewall rules for network security"
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
        os_id = host.get_fact(OsRelease).get("id", "").lower()
        if os_id == "alpine":
            from infraninja.security.alpine.iptables_setup import iptables_setup_alpine

            return iptables_setup_alpine()
        else:
            from infraninja.security.common.iptables_setup import iptables_setup

            return iptables_setup()
