"""System information fact gathering."""

from pyinfra.facts.server import Arch, Hostname, Kernel, KernelVersion, Os, OsRelease

from infraninja.facts.base import Fact, FactResult


class SystemInfo(Fact):
    """
    Gather system information from the server.

    Collects OS, hostname, kernel, architecture and release details
    using pyinfra server facts.
    """

    slug = "system-info"
    name = {
        "en": "System Information",
        "ar": "معلومات النظام",
        "fr": "Informations systeme",
    }
    tags = ["system", "os", "info"]
    category = "system"
    color = "#3498DB"
    logo = "fa-info-circle"
    description = {
        "en": "Gather system information including OS, hostname, kernel, and architecture",
        "ar": "جمع معلومات النظام بما في ذلك نظام التشغيل واسم المضيف والنواة والهندسة المعمارية",
        "fr": "Collecter les informations systeme incluant OS, nom d'hote, noyau et architecture",
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

    def execute(self, **kwargs) -> FactResult:
        """
        Gather system information.

        Returns:
            FactResult with system info data
        """
        from pyinfra import host

        data = {
            "os": host.get_fact(Os),
            "hostname": host.get_fact(Hostname),
            "kernel": host.get_fact(Kernel),
            "kernel_version": host.get_fact(KernelVersion),
            "arch": host.get_fact(Arch),
            "os_release": host.get_fact(OsRelease),
        }

        return FactResult(
            fact=self.slug,
            success=True,
            data=data,
            message="System information gathered successfully",
        )
