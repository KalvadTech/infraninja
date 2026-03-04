"""Media autorun protection action"""

from typing import Any

from infraninja.actions.base import Action


class MediaAutorunProtection(Action):
    slug = "media-autorun-protection"
    name = {
        "en": "Media Autorun Protection",
        "fr": "Protection contre l'exécution automatique",
    }
    tags = ["security", "media", "autorun", "usb"]
    category = "security"
    color = "#F39C12"
    logo = "fa-usb"
    description = {
        "en": "Disable media autorun to prevent automatic execution of removable media content"
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
        from infraninja.security.common.media_autorun import media_autorun

        return media_autorun()
