"""Security audit composite action"""

from .base import Composite
from .auditd_setup import AuditdSetup
from .lynis_setup import LynisSetup
from .uae_compliance_audit import UAEComplianceAudit


class SecurityAudit(Composite):
    slug = "security-audit"
    name = {"en": "Security Audit", "fr": "Audit de sécurité"}
    tags = ["security", "audit", "compliance", "monitoring", "composite"]
    category = "security"
    color = "#27AE60"
    logo = "fa-clipboard-check"
    description = {
        "en": "Comprehensive security auditing with auditd, Lynis, and UAE compliance checks"
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
        AuditdSetup,
        LynisSetup,
        UAEComplianceAudit,
    ]
    stop_on_failure = False
