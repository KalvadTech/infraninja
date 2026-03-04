"""Audit daemon setup action"""

from typing import Any

from pyinfra import host
from pyinfra.facts.server import OsRelease

from infraninja.actions.base import Action


class AuditdSetup(Action):
    slug = "auditd-setup"
    name = {"en": "Auditd Setup", "fr": "Configuration d'Auditd"}
    tags = ["security", "audit", "logging", "monitoring"]
    category = "security"
    color = "#27AE60"
    logo = "fa-clipboard-list"
    description = {
        "en": "Set up system auditing with auditd (Linux) or BSM (FreeBSD) for security event logging"
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
        os_id = host.get_fact(OsRelease).get("id", "").lower()
        if os_id == "freebsd":
            from infraninja.security.freebsd.bsm_setup import bsm_setup

            return bsm_setup()
        else:
            from infraninja.security.common.auditd_setup import auditd_setup

            return auditd_setup()
