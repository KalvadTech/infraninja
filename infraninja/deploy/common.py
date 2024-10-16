from pyinfra.operations import files

ssh_config = {
    "PermitRootLogin": "prohibit-password",
    "PasswordAuthentication": "no",
    "X11Forwarding": "no",
}


# Apply SSH configurations
for option, value in ssh_config.items():
    files.line(
        name=f"Configure SSH setting: {option}",
        path="/etc/ssh/sshd_config",
        line=f"{option} {value}",
        replace=f"^{option}.*",
        sudo=True,
    )
