"""InfraNinja Actions - Entry point for infrastructure automation"""

from .acl_setup import ACLSetup
from .apparmor_setup import AppArmorSetup
from .arp_protection import ARPProtection
from .auditd_setup import AuditdSetup
from .base import Action, ActionResult, Composite, CompositeResult
from .chkrootkit_setup import ChkrootkitSetup
from .clamav_setup import ClamAVSetup
from .disable_services import DisableServices
from .fail2ban_setup import Fail2BanSetup
from .firewall_setup import FirewallSetup
from .full_security_setup import FullSecuritySetup
from .full_setup import FullSetup
from .iptables_setup import IPTablesSetup
from .kernel_hardening import KernelHardening
from .lynis_setup import LynisSetup
from .malware_protection import MalwareProtection
from .media_autorun_protection import MediaAutorunProtection
from .nftables_setup import NFTablesSetup
from .ntp_hardening import NTPHardening
from .pf_setup import PFSetup
from .reboot_system import RebootSystem
from .redis_auth_patch import RedisAuthPatch
from .rkhunter_setup import RkhunterSetup
from .routing_controls import RoutingControls
from .security_audit import SecurityAudit
from .security_hardening import SecurityHardening
from .security_package_install import SecurityPackageInstall
from .smtp_hardening import SmtpHardening
from .ssh_hardening import SSHHardening
from .ssh_keys import SSHKeys
from .suricata_setup import SuricataSetup
from .uae_compliance_audit import UAEComplianceAudit
from .update_and_upgrade import UpdateAndUpgrade

__all__ = [
    "ACLSetup",
    "Action",
    "ActionResult",
    "AppArmorSetup",
    "ARPProtection",
    "AuditdSetup",
    "ChkrootkitSetup",
    "ClamAVSetup",
    "Composite",
    "CompositeResult",
    "DisableServices",
    "Fail2BanSetup",
    "FirewallSetup",
    "FullSecuritySetup",
    "FullSetup",
    "IPTablesSetup",
    "KernelHardening",
    "LynisSetup",
    "MalwareProtection",
    "MediaAutorunProtection",
    "NFTablesSetup",
    "NTPHardening",
    "PFSetup",
    "RebootSystem",
    "RedisAuthPatch",
    "RkhunterSetup",
    "RoutingControls",
    "SecurityAudit",
    "SecurityHardening",
    "SecurityPackageInstall",
    "SmtpHardening",
    "SSHHardening",
    "SSHKeys",
    "SuricataSetup",
    "UAEComplianceAudit",
    "UpdateAndUpgrade",
]
