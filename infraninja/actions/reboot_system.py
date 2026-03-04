"""Reboot system action"""

from typing import Any, Optional

from infraninja.actions.base import Action


class RebootSystem(Action):
    slug = "reboot-system"
    name = {"en": "Reboot System", "fr": "Redémarrage du système"}
    tags = ["system", "reboot", "maintenance"]
    category = "maintenance"
    color = "#E74C3C"
    logo = "fa-power-off"
    description = {
        "en": "Reboot the system if required, with configurable force and skip-check options"
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

    def __init__(
        self,
        need_reboot: Optional[bool] = None,
        force_reboot: bool = False,
        skip_reboot_check: bool = False,
    ):
        self.need_reboot = need_reboot
        self.force_reboot = force_reboot
        self.skip_reboot_check = skip_reboot_check
        super().__init__()

    def execute(self) -> Any:
        from infraninja.security.common.reboot_system import reboot_system

        return reboot_system(
            need_reboot=self.need_reboot,
            force_reboot=self.force_reboot,
            skip_reboot_check=self.skip_reboot_check,
        )
