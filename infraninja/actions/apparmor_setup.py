"""AppArmor configuration action"""

from typing import Any

from infraninja.actions.base import Action


class AppArmorSetup(Action):
    slug = "apparmor-setup"
    name = {"en": "AppArmor Setup", "fr": "Configuration d'AppArmor"}
    tags = ["security", "apparmor", "mac", "access-control"]
    category = "security"
    color = "#9B59B6"
    logo = "fa-user-shield"
    description = {
        "en": "Configure AppArmor mandatory access control profiles for application sandboxing"
    }
    os_available = ["ubuntu", "debian"]

    def execute(self) -> Any:
        from infraninja.security.ubuntu.apparmor_config import apparmor_config

        return apparmor_config()
