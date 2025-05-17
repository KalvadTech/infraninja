from importlib.resources import files as resource_files
from pyinfra.api.deploy import deploy
from pyinfra.operations import files, server
from pyinfra.context import host
from pyinfra.facts.server import Command


@deploy("SMTP Hardening")
def smtp_hardening():
    # Check if postfix is installed using host facts and Command
    postfix_exists = host.get_fact(Command, command="command -v postfix")
    if not postfix_exists:
        return

    # Get template path using importlib.resources
    template_path = resource_files("infraninja.security.templates").joinpath(
        "postfix_main.cf.j2"
    )

    # Ensure the Postfix configuration has the correct content
    files.template(
        name="Configure Postfix security settings",
        src=str(template_path),
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
