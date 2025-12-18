"""Full server setup composite action."""

from .base import Composite
from .netdata import Netdata
from .ssh_hardening import SSHHardening
from .update_and_upgrade import UpdateAndUpgrade


class FullSetup(Composite):
    """
    Complete server setup with updates, hardening, and monitoring.

    Executes the following actions in order:
    1. UpdateAndUpgrade - Update system packages
    2. SSHHardening - Harden SSH configuration
    3. Netdata - Deploy monitoring

    Example:
        .. code:: python

            from infraninja.actions.full_setup import FullSetup

            # Execute with defaults
            setup = FullSetup()
            result = setup.execute()

            # Execute with custom params for sub-actions
            result = setup.execute(
                SSHHardening={"permit_root_login": "no"},
                Netdata={"claim_token": "your-token", "claim_rooms": "your-room"},
            )

            # Check results
            if result.success:
                print("Setup completed successfully")
            for action_result in result.results:
                print(f"  {action_result.action}: {'OK' if action_result.success else 'FAILED'}")
    """

    slug = "full-setup"
    name = {
        "en": "Full Server Setup",
        "ar": "إعداد الخادم الكامل",
        "fr": "Configuration complète du serveur",
    }
    tags = ["setup", "hardening", "monitoring", "composite"]
    category = "setup"
    color = "#9B59B6"
    logo = "fa-server"
    description = {
        "en": "Complete server setup including system updates, SSH hardening, and Netdata monitoring",
        "ar": "إعداد الخادم الكامل بما في ذلك تحديثات النظام وتقوية SSH ومراقبة Netdata",
        "fr": "Configuration complète du serveur incluant mises à jour, durcissement SSH et surveillance Netdata",
    }

    actions = [
        UpdateAndUpgrade,
        SSHHardening,
        Netdata,
    ]
