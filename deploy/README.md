# InfraNinja Test Environment

This directory contains the test environment for the InfraNinja project, providing virtual machines and deployment scripts for testing security configurations and infrastructure automation using Vagrant and PyInfra. The deployment process integrates with APIs to fetch server details dynamically using the Jinn API and Coolify integration.

---

## Files Overview

### `Vagrantfile`

- **Purpose**: Defines the configuration for two virtual machines (VMs) managed by Vagrant
  - **Ubuntu VM**: Ubuntu 22.04 LTS with 1024 MB of memory and 2 CPU cores
  - **Alpine VM**: Alpine 3.19 with 512 MB of memory and 1 CPU core
- **Usage**: Sets up local VMs for testing deployment scripts and security configurations

### `jinn.py`

- **Purpose**: Example inventory script using the Jinn API for dynamic server discovery
- **Details**: Demonstrates how to integrate with the Jinn API for automated inventory management

### `deploy.py`

- **Purpose**: Example deployment script using PyInfra to test security configurations  
- **Details**: Shows how to import and execute security modules from the `infraninja` package

---

## Setting Up the Environment

### Prerequisites

1. **Install Vagrant**: Download and install Vagrant from the [official website](https://www.vagrantup.com/downloads)
2. **Install VirtualBox**: Required as the VM provider for testing
3. **Install Python & Dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

### Environment Variables

Environment variables are not used by the inventory files. Instead, you configure the API connections directly in the inventory scripts by instantiating the classes with the appropriate parameters.

### Initializing the Test Environment

1. **Start the Virtual Machines**:

   ```bash
   vagrant up
   ```

2. **Access the VMs**:

   ```bash
   vagrant ssh ubuntu   # For Ubuntu VM
   vagrant ssh alpine   # For Alpine VM
   ```

## Running the Tests

### Basic VM Testing

To execute test deployments on the local VMs:

1. **Start the Virtual Machines**:

   ```bash
   vagrant up
   ```

2. **Run Basic Security Test on Ubuntu**:

   ```bash
   pyinfra @vagrant/ubuntu deploy.py
   ```

3. **Run Basic Security Test on Alpine**:

   ```bash
   pyinfra @vagrant/alpine deploy.py
   ```

### Dynamic Inventory Testing

#### Using Jinn API

1. **Configure the Jinn inventory script** (`jinn.py`):

   Edit the `jinn.py` file to configure your API connection:

   ```python
   from infraninja.inventory.jinn import Jinn

   jinn = Jinn(
       api_url="https://jinn-api.kalvad.cloud",
       api_key="your-access-key",
       ssh_key_path="~/.ssh/id_rsa",
       groups=["production", "staging"],  # Optional: filter by groups
       tags=["web", "database"],          # Optional: filter by tags
   )
   hosts = jinn.get_servers()
   ```

2. **Run with Jinn inventory**:

   ```bash
   pyinfra jinn.py deploy.py
   ```

#### Using Coolify API

1. **Configure the Coolify inventory script** (`coolify.py`):

   Create or edit the `coolify.py` file:

   ```python
   from infraninja.inventory.coolify import Coolify

   coolify = Coolify(
       api_url="https://coolify.example.com/api",
       api_key="your-coolify-api-key",
       ssh_key_path="~/.ssh/id_rsa",
       tags=["prod", "staging"],  # Optional: filter by tags
   )
   hosts = coolify.get_servers()
   ```

2. **Run with Coolify inventory**:

   ```bash
   pyinfra coolify.py deploy.py
   ```

### VM Access

Access the VMs directly for testing:

```bash
vagrant ssh ubuntu   # For Ubuntu VM
vagrant ssh alpine   # For Alpine VM
```

### Creating Custom Deployment Scripts

You can extend the deployment scripts to include additional security functions:

#### 1. Basic Security Deployment

```python
from pyinfra.api import deploy
from infraninja.security.common.ssh_hardening import ssh_hardening
from infraninja.security.common.kernel_hardening import kernel_hardening

@deploy("Basic Security Setup")
def basic_security():
    # SSH hardening
    ssh_hardening()
    
    # Kernel security hardening
    kernel_hardening()
```

#### 2. OS-Specific Deployments

```python
from pyinfra import host
from pyinfra.facts.server import LinuxName
from pyinfra.api import deploy

@deploy("OS-Specific Security Setup")
def os_specific_security():
    os_name = host.get_fact(LinuxName)
    
    if "ubuntu" in os_name.lower():
        from infraninja.security.ubuntu.fail2ban_setup import fail2ban_setup
        from infraninja.security.ubuntu.install_tools import install_security_tools
        
        install_security_tools()
        fail2ban_setup()
        
    elif "alpine" in os_name.lower():
        from infraninja.security.alpine.fail2ban_setup import fail2ban_setup_alpine
        from infraninja.security.alpine.install_tools import install_security_tools
        
        install_security_tools()
        fail2ban_setup_alpine()
```

#### 3. Comprehensive Security Suite

```python
@deploy("Comprehensive Security Hardening")
def comprehensive_security():
    # Common security measures
    ssh_hardening(_sudo=True)
    kernel_hardening(_sudo=True)
    
    # Network security
    from infraninja.security.common.nftables_setup import nftables_setup
    nftables_setup(_sudo=True)
    
    # Malware detection
    from infraninja.security.common.chkrootkit_setup import chkrootkit_setup
    chkrootkit_setup(_sudo=True)
    
    # System auditing
    from infraninja.security.common.auditd_setup import auditd_setup
    auditd_setup(_sudo=True)
```

#### 4. Infrastructure Monitoring

```python
@deploy("Infrastructure Monitoring")
def monitoring_setup():
    # Deploy Netdata
    from infraninja.netdata import deploy_netdata
    deploy_netdata()
    
    # Setup custom MOTD
    from infraninja.utils.motd import setup_motd
    setup_motd()
```

### Expected Behavior

When running deployments, the system will:

- **API Integration**: Authenticate with Jinn or Coolify APIs to fetch server configurations
- **SSH Configuration**: Automatically generate and update SSH configurations for seamless access
- **Security Hardening**: Deploy comprehensive security configurations based on the target OS
- **Monitoring Setup**: Configure monitoring tools like Netdata for system oversight
- **Firewall Configuration**: Set up and configure firewalls (iptables/nftables) with appropriate rules
- **Malware Protection**: Install and configure antivirus and rootkit detection tools
- **System Auditing**: Enable comprehensive system auditing and logging

## Troubleshooting

### API Connection Issues

- **Jinn API Problems**:
  - Verify your `JINN_API_URL` and `JINN_ACCESS_KEY` are correct
  - Check network connectivity to the API endpoint
  - Ensure your API key has proper permissions
  - Test API connectivity: `curl -H "Authorization: Bearer $JINN_ACCESS_KEY" $JINN_API_URL/health`

- **Coolify API Problems**:
  - Verify your `COOLIFY_API_URL` and `COOLIFY_API_KEY` are correct
  - Ensure the Coolify instance is accessible
  - Check API endpoint format (should include `/api` if required)
  - Verify API key permissions in Coolify dashboard

### SSH Issues

- **Key Permission Errors**:
  - Ensure SSH key has correct permissions: `chmod 600 ~/.ssh/id_rsa`
  - Verify SSH key is in the correct format (PEM, OpenSSH)
  - Check SSH key is properly added to target servers

- **Connection Failures**:
  - Test SSH connectivity manually: `ssh -i ~/.ssh/id_rsa user@hostname`
  - Verify SSH port and user are correct
  - Check if SSH service is running on target servers
  - Ensure firewall allows SSH connections

### Virtual Machine Problems

- **VM Startup Issues**:
  - Check VirtualBox/VMware is properly installed
  - Verify sufficient system resources (RAM, CPU)
  - Run `vagrant status` to check VM state
  - Use `vagrant destroy && vagrant up` to rebuild VMs

- **VM Connectivity**:
  - Ensure VMs have network connectivity
  - Check Vagrant networking configuration
  - Verify VM SSH keys are properly configured

### Deployment Failures

- **Package Installation Errors**:
  - Update package repositories first
  - Check internet connectivity on target systems
  - Verify target OS is supported (Ubuntu 20.04+, Alpine 3.16+)
  - Check for conflicting packages or services

- **Permission Errors**:
  - Use `_sudo=True` parameter for operations requiring root access
  - Verify user has sudo privileges
  - Check sudoers configuration if needed

- **Service Configuration Issues**:
  - Check service logs: `journalctl -u service-name`
  - Verify configuration file syntax
  - Test configuration files before applying
  - Check for port conflicts

### Debug Mode

Enable verbose output for troubleshooting:

```bash
# Enable PyInfra debug mode
pyinfra --debug inventory.py deploy.py

# Enable verbose SSH output
pyinfra --ssh-user root --ssh-password password --debug @vagrant/ubuntu deploy.py -v
```

### Getting Help

- **Documentation**: Refer to the main [InfraNinja README](../README.md)
- **Issues**: Report problems on [GitHub Issues](https://github.com/KalvadTech/infraninja/issues)
- **Examples**: Check the `tests/` directory for working examples
- **Community**: Join discussions in GitHub Discussions
