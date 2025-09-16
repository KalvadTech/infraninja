# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Refactored SSH key deletion functionality with comprehensive tests for SSHKeyDeleter
- Enhanced test coverage for various security modules

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
