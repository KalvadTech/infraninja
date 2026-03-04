"""Security hardening composite action"""

from .base import Composite
from .arp_protection import ARPProtection
from .disable_services import DisableServices
from .kernel_hardening import KernelHardening
from .media_autorun_protection import MediaAutorunProtection
from .ssh_hardening import SSHHardening


class SecurityHardening(Composite):
    slug = "security-hardening"
    name = {"en": "Security Hardening", "fr": "Durcissement de la sécurité"}
    tags = ["security", "hardening", "composite"]
    category = "security"
    color = "#E74C3C"
    logo = "fa-shield-alt"
    description = {
        "en": "Comprehensive security hardening including kernel, SSH, services, media autorun, and ARP protection"
    }

    actions = [
        KernelHardening,
        SSHHardening,
        DisableServices,
        MediaAutorunProtection,
        ARPProtection,
    ]
    stop_on_failure = True
