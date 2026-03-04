"""Full security setup composite action"""

from .base import Composite
from .fail2ban_setup import Fail2BanSetup
from .firewall_setup import FirewallSetup
from .malware_protection import MalwareProtection
from .security_audit import SecurityAudit
from .security_hardening import SecurityHardening
from .security_package_install import SecurityPackageInstall
from .update_and_upgrade import UpdateAndUpgrade


class FullSecuritySetup(Composite):
    slug = "full-security-setup"
    name = {"en": "Full Security Setup", "fr": "Configuration de sécurité complète"}
    tags = ["security", "hardening", "comprehensive", "composite"]
    category = "security"
    color = "#8E44AD"
    logo = "fa-lock"
    description = {
        "en": "Complete security setup including updates, packages, hardening, firewall, intrusion prevention, malware protection, and auditing"
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

    actions = [
        UpdateAndUpgrade,
        SecurityPackageInstall,
        SecurityHardening,
        FirewallSetup,
        Fail2BanSetup,
        MalwareProtection,
        SecurityAudit,
    ]
    stop_on_failure = False
