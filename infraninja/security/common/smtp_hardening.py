from importlib.resources import files as resource_files

from pyinfra.api.deploy import deploy
from pyinfra.context import host
from pyinfra.facts.server import Command
from pyinfra.operations import files, server


@deploy("SMTP Hardening")
def smtp_hardening():
    """
    Harden SMTP server configuration for enhanced security.

    Applies security-focused configuration to Postfix SMTP server
    to prevent abuse and enhance mail security. Updates main.cf
    with hardened settings and restarts the service.

    .. code:: python

        from infraninja.security.common.smtp_hardening import smtp_hardening
        smtp_hardening()

    :returns: None if successful, early return if Postfix not installed
    :rtype: None

    .. note::
        This function only runs if Postfix is installed on the system.
        It will not attempt to install Postfix if it's missing.
    """
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
