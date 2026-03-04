"""SMTP hardening action"""

from typing import Any

from infraninja.actions.base import Action


class SmtpHardening(Action):
    slug = "smtp-hardening"
    name = {"en": "SMTP Hardening", "fr": "Durcissement SMTP"}
    tags = ["security", "smtp", "email", "hardening"]
    category = "security"
    color = "#3498DB"
    logo = "fa-envelope"
    description = {
        "en": "Harden SMTP server configuration to prevent email-based attacks"
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
        from infraninja.security.common.smtp_hardening import smtp_hardening

        return smtp_hardening()
