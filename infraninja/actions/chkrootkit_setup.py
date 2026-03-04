"""Chkrootkit setup action"""

from typing import Any

from pyinfra import host
from pyinfra.facts.server import OsRelease

from infraninja.actions.base import Action


class ChkrootkitSetup(Action):
    slug = "chkrootkit-setup"
    name = {"en": "Chkrootkit Setup", "fr": "Configuration de Chkrootkit"}
    tags = ["security", "rootkit", "malware", "detection"]
    category = "security"
    color = "#C0392B"
    logo = "fa-bug"
    description = {
        "en": "Install and configure chkrootkit for rootkit detection scanning"
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
            from infraninja.security.freebsd.chkrootkit_setup import chkrootkit_setup

            return chkrootkit_setup()
        else:
            from infraninja.security.common.chkrootkit_setup import chkrootkit_setup

            return chkrootkit_setup()
