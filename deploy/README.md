# InfraNinja Test Project

This project contains configuration and deployment scripts for managing virtual machines and deploying updates using Vagrant and Pyinfra. The deployment process integrates with an API to fetch server details dynamically using the Jinn API.

---

## Files Overview

### `Vagrantfile`

- **Purpose**: Defines the configuration for two virtual machines (VMs) managed by Vagrant.
  - **Ubuntu VM**: Ubuntu 22.04 LTS with 1024 MB of memory and 2 CPU cores.
  - **Alpine VM**: Alpine 3.19 with 512 MB of memory and 1 CPU core.
- **Usage**: Sets up local VMs for testing deployment scripts and security configurations.

### `test_deploy.py`

- **Purpose**: Example deployment script using Pyinfra to test security configurations.
- **Details**: Imports and executes security modules from the `infraninja` package.

---

## Setting Up the Environment

### Prerequisites

1. **Install Vagrant**: Download and install Vagrant from the official [Vagrant website](https://www.vagrantup.com/downloads).
2. **Install VirtualBox**: Required as the VM provider for testing.
3. **Install Python & Dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

### Environment Variables

The following environment variables are used:

- `JINN_API_URL`: Base URL for the Jinn API
- `JINN_ACCESS_KEY`: Your API access key
- `JINN_GROUPS`: (Optional) Preselect server groups
- `JINN_TAGS`: (Optional) Preselect server tags
- `SSH_KEY_PATH`: (Optional) Path to your SSH private key

### Initializing the Test Environment

1. **Set Up Environment Variables**:

   ```bash
   export JINN_API_URL="https://your-api-url"
   export JINN_ACCESS_KEY="your-access-key"
   ```

2. **Start the Virtual Machines**:

   ```bash
   vagrant up
   ```

3. **Access the VMs**:

   ```bash
   vagrant ssh ubuntu   # For Ubuntu VM
   vagrant ssh alpine   # For Alpine VM
   ```

## Running the Tests

To execute the test deployment:

1. **Run the Basic Test**:

   ```bash
   pyinfra @vagrant/ubuntu test_deploy.py
   ```

   or

   ```bash
   pyinfra @vagrant/alpine test_deploy.py
   ```

2. **With Dynamic Inventory**:

   ```bash
   pyinfra inventory.py test_deploy.py
   ```

### Adding Security Functions

You can extend `test_deploy.py` to include additional security functions:

1. **Basic Function Addition**:

   ```python
   from pyinfra.api import deploy
   from infraninja.security.common.ssh_hardening import ssh_hardening
   from infraninja.security.common.kernel_hardening import kernel_hardening

   @deploy("Test Security Setup")
   def test_deploy():
       # Add functions to be executed in order
       ssh_hardening()
       kernel_hardening()
   ```

2. **OS-Specific Deployments**:

   ```python
   from pyinfra import host
   from pyinfra.facts.server import LinuxName

   @deploy("Test Security Setup")
   def test_deploy():
       os = host.get_fact(LinuxName)
       
       if os == "Ubuntu":
           from infraninja.security.ubuntu.fail2ban_setup import fail2ban_setup
           fail2ban_setup()
       elif os == "Alpine":
           from infraninja.security.alpine.fail2ban_setup import fail2ban_setup_alpine
           fail2ban_setup_alpine()
   ```

3. **With Sudo Privileges**:

   ```python
   @deploy("Test Security Setup")
   def test_deploy():
       ssh_hardening(_sudo=True)
       kernel_hardening(_sudo=True)
   ```

### Expected Behavior

- The script will authenticate with the Jinn API
- It will fetch server configurations and SSH settings
- Deploy security configurations based on the target OS (Ubuntu/Alpine)
- Set up monitoring, firewalls, and security tools

## Troubleshooting

- **API Connection Issues**:
  - Verify your `JINN_API_URL` and `JINN_ACCESS_KEY` are correct
  - Check your network connection and API endpoint availability

- **SSH Issues**:
  - Ensure your SSH key has correct permissions (600)
  - Verify the SSH key is properly added to the target servers

- **VM Problems**:
  - Run `vagrant status` to check VM state
  - Use `vagrant destroy` and `vagrant up` to rebuild VMs if needed
  - Check VirtualBox/VMware settings if VMs fail to start

For more detailed information about available security modules and configurations,
please refer to the main [InfraNinja README](../README.md).
