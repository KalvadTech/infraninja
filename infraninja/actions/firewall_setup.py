"""Firewall setup composite action"""

from .base import Composite
from .iptables_setup import IPTablesSetup
from .nftables_setup import NFTablesSetup


class FirewallSetup(Composite):
    slug = "firewall-setup"
    name = {"en": "Firewall Setup", "fr": "Configuration du pare-feu"}
    tags = ["security", "firewall", "network", "composite"]
    category = "security"
    color = "#E74C3C"
    logo = "fa-fire"
    description = {"en": "Configure firewall rules using IPTables and NFTables"}
    os_available = [
        "ubuntu",
        "debian",
        "alpine",
        "rhel",
        "centos",
        "fedora",
        "arch",
    ]

    actions = [
        IPTablesSetup,
        NFTablesSetup,
    ]
    stop_on_failure = False
