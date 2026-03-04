# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.5.0] - 2026-03-04

### Architecture

- Introduced **Action framework** (`Action`, `Composite`, `ActionResult`, `CompositeResult` base classes) as the primary entry point for all infrastructure automation tasks, replacing the old `deploys/` module structure
- Introduced **Facts framework** (`Fact`, `CompositeFact`, `FactResult`, `CompositeFactResult` base classes) for read-only server information gathering
- Introduced **Inventories framework** (`Inventory` base class) formalizing dynamic server discovery with `Jinn` and `Coolify` providers
- All actions, facts, and inventories are now importable directly from `infraninja` and registered in `__all__`

### Features

- Added 26 Action classes wrapping all existing security modules with automatic OS dispatch:
  SSHHardening, SSHKeys, UpdateAndUpgrade, ACLSetup, ARPProtection, AuditdSetup,
  ChkrootkitSetup, SecurityPackageInstall, DisableServices, Fail2BanSetup,
  IPTablesSetup, KernelHardening, MediaAutorunProtection, NFTablesSetup,
  SmtpHardening, LynisSetup, PFSetup, RkhunterSetup, ClamAVSetup, SuricataSetup,
  AppArmorSetup, NTPHardening, RoutingControls, RedisAuthPatch, UAEComplianceAudit,
  RebootSystem
- Added 6 composite actions for grouped execution:
  SecurityHardening, FirewallSetup, MalwareProtection, SecurityAudit,
  FullSecuritySetup, FullSetup
- Added Facts module with `Hardware` and `SystemInfo` facts, and `FullFacts` composite
- Added `generate_docs.py` for auto-generating MkDocs documentation from action/fact/inventory metadata
- Added MkDocs configuration (`mkdocs.yml`) with Material theme and custom styling
- Added `list_actions` and `list_inventories` CLI utilities

### Improvements

- Migrated build tooling from `requirements.txt` to `uv` with `pyproject.toml`
- Upgraded dependencies: build 1.4.0, pyinfra 3.6.1, pytest 9.0.2
- Expanded ruff linter rules (security, complexity, naming, import sorting)
- Auto-discovery in `generate_docs.py` — new actions/facts only need to be added to `__init__.py`
- Fixed Font Awesome 6 icon rendering in generated docs (missing `fas` prefix)
- Refactored `pubkeys.py` and `pubkeys_delete.py` for cleaner SSH key management
- Minor fixes across security modules (Alpine, FreeBSD, Ubuntu) for linter compliance and consistency
- Updated CI workflows for pytest and ruff

### Removed

- Removed `infraninja/deploys/` module (replaced by `infraninja/actions/`)
- Removed `infraninja/netdata.py` and Netdata template (deprecated)
- Removed `requirements.txt` (replaced by `pyproject.toml`)

## [0.4.0] - 2025-10-31

Merged PR #30: Created info fetching task and has custom facts

### Features

- **System Information Fetching Module**: New `info_fetch` deployment module for comprehensive system information gathering
- **Custom Facts**: Added custom pyinfra facts for enhanced system data collection:
  - `OsRelease`: Parse and retrieve OS release information from `/etc/os-release`
  - `MemInfo`: Memory usage statistics with flexible measurements (percent, GB, MB) and occurrence types (usage, total)
  - `CPUInfo`: CPU information and statistics
  - `DiskInfo`: Disk usage and partition information
  - `NetworkInfo`: Network interface and connectivity details
- **Integrated System Facts**: Utilizes pyinfra's built-in facts including:
  - Hostname, OS, Linux distribution name
  - Users and Groups
  - Kernel modules and Sysctl parameters
  - Mount points and filesystem information
  - SELinux status and security limits
- **JSON Serialization**: Safe serialization with datetime handling via custom `DateTimeEncoder`
- **Comprehensive Data Collection**: Single deployment to gather complete system inventory across multiple dimensions

### Developer Experience

- Modular fact system for easy extension and customization
- Type-safe fact processing with error handling
- Consistent JSON output format for integration with monitoring and inventory systems

## [0.3.0] - 2025-09-16

