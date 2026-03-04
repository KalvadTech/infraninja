"""UAE IA Compliance audit action"""

import importlib.util
from pathlib import Path
from typing import Any

from infraninja.actions.base import Action


class UAEComplianceAudit(Action):
    slug = "uae-compliance-audit"
    name = {"en": "UAE Compliance Audit", "fr": "Audit de conformité UAE"}
    tags = ["security", "compliance", "audit", "uae", "regulation"]
    category = "security"
    color = "#006400"
    logo = "fa-balance-scale"
    description = {
        "en": "Run UAE Information Assurance compliance audit (T3.6.3) for privileged operations logging"
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
        module_path = (
            Path(__file__).resolve().parent.parent
            / "security"
            / "common"
            / "UAE_IA_COMPLIANCE"
            / "T3.6.3.py"
        )
        spec = importlib.util.spec_from_file_location("T3_6_3", str(module_path))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module.t3_6_3()
