from pyinfra import config, host
from pyinfra.api import deploy
from pyinfra.operations import files, systemd, openrc

config.SUDO = True

ssh_config = {
    "PermitRootLogin": "prohibit-password",
    "PasswordAuthentication": "no",
    "X11Forwarding": "no",
}


@deploy("SSH Hardening")
def ssh_hardening():
    config_changed = False

    for option, value in ssh_config.items():
        change = files.replace(
            name=f"Configure SSH: {option}",
            path="/etc/ssh/sshd_config",
            text=f"^{option} .*$",
            replace=f"{option.removeprefix('#')} {value}",
        )
        if change.changed:
            config_changed = True

    if config_changed:
        init_systems = host.get_fact("init_systems")

        if "systemd" in init_systems:
            systemd.daemon_reload()
            systemd.service(
                name="Restart SSH",
                service="ssh",
                running=True,
                restarted=True,
            )
        elif "openrc" in init_systems:
            openrc.service(
                name="Restart SSH",
                service="sshd",
                running=True,
                restarted=True,
            )