Merged PR #25: freeBSD more tasks

### Changes

- Added FreeBSD security tasks and modules, including:
  - ACL management
  - BSM (Basic Security Module) auditing setup
  - chkrootkit malware detection
  - Disable/trim unnecessary services
  - Fail2ban setup
  - Base tools installation
  - Lynis security auditing
  - PF firewall setup
  - rkhunter rootkit scanner
  - SSH hardening
  - System package update operations
- Refactored reboot handling to use pyinfra's built-in `RebootRequired` fact
  for consistent cross-distro reboot checks (Linux + FreeBSD)

### Testing

- Expanded FreeBSD test coverage (ACL, BSM, chkrootkit, disable services, fail2ban,
  install tools, lynis, PF, rkhunter, SSH hardening, update packages)
- Refactored reboot tests to align with `RebootRequired` fact usage

## [0.2.1] - 2025-06-10

### Features

- SSH key management system with SSHKeyManager and SSHKeyDeleter classes
- Comprehensive test suite with pytest integration
- Support for multiple Linux distributions in package updates (Debian/Ubuntu, Alpine, RHEL/CentOS/Fedora, Arch, openSUSE, FreeBSD, Void Linux)
- Enhanced Coolify inventory management with SSH configuration
- Advanced security hardening modules including:
  - SSH hardening with automated configuration
  - Kernel hardening for multiple OS types
  - Fail2Ban setup for Alpine and Ubuntu
  - Auditd setup and configuration
  - ClamAV antivirus setup
  - Chkrootkit malware detection
  - Lynis security auditing
  - Suricata IDS setup
- Network security features:
  - IPTables and NFTables setup
  - ARP poisoning protection
  - Media autorun protection
- UAE IA Compliance modules (T3.6.3)
- MOTD (Message of the Day) customization with server information
- ACL (Access Control Lists) setup
- Service management and hardening

### Improvements

- Refactored SSH configuration handling to prevent include directive loops
- Enhanced error handling across all modules
- Improved package installation logic with distribution family detection
- Updated template system using importlib.resources for better maintainability
- Streamlined deployment scripts with better OS detection

### Bug Fixes

- SSH bastion connection issues for unencrypted SSH key files
- SSH port retrieval from server configuration
- Template path resolution using importlib.resources
- Package installation compatibility across different Linux distributions
- Service restart logic in security hardening modules

### Security Enhancements

- Enhanced SSH hardening with multiple security options
- Kernel parameter hardening for improved system security
- Firewall configuration with logging and rate limiting
- Malware detection and prevention tools integration
- System auditing and logging improvements

## [0.2.0] - 2025-04-16

### Features

- Initial Jinn API integration for dynamic inventory management
- Basic security deployment modules
- Alpine Linux support alongside Ubuntu
- Vagrant-based testing environment
- SSH configuration management
- Template system for configuration files

### Improvements

- Restructured project layout with separate security modules
- Enhanced inventory management with API integration

## [0.1.0] - 2024-10-14

### Features

- Initial project setup with PyInfra integration
- Basic Netdata deployment functionality
- Core project structure and packaging
- MIT License
- Basic README and documentation

### Infrastructure

- PyPI package publishing setup
- Build system configuration with setuptools
- Requirements management
- Git repository initialization

---

## Release Notes

### How to Read This Changelog

- **Features** for new features and capabilities
- **Improvements** for changes in existing functionality  
- **Deprecated** for soon-to-be removed features
- **Removed** for now removed features
- **Bug Fixes** for any bug fixes
- **Security Enhancements** for security-related changes

### Version Numbering

This project follows [Semantic Versioning](https://semver.org/) (SemVer):

- **MAJOR** version when you make incompatible API changes
- **MINOR** version when you add functionality in a backwards compatible manner  
- **PATCH** version when you make backwards compatible bug fixes

### PyPI Releases

All releases are automatically published to [PyPI](https://pypi.org/project/infraninja/) and can be installed via:

```bash
pip install infraninja==<version>
```

For the latest release:

```bash
pip install infraninja
```
