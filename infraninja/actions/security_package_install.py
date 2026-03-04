"""Security package installation action"""

from typing import Any, Dict, List, Optional

from pyinfra import host
from pyinfra.facts.server import OsRelease

from infraninja.actions.base import Action


class SecurityPackageInstall(Action):
    slug = "security-package-install"
    name = {"en": "Security Package Install", "fr": "Installation des paquets de sécurité"}
    tags = ["security", "packages", "installation", "tools"]
    category = "security"
    color = "#2ECC71"
    logo = "fa-download"
    description = {
        "en": "Install essential security packages and tools across all supported operating systems"
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
        packages: Optional[Dict] = None,
        zypper_repos: Optional[List[str]] = None,
    ):
        self.packages = packages
        self.zypper_repos = zypper_repos
        super().__init__()

    def execute(self) -> Any:
        os_id = host.get_fact(OsRelease).get("id", "").lower()
        if os_id == "freebsd":
            from infraninja.security.freebsd.install_tools import (
                FreeBSDSecurityInstaller,
            )

            installer = FreeBSDSecurityInstaller(packages=self.packages)
            return installer.deploy()
        elif os_id == "alpine":
            from infraninja.security.alpine.install_tools import install_security_tools

            return install_security_tools()
        elif os_id in ("ubuntu", "debian"):
            from infraninja.security.ubuntu.install_tools import install_security_tools

            return install_security_tools()
        else:
            from infraninja.security.common.common_install import CommonPackageInstaller

            installer = CommonPackageInstaller(
                packages=self.packages, zypper_repos=self.zypper_repos
            )
            return installer.deploy()
