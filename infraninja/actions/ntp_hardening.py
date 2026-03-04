"""NTP hardening action"""

from typing import Any

from infraninja.actions.base import Action


class NTPHardening(Action):
    slug = "ntp-hardening"
    name = {"en": "NTP Hardening", "fr": "Durcissement NTP"}
    tags = ["security", "ntp", "time", "hardening"]
    category = "security"
    color = "#2980B9"
    logo = "fa-clock"
    description = {
        "en": "Harden NTP configuration and apply security patches for time synchronization"
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
        from infraninja.security.ubuntu.ntp_hardening import ntp_hardening

        ntp_hardening()

        from infraninja.security.patches.ntp_security_patch import (
            deploy_ntp_security_patch,
        )

        return deploy_ntp_security_patch()
