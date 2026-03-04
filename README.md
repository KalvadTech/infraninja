# InfraNinja

A modern infrastructure automation framework built on PyInfra, providing reusable deployment tasks used by Kalvad teams and made publicly available via PyPI.

InfraNinja simplifies infrastructure management through **Actions** (reusable deployment tasks), **Facts** (read-only server information gathering), and **Inventories** (dynamic server management).

## Features

- **Action-Based Architecture**: 26 pre-built actions covering security hardening, firewall setup, malware protection, auditing, and system maintenance
- **Composite Actions**: Group related actions together (e.g. `FullSecuritySetup` runs 7 sub-actions in sequence)
- **Facts**: Gather read-only server information (hardware specs, OS details) without making changes
- **Dynamic Inventories**: Automated server discovery from Jinn API and Coolify
- **Multi-OS Support**: Ubuntu, Debian, Alpine Linux, FreeBSD, RHEL, CentOS, Fedora, and Arch Linux
- **Multilingual**: Actions support English, Arabic, and French metadata
- **Compliance**: UAE IA compliance modules and security auditing tools (Lynis, Auditd)

## Getting Started

**Requirements:** Python 3.10+

```bash
pip install infraninja
```

Or using uv:

```bash
uv add infraninja
```

## Quick Examples

### Using Actions

```python
from infraninja import SSHHardening, UpdateAndUpgrade

# Update system packages
UpdateAndUpgrade().execute()

# Harden SSH with custom settings
SSHHardening(permit_root_login="no").execute()
```

### Composite Actions

```python
from infraninja import FullSecuritySetup

# Run full security setup (updates, packages, hardening, firewall, fail2ban, malware, audit)
result = FullSecuritySetup().execute()

for action_result in result.results:
    print(f"  {action_result.action}: {'OK' if action_result.success else 'FAILED'}")
```

### Gathering Facts

```python
from infraninja import Hardware, SystemInfo

# Get hardware information
hw = Hardware()
hw.execute()

# Get system information
sys_info = SystemInfo()
sys_info.execute()
```

### Using Inventories

```python
from infraninja.inventories import Jinn, Coolify

# Jinn API integration
jinn = Jinn(
    api_url="https://jinn-api.kalvad.cloud",
    api_key="your-api-key",
    groups=["production", "web"],
    tags=["nginx", "database"]
)
servers = jinn.get_servers()

# Coolify integration
coolify = Coolify(
    api_url="https://coolify.example.com/api",
    api_key="your-api-key",
    tags=["prod", "staging"]
)
servers = coolify.get_servers()
```

## Available Actions

### Security & Hardening

| Action | Description |
|--------|-------------|
| `SSHHardening` | SSH server hardening with security best practices |
| `KernelHardening` | Kernel security parameters via sysctl |
| `DisableServices` | Disable unnecessary services to reduce attack surface |
| `MediaAutorunProtection` | Disable media autorun |
| `ARPProtection` | ARP poisoning protection |
| `ACLSetup` | Access Control Lists for file permissions |
| `SmtpHardening` | SMTP server hardening |
| `AppArmorSetup` | AppArmor mandatory access control (Ubuntu/Debian) |
| `NTPHardening` | NTP configuration hardening with security patches |
| `RoutingControls` | Network routing controls (Ubuntu/Debian) |

### Firewall

| Action | Description |
|--------|-------------|
| `IPTablesSetup` | IPTables firewall rules |
| `NFTablesSetup` | NFTables firewall rules |
| `PFSetup` | PF packet filter (FreeBSD) |

### Intrusion Prevention & Malware Detection

| Action | Description |
|--------|-------------|
| `Fail2BanSetup` | Fail2Ban intrusion prevention |
| `ChkrootkitSetup` | Chkrootkit rootkit detection |
| `RkhunterSetup` | Rkhunter rootkit detection (FreeBSD) |
| `ClamAVSetup` | ClamAV antivirus |
| `SuricataSetup` | Suricata IDS/IPS |

### Auditing & Compliance

| Action | Description |
|--------|-------------|
| `AuditdSetup` | System auditing with auditd/BSM |
| `LynisSetup` | Lynis security audit tool |
| `UAEComplianceAudit` | UAE IA compliance audit (T3.6.3) |

### System & Packages

| Action | Description |
|--------|-------------|
| `UpdateAndUpgrade` | System package updates |
| `SecurityPackageInstall` | Install security packages and tools |
| `SSHKeys` | SSH key management and deployment |
| `RedisAuthPatch` | Enable Redis authentication |
| `RebootSystem` | Conditional system reboot |

### Composite Actions

| Action | Sub-Actions |
|--------|-------------|
| `SecurityHardening` | KernelHardening, SSHHardening, DisableServices, MediaAutorunProtection, ARPProtection |
| `FirewallSetup` | IPTablesSetup, NFTablesSetup |
| `MalwareProtection` | ChkrootkitSetup, RkhunterSetup, ClamAVSetup |
| `SecurityAudit` | AuditdSetup, LynisSetup, UAEComplianceAudit |
| `FullSecuritySetup` | UpdateAndUpgrade, SecurityPackageInstall, SecurityHardening, FirewallSetup, Fail2BanSetup, MalwareProtection, SecurityAudit |
| `FullSetup` | UpdateAndUpgrade, SSHHardening, SSHKeys |

## Development

### Setup

```bash
git clone https://github.com/KalvadTech/infraninja.git
cd infraninja
uv sync
```

### Running Tests

```bash
uv run pytest

# With coverage
uv run pytest --cov=infraninja tests/
```

### Building the Package

```bash
uv build
```

### Building the Documentation

The documentation is generated from action/fact metadata using MkDocs:

```bash
# Install MkDocs and theme
pip install mkdocs mkdocs-material

# Regenerate docs from action metadata
python generate_docs.py

# Serve locally at http://127.0.0.1:8000
mkdocs serve

# Build static site to site/
mkdocs build
```

## Contributions

Contributions are welcome! If you spot any bugs or have ideas for new features, feel free to open an issue or submit a pull request.

## Maintainers

- **Mohammad Abu-khader** <mohammad@kalvad.com>
- **Pierre Guillemot** <pierre@kalvad.com>
- **Loic Tosser** <loic@kalvad.com>

## Community & Support

- **Repository**: [GitHub - KalvadTech/infraninja](https://github.com/KalvadTech/infraninja)
- **PyPI Package**: [pypi.org/project/infraninja](https://pypi.org/project/infraninja/)
- **Issues**: [Report bugs and request features](https://github.com/KalvadTech/infraninja/issues)
- **Changelog**: See [CHANGELOG.md](CHANGELOG.md) for version history

## License

This project is licensed under the **MIT License**.
