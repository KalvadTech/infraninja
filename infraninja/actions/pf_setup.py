"""PF firewall setup action (FreeBSD)"""

from typing import Any

from infraninja.actions.base import Action


class PFSetup(Action):
    slug = "pf-setup"
    name = {"en": "PF Setup", "fr": "Configuration de PF"}
    tags = ["security", "firewall", "pf", "freebsd"]
    category = "security"
    color = "#E74C3C"
    logo = "fa-fire"
    description = {
        "en": "Configure PF packet filter firewall on FreeBSD systems"
    }
    os_available = ["freebsd"]

    def execute(self) -> Any:
        from infraninja.security.freebsd.pf_setup import pf_setup

        return pf_setup()
