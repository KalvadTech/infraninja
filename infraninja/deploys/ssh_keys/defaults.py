"""Default configuration values for SSH keys deployment module.

This module defines the default configuration structure and values
for managing SSH keys on remote servers.
"""

# Default configuration for SSH keys management
DEFAULTS = {
    "infraninja": {
        "ssh_keys": [
            {
                # List of GitHub usernames whose public keys should be added
                # Example: ["username1", "username2"]
                "github_users": [],
                # List of SSH public keys to be added directly
                # Example: ["ssh-rsa AAAAB3Nza...", "ssh-ed25519 AAAAC3Nza..."]
                "ssh_keys": [],
                # Whether to delete existing SSH keys before adding new ones
                # Set to True to replace all existing keys, False to append
                "delete": False,
                # Target user account for SSH key management
                # If None, the deployment will fail
                "user": None,
                "group": None,
            }
        ]
    }
}
