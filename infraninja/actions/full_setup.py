"""Full server setup composite action."""

from .base import Composite
from .ssh_hardening import SSHHardening
from .ssh_keys import SSHKeys
from .update_and_upgrade import UpdateAndUpgrade


class FullSetup(Composite):
    """
    Complete server setup with updates, hardening, and key deployment.

    Executes the following actions in order:
    1. UpdateAndUpgrade - Update system packages
    2. SSHHardening - Harden SSH configuration
    3. SSHKeys - Deploy SSH keys

    Example:
        .. code:: python

            from infraninja.actions.full_setup import FullSetup

            # Execute with defaults
            setup = FullSetup()
            result = setup.execute()

            # Execute with custom params for sub-actions
            result = setup.execute(
                SSHHardening={"permit_root_login": "no"},
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
    tags = ["setup", "hardening", "ssh", "composite"]
    category = "setup"
    color = "#9B59B6"
    logo = "fa-server"
    description = {
        "en": "Complete server setup including system updates, SSH hardening, and SSH key deployment",
        "ar": "إعداد الخادم الكامل بما في ذلك تحديثات النظام وتقوية SSH ونشر مفاتيح SSH",
        "fr": "Configuration complète du serveur incluant mises à jour, durcissement SSH et déploiement de clés SSH",
    }

    actions = [
        UpdateAndUpgrade,
        SSHHardening,
        SSHKeys,
    ]
