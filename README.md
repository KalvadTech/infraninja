# 🥷 InfraNinja ⚡ – Your Stealthy PyInfra Deployments 📦

Welcome to **InfraNinja**! 🎉 This project contains a set of common PyInfra deployments 🥷 used by all teams at Kalvad 🛠️, making them publicly available for everyone via PyPi! 🚀

These ninja-level deployments are designed to simplify infrastructure management and automate common tasks, helping you set up services like **Netdata**, configure security, and more – fast and effortlessly! 💨

## ⚡️ Features

- 🌐 **Automated Deployments**: Easily deploy services like **Netdata**, NGINX, Docker, and more with ninja-like precision! 🥷
- 🛡️ **Security Focused**: Set up firewalls, harden SSH, and safeguard your servers like a true ninja.
- 🧩 **Modular**: Reusable deployment modules that you can drop into any project.
- 🛠️ **Configurable**: Fine-tune your deployments with flexible templates and configuration files.
- 📦 **PyPi Support**: Available publicly on PyPi for smooth, easy installation in your environments.

## 🎯 Getting Started

To get started with **InfraNinja**, you can install it directly from PyPi:

```bash
pip install infraninja
```

Then, bring ninja-style automation to your infrastructure with simple imports:

```python
from infraninja.netdata import deploy_netdata
```

## 🚀 Example Usage

Here’s how you can deploy **Netdata** like a ninja 🥷:

```python
from infraninja.netdata import deploy_netdata

deploy_netdata()
```

Or, configure **Netdata** settings with precision:

```python
from infraninja.netdata import configure_netdata

configure_netdata()
```

## 📜 Available Deployments

Here are the ninja-level tasks included in this package:

- 🔍 **Netdata**: Keep your systems under surveillance like a true ninja. 🕵️‍♂️
- 🐳 **Docker**: Set up Docker with skill and speed. 🐋
- 🌐 **NGINX**: Deploy NGINX web servers with a ninja's agility. 💨
- 🛡️ **Security**: Lock down your infrastructure with firewall, SSH hardening, and more! 🛡️
- 🎛️ **Custom Templates**: Configure services using templates for ultimate control. 🧩

## 🔧 Development

Want to add your own ninja-style improvements? Here's how:

```bash
git clone https://github.com/kalvad/infraninja.git
cd infraninja
pip install -r requirements.txt
```

You can test your deployments locally using PyInfra:

```bash
pyinfra @local deploy_netdata.py
```

You can create a build:
```bash
python -m build
```

## 📝 License

This project is licensed under the **MIT License**. 📝 Feel free to use it, modify it, and become an infrastructure ninja yourself! 🥷

## 🤝 Contributions

Contributions are welcome! 🎉 If you spot any bugs 🐛 or have ideas 💡 for cool new features, feel free to open an issue or submit a pull request. The ninja squad would love to collaborate! 🤗

## 👨‍💻 Maintainers

- **Loïc Tosser** 🥷
- The skilled ninja team at **Kalvad** 🛠️

---

Stay stealthy and keep deploying like a ninja! 🥷💨🚀

---
