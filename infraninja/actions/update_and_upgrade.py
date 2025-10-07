"""System update and upgrade action"""

from typing import Any

from pyinfra import host, operations
from pyinfra.api import DeployError
from pyinfra.facts.server import OsRelease

from infraninja.actions.base import Action


class UpdateAndUpgradeAction(Action):
    """
    Update and upgrade system packages across multiple Linux distributions.

    Performs package repository updates followed by system-wide package upgrades.
    Supports Debian/Ubuntu (apt), RHEL/CentOS/Fedora (dnf), Arch (pacman),
    Alpine (apk), and FreeBSD (pkg).

    Example:
        .. code:: python

            from infraninja.actions.update_and_upgrade import UpdateAndUpgradeAction

            action = UpdateAndUpgradeAction()
            action.execute()
    """

    slug = "update-and-upgrade"
    name = {
        "en": "Update and Upgrade System",
        "ar": "تحديث وترقية النظام",
        "fr": "Mettre à jour et améliorer le système",
    }
    tags = ["system", "updates", "packages", "maintenance"]
    category = "maintenance"
    color = "#FF6B35"
    logo = "fa-sync-alt"
    description = {
        "en": "Update package repositories and upgrade all installed packages across multiple Linux distributions and FreeBSD",
        "ar": "تحديث مستودعات الحزم وترقية جميع الحزم المثبتة عبر توزيعات Linux المتعددة وFreeBSD",
        "fr": "Mettre à jour les dépôts de paquets et améliorer tous les paquets installés sur plusieurs distributions",
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
        """
        Execute system update and upgrade.

        Detects the operating system and runs the appropriate package manager
        update and upgrade commands.

        Returns:
            Result of the deployment operation
        """
        self._deploy_update()
        self._deploy_upgrade()

    def _deploy_update(self):
        """Update package repositories based on the detected OS."""
        os_id = host.get_fact(OsRelease).get("id")
        os_id_like = host.get_fact(OsRelease).get("id_like")

        if os_id_like:
            if "debian" in os_id_like:
                operations.server.apt.update(
                    name="Update apt repositories",
                )
            elif "rhel" in os_id_like:
                operations.server.dnf.update(
                    name="Update dnf repositories",
                )
            elif "arch" in os_id_like:
                operations.server.pacman.update(
                    name="Update pacman repositories",
                )
            else:
                raise DeployError(f"Unsupported OS: {os_id} {os_id_like}")
        else:
            if os_id == "alpine":
                operations.server.apk.update(
                    name="Update apk repositories",
                )
            elif os_id == "freebsd":
                operations.server.shell(
                    name="Run freebsd-update",
                    commands=["freebsd-update fetch"],
                )
                operations.server.shell(
                    name="Run pkg update",
                    commands=["pkg update"],
                )
            else:
                raise DeployError(f"Unsupported OS: {os_id} {os_id_like}")

    def _deploy_upgrade(self):
        """Upgrade system packages based on the detected OS."""
        os_id = host.get_fact(OsRelease).get("id")
        os_id_like = host.get_fact(OsRelease).get("id_like")

        if os_id_like:
            if "debian" in os_id_like:
                operations.server.apt.upgrade(
                    name="Upgrade apt repositories",
                )
            elif "rhel" in os_id_like:
                operations.server.dnf.upgrade(
                    name="Upgrade dnf repositories",
                )
            elif "arch" in os_id_like:
                operations.server.pacman.upgrade(
                    name="Upgrade pacman repositories",
                )
            else:
                raise DeployError(f"Unsupported OS: {os_id} {os_id_like}")
        else:
            if os_id == "alpine":
                operations.server.apk.upgrade(
                    name="Upgrade apk repositories",
                )
            elif os_id == "freebsd":
                operations.server.shell(
                    name="Run pkg upgrade",
                    commands=["pkg upgrade"],
                )
            else:
                raise DeployError(f"Unsupported OS: {os_id} {os_id_like}")
