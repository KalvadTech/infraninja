"""Full facts composite fact gathering."""

from .base import CompositeFact
from .hardware import Hardware
from .system_info import SystemInfo


class FullFacts(CompositeFact):
    """
    Gather complete system and hardware facts.

    Executes the following facts in order:
    1. SystemInfo - Gather OS, hostname, kernel, architecture
    2. Hardware - Gather CPUs, memory, block devices, network devices
    """

    slug = "full-facts"
    name = {
        "en": "Full System Facts",
        "ar": "معلومات النظام الكاملة",
        "fr": "Informations systeme completes",
    }
    tags = ["system", "hardware", "info", "composite"]
    category = "system"
    color = "#9B59B6"
    logo = "fa-clipboard-list"
    description = {
        "en": "Gather complete system and hardware information from the server",
        "ar": "جمع معلومات النظام والأجهزة الكاملة من الخادم",
        "fr": "Collecter les informations completes du systeme et du materiel du serveur",
    }

    facts = [
        SystemInfo,
        Hardware,
    ]
