"""Lynis security audit setup action"""

from typing import Any

from pyinfra import host
from pyinfra.facts.server import OsRelease

from infraninja.actions.base import Action


class LynisSetup(Action):
    slug = "lynis-setup"
    name = {"en": "Lynis Setup", "fr": "Configuration de Lynis"}
    tags = ["security", "audit", "lynis", "compliance"]
    category = "security"
    color = "#16A085"
    logo = "fa-search"
    description = {
        "en": "Install and configure Lynis security auditing tool for system hardening assessment"
    }
    os_available = [
        "ubuntu",
        "debian",
        "alpine",
        "freebsd",
        "rhel",
        "centos",
        "fedora",
        "arch",
    ]

    def execute(self) -> Any:
        os_id = host.get_fact(OsRelease).get("id", "").lower()
        if os_id == "freebsd":
            from infraninja.security.freebsd.lynis_setup import lynis_setup

            return lynis_setup()
        elif os_id == "alpine":
            from infraninja.security.alpine.lynis_setup import lynis_setup

            return lynis_setup()
        elif os_id in ("ubuntu", "debian"):
            from infraninja.security.ubuntu.lynis_setup import lynis_setup

            return lynis_setup()
        else:
            from infraninja.security.ubuntu.lynis_setup import lynis_setup

            return lynis_setup()
