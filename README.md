# 🥷 InfraNinja ⚡ – Your Stealthy Infrastructure Ninja

Welcome to **InfraNinja**! 🎉 This project contains a comprehensive set of PyInfra deployments 🥷 used by Kalvad teams 🛠️, making them publicly available for everyone via PyPI! 🚀

These ninja-level deployments are designed to simplify infrastructure management and automate common tasks, helping you deploy services, configure security hardening, manage inventory, and more – fast and effortlessly! 💨

## ⚡️ Features

- 🌐 **Automated Deployments**: Deploy services like **Netdata** with precision and ease! 🥷
- 🛡️ **Comprehensive Security**: Advanced security hardening including SSH configuration, kernel hardening, firewall setup, malware detection, and intrusion detection systems
- 🧩 **Modular Architecture**: Reusable deployment modules organized by OS (Ubuntu, Alpine, FreeBSD) and functionality
- 🔗 **Dynamic Inventory**: Integration with **Jinn API** and **Coolify** for automated server inventory management
- 🛠️ **Multi-OS Support**: Compatible with Ubuntu, Alpine Linux, and FreeBSD
- 📋 **Compliance Ready**: Includes UAE IA compliance modules
- 📦 **PyPI Ready**: Available publicly on PyPI for smooth installation

## 🎯 Getting Started

To get started with **InfraNinja**, you can install it directly from PyPI:

```bash
pip install infraninja
```

Then, bring ninja-style automation to your infrastructure with simple imports:

```python
from infraninja.netdata import deploy_netdata
```

## 🚀 Quick Examples

### Basic Netdata Deployment

Deploy **Netdata** monitoring like a ninja 🥷:

```python
from infraninja.netdata import deploy_netdata

deploy_netdata()
```

### Security Hardening

Comprehensive security hardening across different OS types:

```python
# SSH Hardening
from infraninja.security.common.ssh_hardening import ssh_hardening
ssh_hardening()

# Kernel Security
from infraninja.security.common.kernel_hardening import kernel_hardening  
kernel_hardening()

# Firewall Setup (Ubuntu)
from infraninja.security.ubuntu.fail2ban_setup import fail2ban_setup
fail2ban_setup()

# For Alpine Linux
from infraninja.security.alpine.fail2ban_setup import fail2ban_setup_alpine
fail2ban_setup_alpine()
```

### Dynamic Inventory Management

Use Jinn API for dynamic server inventory:

```python
from infraninja.inventory.jinn import Jinn

# Initialize with API credentials
jinn = Jinn(
    api_url="https://jinn-api.kalvad.cloud",
    api_key="your-api-key",
    groups=["production", "web"],
    tags=["nginx", "database"]
)

# Get filtered servers
servers = jinn.get_servers()
```

Use Coolify for container management:

```python
from infraninja.inventory.coolify import Coolify

coolify = Coolify(
    api_url="https://coolify.example.com/api",
    api_key="your-api-key",
    tags=["prod", "staging"]
)

servers = coolify.get_servers()
```

## 📜 Available Deployments

InfraNinja provides comprehensive deployment modules organized by functionality:

### 🔍 Monitoring & Observability

- **Netdata**: Real-time performance monitoring and alerting

### 🛡️ Security Modules

#### Common Security (Cross-Platform)

- **SSH Hardening**: Secure SSH configuration with multiple security options
- **Kernel Hardening**: System-level security hardening
- **Firewall Management**: IPTables and NFTables configuration
- **Network Security**: ARP poisoning protection, secure routing controls
- **Audit & Compliance**: System auditing, UAE IA compliance modules

#### Ubuntu-Specific Security

- **Fail2Ban**: Intrusion prevention system
- **AppArmor**: Mandatory access controls
- **ClamAV**: Antivirus scanning
- **Lynis**: Security auditing tool
- **Suricata**: Network threat detection
- **Chkrootkit**: Rootkit detection

#### Alpine Linux Security

- **Fail2Ban**: Lightweight intrusion prevention
- **ClamAV**: Antivirus for Alpine
- **Suricata**: IDS for Alpine systems
- **Security Tools**: Alpine-optimized security utilities

### 🏗️ Infrastructure Management

- **Jinn Integration**: Dynamic inventory management via Jinn API
- **Coolify Integration**: Container orchestration platform integration
- **SSH Key Management**: Automated SSH key deployment and management
- **System Updates**: Multi-distribution package updates

### 🎛️ Utilities

- **MOTD Customization**: Dynamic message of the day
- **Template System**: Jinja2 templates for configuration files

## 🔧 Development & Testing

Want to add your own ninja-style improvements? Here's how to get started:

### Setup Development Environment

```bash
git clone https://github.com/KalvadTech/infraninja.git
cd infraninja
pip install -r requirements.txt
```

### Testing Your Deployments

Test your deployments locally using PyInfra:

```bash
# Test with local inventory
pyinfra @local your_deployment.py

# Test with dynamic inventory
pyinfra inventory.py your_deployment.py

# Test specific modules
pyinfra @vagrant/ubuntu infraninja.security.common.ssh_hardening
```

### Running the Test Suite

```bash
# Run all tests
pytest

# Run specific test modules
pytest tests/inventory/
pytest tests/common/

# Run with coverage
pytest --cov=infraninja tests/
```

### Building the Package

Create a distribution package:

```bash
python -m build
```

### Using the Test Environment

The project includes a Vagrant-based test environment in the `deploy/` directory:

```bash
cd deploy
vagrant up
vagrant ssh ubuntu   # or vagrant ssh alpine
```

## 📈 Project Status

- **Current Version**: 0.2.1
- **Python Support**: >=3.8
- **License**: MIT License
- **Stability**: Production Ready

## 🤝 Contributions

Contributions are welcome! 🎉 If you spot any bugs 🐛 or have ideas 💡 for cool new features, feel free to open an issue or submit a pull request. The ninja squad would love to collaborate! 🤗

## 👨‍💻 Maintainers

- **Mohammad Abu-khader** 🥷 <mohammad@kalvad.com>
- **Loïc Tosser** 🥷
- The skilled ninja team at **KalvadTech** 🛠️

## 🌟 Community & Support

- **Repository**: [GitHub - KalvadTech/infraninja](https://github.com/KalvadTech/infraninja)
- **Issues**: [Report bugs and request features](https://github.com/KalvadTech/infraninja/issues)
- **Discussions**: Share your ninja deployments with the community

## 📝 License

This project is licensed under the **MIT License**. 📝 Feel free to use it, modify it, and become an infrastructure ninja yourself! 🥷

---

Stay stealthy and keep deploying like a ninja! 🥷💨🚀

---
