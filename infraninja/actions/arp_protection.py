"""ARP poisoning protection action"""

from typing import Any

from infraninja.actions.base import Action


class ARPProtection(Action):
    slug = "arp-protection"
    name = {"en": "ARP Protection", "fr": "Protection ARP"}
    tags = ["security", "network", "arp", "poisoning"]
    category = "security"
    color = "#8E44AD"
    logo = "fa-network-wired"
    description = {
        "en": "Protect against ARP poisoning attacks with network-level safeguards"
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
        from infraninja.security.common.arp_poisoning_protection import (
            arp_poisoning_protectio,
        )

        return arp_poisoning_protectio()
