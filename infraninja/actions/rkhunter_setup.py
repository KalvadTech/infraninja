"""Rkhunter setup action (FreeBSD)"""

from typing import Any

from infraninja.actions.base import Action


class RkhunterSetup(Action):
    slug = "rkhunter-setup"
    name = {"en": "Rkhunter Setup", "fr": "Configuration de Rkhunter"}
    tags = ["security", "rootkit", "rkhunter", "detection"]
    category = "security"
    color = "#C0392B"
    logo = "fa-bug"
    description = {
        "en": "Install and configure rkhunter rootkit detection tool on FreeBSD"
    }
    os_available = ["freebsd"]

    def execute(self) -> Any:
        from infraninja.security.freebsd.rkhunter_setup import rkhunter_setup

        return rkhunter_setup()
