# deploy/security.py

from pyinfra import host
from pyinfra.operations import apt, apk, server, files, openrc, systemd


if host.fact.linux_name == 'Ubuntu':
    # Update and upgrade packages
    apt.update(name="Update package lists", sudo=True)
    apt.upgrade(name="Upgrade all packages", sudo=True)

    # Install security tools
    apt.packages(
        name="Install security tools",
        packages=[
            "fail2ban", "ufw", "clamav", "clamav-daemon",
            "lynis", "chkrootkit", "auditd", "apparmor"
        ],
        sudo=True,
    )

    # Configure UFW Firewall
    server.shell(
        name="Enable UFW and allow SSH",
        commands=[
            "ufw allow OpenSSH",
            "ufw enable",
        ],
        sudo=True,
    )

    # Start and enable services
    services = ["fail2ban", "clamav-freshclam", "auditd", "apparmor"]
    for service in services:
        systemd.service(
            name=f"Enable and start {service}",
            service=service,
            running=True,
            enabled=True,
            sudo=True,
        )

    server.shell(name="Enable positive source/destination address checks", commands=["sysctl -w net.ipv4.conf.all.rp_filter=1"])


elif host.fact.linux_name == 'Alpine':
    # Update and upgrade packages
    apk.update(name="Update package lists", sudo=True)
    apk.upgrade(name="Upgrade all packages", sudo=True)

    # Install security tools
    apk.packages(
        name="Install security tools",
        packages=[
            "fail2ban", "iptables", "clamav", "clamav-daemon",
            "lynis", "chkrootkit", "audit"
        ],
        sudo=True,
    )

    # T1.4.1: Disable removable media auto-run and enforce encryption
    files.line(
        name="Disable auto-run for removable media",
        path="/etc/apk/repositories",
        line="noauto"
    )
  
    # Configure iptables Firewall
    server.shell(
        name="Set up iptables to allow SSH",
        commands=[
            "iptables -A INPUT -p tcp --dport 22 -j ACCEPT",
            "iptables -A INPUT -j DROP",
            "rc-update add iptables",
            "rc-service iptables save",
        ],
        sudo=True,
    )

    # Start and enable services
    services = ["fail2ban", "clamav-freshclam", "auditd"]
    for service in services:
        openrc.service(
            name=f"Enable and start {service}",
            service=service,
            running=True,
            enabled=True,
            sudo=True,
        )

# Common configurations for all servers

# Disable root password login
files.line(
    name="Disable root password",
    path="/etc/shadow",
    line="root:*:",
    replace="^root:.*",
    sudo=True,
)

