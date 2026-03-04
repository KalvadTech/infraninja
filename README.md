# 🥷 InfraNinja ⚡ – Your Stealthy Infrastructure Ninja

Welcome to **InfraNinja**! 🎉 A modern infrastructure automation framework built on PyInfra, providing ninja-level deployments used by Kalvad teams 🛠️ and made publicly available via PyPI! 🚀

InfraNinja simplifies infrastructure management through **Actions** (reusable deployment tasks) and **Inventories** (dynamic server management), helping you deploy services, configure security hardening, and automate common tasks – fast and effortlessly! 💨

## ⚡️ Features

- 🎯 **Action-Based Architecture**: Execute pre-built deployment tasks with rich metadata (SSH hardening, SSH keys, system updates)
- 🌐 **Dynamic Inventories**: Automated server discovery from Jinn API and Coolify with intelligent filtering
- 🛡️ **Comprehensive Security**: 30+ security modules including SSH/kernel hardening, firewall setup (IPTables, NFTables, PF), malware detection (chkrootkit, rkhunter), and intrusion prevention (Fail2Ban, Suricata)
- 🧩 **Multi-OS Support**: Ubuntu, Debian, Alpine Linux, FreeBSD, RHEL, CentOS, Fedora, and Arch Linux
- 🌍 **Multilingual**: Actions support English, Arabic, and French translations
- 📋 **Compliance Ready**: UAE IA compliance modules and security auditing tools (Lynis, Auditd)
- 📦 **PyPI Available**: Install with a simple `pip install infraninja`

## 🎯 Getting Started

**Requirements:** Python 3.10+

Install InfraNinja directly from PyPI:

```bash
pip install infraninja
```

Or using uv:

```bash
uv add infraninja
```

## 🚀 Quick Examples

### Using Actions

Actions are the primary way to execute deployment tasks:

```python
from infraninja import UpdateAndUpgrade

# Update system packages
update = UpdateAndUpgrade()
update.execute()
```

### Using Inventories

Inventories provide dynamic server management from various sources:

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

### Using with PyInfra

Integrate actions with PyInfra deployments:

```python
from pyinfra import inventory
from infraninja import SSHHardening

# Define inventory
inventory.add_host(name="server1", ssh_user="root")

# Execute action across inventory
action = SSHHardening()
action.execute()
```

## 📜 Available Actions

InfraNinja provides comprehensive deployment actions organized by functionality:

### 🛡️ Security & Hardening

- **SSHHardening**: Comprehensive SSH server hardening with security best practices
- **SSHKeys**: SSH key management and deployment

### 🔄 System Maintenance

- **UpdateAndUpgrade**: System package updates across multiple distributions

## 🔐 Security Modules

InfraNinja includes extensive security hardening modules organized by OS:

### Cross-Platform (Common)
- ACL management, ARP poisoning protection, Auditd setup
- Chkrootkit malware detection, Fail2Ban intrusion prevention
- IPTables/NFTables firewall setup, Kernel hardening
- SSH hardening, SMTP hardening, Service management

### FreeBSD
- PF firewall setup, BSM auditing, rkhunter rootkit scanner
- Lynis security auditing, Fail2Ban, SSH hardening

### Alpine Linux
- ClamAV antivirus, Suricata IDS, Lynis auditing
- IPTables setup, Fail2Ban

### Ubuntu/Debian
- AppArmor configuration, ClamAV antivirus, Suricata IDS
- NTP hardening, Routing controls, Lynis auditing

## 🔧 Development & Testing

Want to add your own ninja-style improvements? Here's how to get started:

### Setup Development Environment

```bash
git clone https://github.com/KalvadTech/infraninja.git
cd infraninja
uv sync
```

Or using pip:

```bash
pip install -e ".[dev]"
```

### Testing Your Deployments

Test deployments using the Vagrant-based test environment:

```bash
# Start test VMs
cd deploy
vagrant up

# Test with Ubuntu VM
pyinfra @vagrant/ubuntu deploy.py

# Test with Alpine VM
pyinfra @vagrant/alpine deploy.py

# Test with dynamic inventories
pyinfra jinn.py deploy.py
```

### Running the Test Suite

```bash
# Run all tests
uv run pytest

# Run specific test modules
uv run pytest tests/inventory/
uv run pytest tests/common/

# Run with coverage
uv run pytest --cov=infraninja tests/
```

### Building the Package

Create a distribution package:

```bash
uv build
```

### Using the Test Environment

The project includes a comprehensive test environment in the `deploy/` directory with:
- Vagrant VMs (Ubuntu 22.04, Alpine 3.19)
- Example inventory scripts (Jinn, Coolify)
- Sample deployment scripts

```bash
cd deploy
vagrant up
vagrant ssh ubuntu   # or vagrant ssh alpine
```

See [deploy/README.md](deploy/README.md) for detailed testing instructions.

## 🤝 Contributions

Contributions are welcome! 🎉 If you spot any bugs 🐛 or have ideas 💡 for cool new features, feel free to open an issue or submit a pull request. The ninja squad would love to collaborate! 🤗

## 👨‍💻 Maintainers

- **Mohammad Abu-khader** <mohammad@kalvad.com>
- **Pierre Guillemot** <pierre@kalvad.com>
- **Loïc Tosser** <loic@kalvad.com>
- The skilled ninja team at **KalvadTech** 🛠️

## 🌟 Community & Support

- **Repository**: [GitHub - KalvadTech/infraninja](https://github.com/KalvadTech/infraninja)
- **PyPI Package**: [pypi.org/project/infraninja](https://pypi.org/project/infraninja/)
- **Issues**: [Report bugs and request features](https://github.com/KalvadTech/infraninja/issues)
- **Documentation**: See `docs/` directory and READMEs in subdirectories
- **Changelog**: See [CHANGELOG.md](CHANGELOG.md) for version history

## 📝 License

This project is licensed under the **MIT License**. 📝 Feel free to use it, modify it, and become an infrastructure ninja yourself! 🥷

---

Stay stealthy and keep deploying like a ninja! 🥷💨🚀

---
