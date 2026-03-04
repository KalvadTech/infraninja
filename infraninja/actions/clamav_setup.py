"""ClamAV antivirus setup action"""

from typing import Any

from pyinfra import host
from pyinfra.facts.server import OsRelease

from infraninja.actions.base import Action


class ClamAVSetup(Action):
    slug = "clamav-setup"
    name = {"en": "ClamAV Setup", "fr": "Configuration de ClamAV"}
    tags = ["security", "antivirus", "clamav", "malware"]
    category = "security"
    color = "#E74C3C"
    logo = "fa-shield-virus"
    description = {
        "en": "Install and configure ClamAV antivirus for malware scanning"
    }
    os_available = ["ubuntu", "debian", "alpine"]

    def execute(self) -> Any:
        os_id = host.get_fact(OsRelease).get("id", "").lower()
        if os_id == "alpine":
            from infraninja.security.alpine.clamav_setup import clamav_setup

            return clamav_setup()
        else:
            from infraninja.security.ubuntu.clamav_setup import clamav_setup

            return clamav_setup()
