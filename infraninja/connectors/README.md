# PSsh Connector for Infraninja

A parallel SSH connector that provides pssh-like functionality for running pyinfra deployments across multiple hosts simultaneously.

## Features

- **Parallel Execution**: Run deployments on multiple hosts concurrently with configurable parallelism
- **Host Filtering**: Filter hosts by groups, tags, or specific hostnames
- **Failure Handling**: Configurable retry logic, fail-fast options, and graceful error handling
- **Progress Tracking**: Real-time execution tracking with detailed result aggregation
- **SSH Configuration**: Support for SSH config files, custom keys, users, and sudo options
- **Result Export**: Export detailed execution results to JSON for analysis
- **Timeout Management**: Per-host timeout controls to prevent hanging operations

## Quick Start

```python
from infraninja.inventory.jinn import Jinn
from infraninja.connectors.pssh import PSshConnector

# Get hosts from inventory
jinn = Jinn(api_url="https://your-api.com", api_key="your_key")
hosts = jinn.get_servers()

# Initialize connector
connector = PSshConnector(
    hosts=hosts,
    max_parallel=5,
    timeout=300,
    verbose=True
)

# Create a simple deployment script
with open('/tmp/deploy.py', 'w') as f:
    f.write("""
from pyinfra.operations import server, apt

apt.update(name="Update packages")
apt.packages(name="Install tools", packages=["htop", "vim"])
""")

# Execute across all hosts
result = connector.execute('/tmp/deploy.py')

# View summary
print(connector.get_summary())
```

## Installation

The PSsh connector is part of infraninja and requires:

```bash
pip install pyinfra
```

## Usage

### Basic Usage

```python
from infraninja.connectors.pssh import PSshConnector

# Initialize with host list
hosts = [
    ("web01", {"ssh_hostname": "192.168.1.10", "group_name": "web-servers"}),
    ("web02", {"ssh_hostname": "192.168.1.11", "group_name": "web-servers"}),
    ("db01", {"ssh_hostname": "192.168.1.20", "group_name": "database"})
]

connector = PSshConnector(hosts=hosts)

# Execute deployment script
result = connector.execute("/path/to/deployment.py")
```

### Host Filtering

Filter hosts before execution:

```python
# Filter by groups
web_hosts = connector.filter_hosts(groups=["web-servers"])

# Filter by tags
prod_hosts = connector.filter_hosts(tags=["production"])

# Exclude maintenance hosts
active_hosts = connector.filter_hosts(exclude_tags=["maintenance"])

# Complex filtering
filtered = connector.filter_hosts(
    groups=["web-servers"],
    tags=["production"],
    exclude_tags=["maintenance", "upgrading"]
)

# Execute on filtered hosts
result = connector.execute(
    "/path/to/deployment.py",
    hosts_filter={"groups": ["web-servers"]}
)
```

### Configuration Options

```python
connector = PSshConnector(
    hosts=hosts,
    max_parallel=10,           # Run on 10 hosts simultaneously
    timeout=600,               # 10 minute timeout per host
    retry_count=2,             # Retry failed hosts twice
    retry_delay=10,            # Wait 10 seconds between retries
    fail_fast=False,           # Continue even if hosts fail
    continue_on_error=True,    # Don't stop on first error
    ssh_config_file="/etc/ssh/config",  # Use custom SSH config
    ssh_key="/path/to/key",    # Use specific SSH key
    ssh_user="admin",          # Override SSH username
    sudo=True,                 # Use sudo for operations
    sudo_user="root",          # Sudo to root user
    verbose=True               # Enable debug logging
)
```

### Error Handling

```python
result = connector.execute("/path/to/deployment.py")

if result.failed_hosts > 0:
    print(f"Warning: {result.failed_hosts} hosts failed!")
    
    for hostname, host_result in result.host_results.items():
        if host_result.status.value == "failed":
            print(f"{hostname}: {', '.join(host_result.errors)}")

# Check success rate
if result.success_rate < 90.0:
    print("Deployment had significant failures")
```

### Result Analysis

```python
# Get formatted summary
print(connector.get_summary())

# Export detailed results
connector.export_results("/tmp/deployment_results.json")

# Access individual host results
for hostname, result in connector.host_results.items():
    print(f"{hostname}: {result.status.value} ({result.duration:.2f}s)")
    if result.errors:
        for error in result.errors:
            print(f"  Error: {error}")
```

## Deployment Scripts

The connector executes standard pyinfra deployment scripts. Here are some examples:

### Basic System Updates

```python
# update_systems.py
from pyinfra.operations import apt, server

# Update package lists
apt.update(name="Update apt cache")

# Upgrade all packages
apt.upgrade(name="Upgrade packages")

# Reboot if required
server.reboot(name="Reboot if needed", reboot_timeout=300)
```

### Security Hardening

```python
# security_hardening.py
from pyinfra.operations import apt, server, files

# Install security tools
apt.packages(
    name="Install security tools",
    packages=["fail2ban", "ufw", "aide", "rkhunter"]
)

# Configure firewall
server.shell(
    name="Configure UFW",
    commands=[
        "ufw --force reset",
        "ufw default deny incoming",
        "ufw default allow outgoing", 
        "ufw allow ssh",
        "ufw --force enable"
    ]
)

# Start services
server.service(
    name="Enable fail2ban",
    service="fail2ban",
    running=True,
    enabled=True
)
```

