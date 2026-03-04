"""Disable unnecessary services action"""

from typing import Any, List, Optional

from pyinfra import host
from pyinfra.facts.server import OsRelease

from infraninja.actions.base import Action


class DisableServices(Action):
    slug = "disable-services"
    name = {"en": "Disable Services", "fr": "Désactivation des services"}
    tags = ["security", "services", "hardening", "attack-surface"]
    category = "security"
    color = "#E67E22"
    logo = "fa-ban"
    description = {"en": "Disable unnecessary system services to reduce attack surface"}
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

    def __init__(self, services: Optional[List[str]] = None):
        self.services = services
        super().__init__()

    def execute(self) -> Any:
        os_id = host.get_fact(OsRelease).get("id", "").lower()
        if os_id == "freebsd":
            from infraninja.security.freebsd.disable_services import (
                FreeBSDServiceDisabler,
            )

            disabler = FreeBSDServiceDisabler(services=self.services)
            return disabler.deploy()
        else:
            from infraninja.security.common.disable_services import ServiceDisabler

            disabler = ServiceDisabler(services=self.services)
            return disabler.deploy()
