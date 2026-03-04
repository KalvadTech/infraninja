"""Hardware information fact gathering."""

from pyinfra.facts.hardware import BlockDevices, Cpus, Memory, NetworkDevices

from infraninja.facts.base import Fact, FactResult


class Hardware(Fact):
    """
    Gather hardware information from the server.

    Collects CPU, memory, block device and network device details
    using pyinfra hardware facts.
    """

    slug = "hardware"
    name = {
        "en": "Hardware Information",
        "ar": "معلومات الأجهزة",
        "fr": "Informations materiel",
    }
    tags = ["hardware", "cpu", "memory", "network"]
    category = "hardware"
    color = "#E67E22"
    logo = "fa-microchip"
    description = {
        "en": "Gather hardware information including CPUs, memory, block devices, and network devices",
        "ar": "جمع معلومات الأجهزة بما في ذلك المعالجات والذاكرة وأجهزة الكتل وأجهزة الشبكة",
        "fr": "Collecter les informations materiel incluant CPUs, memoire, peripheriques de stockage et reseau",
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
        Gather hardware information.

        Returns:
            FactResult with hardware info data
        """
        from pyinfra import host

        data = {
            "cpus": host.get_fact(Cpus),
            "memory": host.get_fact(Memory),
            "block_devices": host.get_fact(BlockDevices),
            "network_devices": host.get_fact(NetworkDevices),
        }

        return FactResult(
            fact=self.slug,
            success=True,
            data=data,
            message="Hardware information gathered successfully",
        )
