"""Fail2Ban setup action"""

from typing import Any

from pyinfra import host
from pyinfra.facts.server import OsRelease

from infraninja.actions.base import Action


class Fail2BanSetup(Action):
    slug = "fail2ban-setup"
    name = {"en": "Fail2Ban Setup", "fr": "Configuration de Fail2Ban"}
    tags = ["security", "intrusion-prevention", "fail2ban", "brute-force"]
    category = "security"
    color = "#D35400"
    logo = "fa-shield-alt"
    description = {
        "en": "Set up Fail2Ban intrusion prevention system with jail configuration"
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
            from infraninja.security.freebsd.fail2ban_setup import fail2ban_setup

            return fail2ban_setup()
        elif os_id == "alpine":
            from infraninja.security.alpine.fail2ban_setup import fail2ban_setup_alpine

            return fail2ban_setup_alpine()
        else:
            from infraninja.security.common.fail2ban_setup import fail2ban_setup

            return fail2ban_setup()
