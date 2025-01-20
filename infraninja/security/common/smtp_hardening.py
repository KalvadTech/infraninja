from pyinfra.api import deploy
from pyinfra.operations import files, server


@deploy("SMTP Hardening")
def smtp_hardening():
    # Ensure the Postfix configuration has the correct content

    files.template(
        name="Configure Postfix security settings",
        src="../infraninja/security/templates/postfix_main.cf.j2",
        dest="/etc/postfix/main.cf",
        user="root",
        group="root",
        mode="644",
    )

    # Restart postfix to apply changes
    server.service(
        name="Restart postfix",
        service="postfix",
        running=True,
        restarted=True,
        _ignore_errors=True,
    )
