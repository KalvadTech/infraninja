"""Kernel hardening action"""

from typing import Any

from infraninja.actions.base import Action


class KernelHardening(Action):
    slug = "kernel-hardening"
    name = {"en": "Kernel Hardening", "fr": "Durcissement du noyau"}
    tags = ["security", "kernel", "hardening", "sysctl"]
    category = "security"
    color = "#1ABC9C"
    logo = "fa-microchip"
    description = {
        "en": "Apply kernel security parameters via sysctl for system hardening"
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
        from infraninja.security.common.kernel_hardening import kernel_hardening

        return kernel_hardening()