### Application Deployment

```python
# deploy_app.py
from pyinfra.operations import apt, server, files, git

# Install dependencies
apt.packages(
    name="Install app dependencies",
    packages=["python3", "python3-pip", "nginx"]
)

# Clone application
git.repo(
    name="Clone application",
    src="https://github.com/user/app.git",
    dest="/opt/myapp"
)

# Install Python dependencies
server.shell(
    name="Install pip requirements",
    commands=["cd /opt/myapp && pip3 install -r requirements.txt"]
)

# Configure nginx
files.template(
    name="Configure nginx",
    src="nginx.conf.j2",
    dest="/etc/nginx/sites-available/myapp"
)

# Enable site
server.shell(
    name="Enable nginx site",
    commands=[
        "ln -sf /etc/nginx/sites-available/myapp /etc/nginx/sites-enabled/",
        "systemctl reload nginx"
    ]
)
```

## Integration with Infraninja

The PSsh connector integrates seamlessly with infraninja's inventory and security modules:

```python
from infraninja.inventory.jinn import Jinn
from infraninja.connectors.pssh import PSshConnector

# Get hosts from Jinn inventory
jinn = Jinn(api_url="https://api.example.com", api_key="key")
hosts = jinn.get_servers()

# Filter for production web servers
connector = PSshConnector(hosts=hosts)
web_hosts = connector.filter_hosts(
    groups=["web-servers"],
    tags=["production"]
)

# Deploy security hardening
result = connector.execute(
    "infraninja/security/common/ssh_hardening.py",
    hosts_filter={"groups": ["web-servers"], "tags": ["production"]}
)
```

## Performance Considerations

- **Parallelism**: Start with `max_parallel=5-10` and adjust based on your infrastructure
- **Timeouts**: Set appropriate timeouts for your deployment complexity
- **SSH Configuration**: Use SSH connection multiplexing for better performance
- **Logging**: Disable verbose logging in production for better performance

## Troubleshooting

### Common Issues

1. **SSH Connection Failures**
   ```python
   # Use SSH config file for complex setups
   connector = PSshConnector(
       hosts=hosts,
       ssh_config_file="/etc/ssh/config",
       ssh_key="/path/to/key"
   )
   ```

2. **Timeout Issues**
   ```python
   # Increase timeouts for slow operations
   connector = PSshConnector(
       hosts=hosts,
       timeout=1200,  # 20 minutes
       retry_count=1
   )
   ```

3. **Permission Errors**
   ```python
   # Ensure proper sudo configuration
   connector = PSshConnector(
       hosts=hosts,
       sudo=True,
       sudo_user="root"
   )
   ```

### Debug Mode

Enable verbose logging to troubleshoot issues:

```python
connector = PSshConnector(hosts=hosts, verbose=True)
```

This will show detailed SSH connection info, command execution, and error details.

## Examples

See `examples/pssh_example.py` for comprehensive usage examples including:

- Basic deployment workflows
- Security hardening automation
- Advanced host filtering
- Error handling patterns
- Result analysis and reporting

## API Reference

### PSshConnector Class

#### Constructor Parameters

- `hosts`: List of (hostname, host_data) tuples
- `max_parallel`: Maximum concurrent host operations (default: 10)
- `timeout`: Per-host timeout in seconds (default: 300)
- `retry_count`: Number of retries for failures (default: 0)
- `retry_delay`: Delay between retries in seconds (default: 5)
- `fail_fast`: Stop on first failure (default: False)
- `continue_on_error`: Continue with remaining hosts on error (default: True)
- `ssh_config_file`: Path to SSH config file (optional)
- `ssh_key`: Path to SSH private key (optional)
- `ssh_user`: SSH username override (optional)
- `sudo`: Use sudo for operations (default: True)
- `sudo_user`: User to sudo to (default: "root")
- `verbose`: Enable debug logging (default: False)

#### Methods

- `filter_hosts(**criteria)`: Filter hosts by groups, tags, or hostnames
- `execute(deployment_script, hosts_filter=None, *args)`: Execute deployment script
- `get_summary()`: Get formatted execution summary
- `export_results(output_file)`: Export results to JSON file

### Result Classes

#### HostResult

Contains per-host execution details:

- `hostname`: Target hostname
- `status`: ExecutionStatus enum value
- `operations_count`: Number of operations executed
- `success_count`: Number of successful operations  
- `error_count`: Number of failed operations
- `duration`: Execution time in seconds
- `errors`: List of error messages
- `output`: Command output lines
- `return_code`: Process exit code

#### DeploymentResult

Contains aggregated results across all hosts:

- `total_hosts`: Total number of target hosts
- `successful_hosts`: Number of successful deployments
- `failed_hosts`: Number of failed deployments
- `skipped_hosts`: Number of skipped hosts
- `timeout_hosts`: Number of timed-out hosts
- `total_duration`: Total execution time
- `host_results`: Dictionary of per-host results
- `success_rate`: Success percentage (property)

## License

This module is part of infraninja and follows the same license terms.