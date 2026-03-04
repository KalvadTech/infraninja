"""Suricata IDS/IPS setup action"""

from typing import Any

from pyinfra import host
from pyinfra.facts.server import OsRelease

from infraninja.actions.base import Action


class SuricataSetup(Action):
    slug = "suricata-setup"
    name = {"en": "Suricata Setup", "fr": "Configuration de Suricata"}
    tags = ["security", "ids", "ips", "suricata", "network"]
    category = "security"
    color = "#2C3E50"
    logo = "fa-eye"
    description = {
        "en": "Install and configure Suricata intrusion detection and prevention system"
    }
    os_available = ["ubuntu", "debian", "alpine"]

    def execute(self) -> Any:
        os_id = host.get_fact(OsRelease).get("id", "").lower()
        if os_id == "alpine":
            from infraninja.security.alpine.suricata_setup import suricata_setup

            return suricata_setup()
        else:
            from infraninja.security.ubuntu.suricata_setup import suricata_setup

            return suricata_setup()
