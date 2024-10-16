from pyinfra import host, config
from pyinfra.operations import apt, apk, files, server, openrc, systemd
from pyinfra.facts.server import LinuxName

os = host.get_fact(LinuxName)

ssh_config = {
    "PermitRootLogin": "no",
    "PasswordAuthentication": "no",
    "X11Forwarding": "no",
}

config.SUDO = True

# Configure SSH security settings
for option, value in ssh_config.items():
    files.line(
        name=f"Configure SSH setting: {option}",
        path="/etc/ssh/sshd_config",
        line=f"{option} {value}",
    )

# Apply UAE IA controls and server security management
if os == "Alpine":
    
    # Update and upgrade packages
    apk.update(name="Update package lists")
    apk.upgrade(name="Upgrade all packages")

    # Install required security tools
    apk.packages(name="Install security tools", packages=["fail2ban", "clamav", "clamav-daemon", "lynis", "chkrootkit"])

    # Configure services and disable automatic updates
    openrc.service("clamav-freshclam", running=False, enabled=True)
    server.shell(name="Update ClamAV database", commands="freshclam")
    openrc.service("clamav-freshclam", running=True, enabled=True)
    openrc.service("fail2ban", running=True, enabled=True)

    apk.packages(name="Remove unattended-upgrades", packages=["unattended-upgrades"], present=False)
    
    # T1.4.1: Disable removable media auto-run and enforce encryption
    files.line(
        name="Disable auto-run for removable media",
        path="/etc/apk/repositories",
        line="noauto"
    )
    
    server.shell(
        name="Ensure media encryption",
        commands=["cryptsetup luksFormat /dev/sdx"]  # Example: Replace with actual media device
    )

    # T1.2.1: Manage firewall/IDS/IPS devices
    server.shell(
        name="Ensure firewall and IDS/IPS are installed and configured",
        commands=["apk add iptables", "apk add suricata"]  # IDS/IPS example
    )
    openrc.service("iptables", running=True, enabled=True)
    openrc.service("suricata", running=True, enabled=True)  # IDS/IPS service

elif os == "Ubuntu":
    
    # Update and upgrade packages
    apt.update(name="Update package lists")
    apt.upgrade(name="Upgrade all packages")

    # Install required security tools
    apt.packages(name="Install security tools", packages=["fail2ban", "apparmor-utils", "auditd", "clamav", "clamav-daemon", "lynis", "chkrootkit"])

    # T5.4.6: Apply routing controls (Source & Destination Address Checks)
    systemd.service("apparmor", running=True, enabled=True)
    systemd.service("auditd", running=True, enabled=True)
    server.shell(name="Enable positive source/destination address checks", commands=["sysctl -w net.ipv4.conf.all.rp_filter=1"])

    # T3.4.1: Anti-malware configurations and update ClamAV
    systemd.service("clamav-freshclam", running=False, enabled=True)
    server.shell(name="Update ClamAV database", commands="freshclam")
    systemd.service("clamav-freshclam", running=True, enabled=True)
    
    # Configure Fail2Ban for malware detection and logging
    systemd.service("fail2ban", running=True, enabled=True)

    # Disable automatic security updates
    apt.packages(name="Remove unattended-upgrades", packages=["unattended-upgrades"], present=False)
    
    files.line(
        name="Disable automatic updates ",
        path="/etc/apt/apt.conf.d/10periodic",
        line="APT::Periodic::Enable \"0\";",
    )
    
    # T3.6: Audit and Logging - Access logs and privileged operations
    files.line(
        name="Enable logging for privileged operations",
        path="/etc/audit/auditd.conf",
        line="log_format = ENRICHED"
    )

    server.shell(
        name="Start audit logs for user activities",
        commands=["auditctl -e 1"]
    )
    
# T3.6.2: Capture user activities, exceptions, security events, and more
files.line(
    name="Log user activity and system events",
    path="/etc/audit/audit.rules",
    line="-w /etc/passwd -p wa -k identity\n-w /etc/shadow -p wa -k auth\n-w /var/log/auth.log -p wa -k logins"
)

# T3.6.3: Log privileged operations and unauthorized access attempts
files.line(
    name="Log privileged operations and unauthorized access",
    path="/etc/audit/audit.rules",
    line="-w /sbin/ifconfig -p x -k network"
)

# T4.5.1 - T4.5.4: Network components inventory and scanning
server.shell(
    name="Network scanning and port checks",
    commands=["nmap -sS localhost"]
)

# Regular scan and capture version changes in services
server.shell(
    name="Port scan for changes in services",
    commands=["nmap -O localhost > /var/log/nmap.log"]
)

# Backup firewall configurations regularly
server.shell(
    name="Backup firewall configuration",
    commands=["iptables-save > /etc/firewall.backup"]
)
