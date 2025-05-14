from pyinfra.context import host
from pyinfra.api.deploy import deploy
from pyinfra.facts.server import LinuxDistribution, Which
from pyinfra.operations import files, openrc, systemd, server, sysvinit, runit
from pyinfra.facts.files import FindInFile

ssh_config = {
    "PermitRootLogin": "prohibit-password",
    "PasswordAuthentication": "no",
    "X11Forwarding": "no",
}


@deploy("SSH Hardening")
def ssh_hardening():
    config_changed = False

    for option, value in ssh_config.items():
        # Find existing lines first
        matching_lines = host.get_fact(
            FindInFile, path="/etc/ssh/sshd_config", pattern=rf"^#?\s*{option}\s+.*$"
        )

        if matching_lines:
            change = files.replace(
                name=f"Configure SSH: {option}",
                path="/etc/ssh/sshd_config",
                text=f"^{matching_lines[0]}$",
                replace=f"{option} {value}",
                _ignore_errors=True,
            )
            if change.changed:
                config_changed = True
        else:
            # Append if not found
            files.line(
                path="/etc/ssh/sshd_config", line=f"{option} {value}", present=True
            )
            config_changed = True

    if config_changed:
        # Get detailed distribution information
        distro = host.get_fact(LinuxDistribution)
        distro_name = distro.get("name", "")
        if distro_name:
            distro_name = distro_name.lower()

        # Determine the init system and SSH service name
        ssh_service = "sshd"  # Default service name

        if distro_name and ("ubuntu" in distro_name or "debian" in distro_name):
            ssh_service = "ssh"

        # Check which init system is in use and restart SSH accordingly
        if host.get_fact(Which, command="systemctl"):
            systemd.daemon_reload()
            systemd.service(
                name="Restart SSH",
                service=ssh_service,
                running=True,
                restarted=True,
            )
        elif host.get_fact(Which, command="rc-service"):
            openrc.service(
                name="Restart SSH",
                service=ssh_service,
                running=True,
                restarted=True,
            )
        elif host.get_fact(Which, command="sv"):  # (Void Linux)
            runit.service(
            service=ssh_service,
            running=True,
            restarted=True,
            )
        elif host.get_fact(Which, command="service") or any(
            host.get_fact(Which, command=cmd)
            for cmd in ["update-rc.d", "chkconfig", "rc-update"]
        ):
            sysvinit.service(
                name="Restart SSH with SysV init",
                service=ssh_service,
                running=True,
                restarted=True,
            )
        else:
            # Fallback to a direct restart attempt
            server.shell(
                name="Restart SSH (generic)",
                commands=[
                    f"/etc/init.d/{ssh_service} restart 2>/dev/null || "
                    f"systemctl restart {ssh_service} 2>/dev/null || "
                    f"rc-service {ssh_service} restart 2>/dev/null"
                ],
                _ignore_errors=True,
            )
