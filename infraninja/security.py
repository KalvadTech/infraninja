from pyinfra.operations import apt, apk, files, server, systemd, openrc
from pyinfra import host

@deploy('Harden SSH and Security Setup')
def security_setup():
    os = host.fact.linux_name
ssh_config = {
    "PermitRootLogin": "prohibit-password",
    "PasswordAuthentication": "no",
    "X11Forwarding": "no",
}

    # Harden SSH
    for option, value in ssh_config.items():
        files.line(
            name=f"Configure SSH: {option}",
            path="/etc/ssh/sshd_config",
            line=f"{option} {value}",
            sudo=True,
        )

    # OS-specific security tools
    if os == 'Ubuntu':
        apt.packages(name="Install security tools", packages=["fail2ban", "ufw"], sudo=True)
        systemd.service(name="Enable Fail2Ban", service="fail2ban", running=True, enabled=True)
    elif os == 'Alpine':
        apk.packages(name="Install security tools", packages=["fail2ban", "iptables"], sudo=True)
        openrc.service(name="Enable Fail2Ban", service="fail2ban", running=True, enabled=True)
