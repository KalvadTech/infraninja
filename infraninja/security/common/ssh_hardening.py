from pyinfra import host
from pyinfra.api import deploy
from pyinfra.facts.server import LinuxName
from pyinfra.operations import files, openrc, systemd
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
        init_systems = host.get_fact(LinuxName)

        if "Ubuntu" in init_systems:
            systemd.daemon_reload()
            systemd.service(
                name="Restart SSH",
                service="ssh",
                running=True,
                restarted=True,
            )
        elif "Alpine" in init_systems:
            openrc.service(
                name="Restart SSH",
                service="sshd",
                running=True,
                restarted=True,
            )
