"""SSH keys deployment action"""

import logging
import time
from typing import Any, Dict, List

import requests
from pyinfra import host
from pyinfra.api import DeployError, FactError, deploy
from pyinfra.operations import server

from infraninja.actions.base import Action

logger = logging.getLogger(__name__)

DEFAULTS = {
    "infraninja": {
        "ssh_keys": [
            {
                "github_users": [],
                "ssh_keys": [],
                "delete": False,
                "user": None,
                "group": None,
            }
        ]
    }
}


class SSHKeysAction(Action):
    """
    Deploy and manage SSH keys for system users.

    Fetches SSH keys from GitHub users and/or uses manually specified keys,
    then configures them in users' authorized_keys files for secure authentication.

    Example:
        .. code:: python

            from infraninja.actions.ssh_keys import SSHKeysAction

            action = SSHKeysAction()
            action.execute(
                timeout=10,
                max_retries=3,
                validate_keys=True
            )
    """

    slug = "deploy-ssh-keys"
    name = {
        "en": "Deploy SSH Keys",
        "ar": "نشر مفاتيح SSH",
        "fr": "Déployer les clés SSH",
    }
    tags = ["security", "ssh", "authentication", "access-control"]
    category = "security"
    color = "#0080FF"
    logo = "fa-key"
    description = {
        "en": "Deploy and manage SSH keys for users from GitHub and manual sources with validation and access control",
        "ar": "نشر وإدارة مفاتيح SSH للمستخدمين من GitHub والمصادر اليدوية مع التحقق والتحكم في الوصول",
        "fr": "Déployer et gérer les clés SSH pour les utilisateurs depuis GitHub et sources manuelles avec validation",
    }
    os_available = ["ubuntu", "debian", "alpine", "freebsd", "rhel", "centos", "fedora", "arch", "opensuse"]

    @deploy("Setup SSH keys", data_defaults=DEFAULTS)
    def execute(
        self,
        timeout: int = 10,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        validate_keys: bool = True,
        **kwargs
    ) -> Any:
        """
        Execute SSH keys deployment.

        Args:
            timeout: Timeout for GitHub API requests in seconds (default: 10)
            max_retries: Maximum retry attempts for failed requests (default: 3)
            retry_delay: Delay between retry attempts in seconds (default: 1.0)
            validate_keys: Whether to validate SSH key formats (default: True)
            **kwargs: Additional parameters

        Returns:
            Result of the deployment operation
        """
        logger.info("Starting SSH keys deployment")

        # Get and validate configuration
        config = self._get_and_validate_config()
        ssh_keys_configs = config["ssh_keys"]

        logger.info(f"Found {len(ssh_keys_configs)} SSH key configurations to process")

        for i, ssh_config in enumerate(ssh_keys_configs):
            target_user = ssh_config["user"]
            if "group" not in ssh_config or ssh_config["group"] is None:
                target_group = target_user
            else:
                target_group = ssh_config["group"]
            logger.info(
                f"Configuring SSH keys for user: {target_user} (config {i + 1}/{len(ssh_keys_configs)})"
            )

            # Start with manually specified keys
            all_keys = ssh_config.get("ssh_keys", []).copy()
            logger.info(f"Found {len(all_keys)} manually specified SSH keys")

            # Validate manual keys if requested
            if validate_keys and all_keys:
                all_keys = self._validate_and_filter_keys(all_keys)

            # Fetch GitHub keys if users are specified
            github_users = ssh_config.get("github_users", [])
            if github_users:
                logger.info(
                    f"Fetching SSH keys from {len(github_users)} GitHub users: {github_users}"
                )
                try:
                    github_keys = self._fetch_github_ssh_keys(
                        github_users=github_users,
                        timeout=timeout,
                        max_retries=max_retries,
                        retry_delay=retry_delay,
                    )
                    all_keys.extend(github_keys)
                    logger.info(f"Successfully fetched {len(github_keys)} keys from GitHub")
                except Exception as e:
                    logger.error(f"Failed to fetch GitHub SSH keys: {e}")
                    raise DeployError(f"Failed to fetch GitHub SSH keys: {e}")
            else:
                logger.info("No GitHub users specified, skipping GitHub key fetch")

            # Check if we have any keys to deploy
            if not all_keys:
                logger.warning(f"No SSH keys to deploy for user {target_user}")
                continue

            logger.info(f"Deploying {len(all_keys)} total SSH keys for user {target_user}")

            # Deploy the keys
            try:
                server.user_authorized_keys(
                    user=target_user,
                    group=target_group,
                    public_keys=all_keys,
                    delete_keys=ssh_config.get("delete", False),
                )
                logger.info(
                    f"SSH keys deployment completed successfully for user {target_user}"
                )
            except Exception as e:
                logger.error(f"Failed to deploy SSH keys for user {target_user}: {e}")
                raise DeployError(f"Failed to deploy SSH keys for user {target_user}: {e}")

        logger.info("All SSH key configurations processed successfully")

    def _get_and_validate_config(self) -> Dict[str, Any]:
        """Get and validate the SSH keys configuration from host data."""
        infraninja_config = host.data.get("infraninja")
        if not infraninja_config:
            raise DeployError("Missing 'infraninja' configuration in host data")

        if not isinstance(infraninja_config, dict):
            raise DeployError("'infraninja' configuration must be a dictionary")

        ssh_keys_configs = infraninja_config.get("ssh_keys")
        if not ssh_keys_configs:
            raise DeployError("Missing 'ssh_keys' configuration in infraninja data")

        if not isinstance(ssh_keys_configs, list):
            raise DeployError("'ssh_keys' configuration must be a list of dictionaries")

        if not ssh_keys_configs:
            raise DeployError("'ssh_keys' configuration cannot be empty")

        # Validate each SSH keys configuration
        for i, ssh_config in enumerate(ssh_keys_configs):
            if not isinstance(ssh_config, dict):
                raise DeployError(
                    f"SSH keys configuration at position {i} must be a dictionary"
                )

            target_user = ssh_config.get("user")
            if not target_user:
                raise DeployError(
                    f"SSH keys configuration at position {i} missing required 'user' field"
                )

            if not isinstance(target_user, str) or not target_user.strip():
                raise DeployError(
                    f"'user' field at position {i} must be a non-empty string"
                )

            ssh_keys = ssh_config.get("ssh_keys", [])
            if not isinstance(ssh_keys, list):
                raise DeployError(f"'ssh_keys' field at position {i} must be a list")

            github_users = ssh_config.get("github_users", [])
            if not isinstance(github_users, list):
                raise DeployError(f"'github_users' field at position {i} must be a list")

            delete_keys = ssh_config.get("delete", False)
            if not isinstance(delete_keys, bool):
                raise DeployError(f"'delete' field at position {i} must be a boolean")

            # Validate GitHub usernames
            for username in github_users:
                if not isinstance(username, str):
                    raise DeployError(
                        f"GitHub username in config {i} must be a string, got: {type(username).__name__}"
                    )
                if not username.strip():
                    raise DeployError(f"GitHub username in config {i} cannot be empty")
                if not self._is_valid_github_username(username.strip()):
                    raise DeployError(
                        f"Invalid GitHub username format in config {i}: '{username}'"
                    )

            # Validate SSH keys
            for j, key in enumerate(ssh_keys):
                if not isinstance(key, str):
                    raise DeployError(
                        f"SSH key at position {j} in config {i} must be a string, got: {type(key).__name__}"
                    )
                if not key.strip():
                    raise DeployError(
                        f"SSH key at position {j} in config {i} cannot be empty"
                    )

            logger.debug(
                f"Configuration {i} validated successfully for user: {target_user}"
            )

        return infraninja_config

    def _validate_and_filter_keys(self, keys: List[str]) -> List[str]:
        """Validate and filter SSH keys, removing invalid ones."""
        valid_keys = []

        for i, key in enumerate(keys):
            key = key.strip()
            if not key:
                logger.warning(f"Skipping empty SSH key at position {i}")
                continue

            if self._is_valid_ssh_key_format(key):
                valid_keys.append(key)
            else:
                logger.warning(f"Skipping invalid SSH key at position {i}: {key[:50]}...")

        logger.info(
            f"Validated {len(valid_keys)} out of {len(keys)} manually specified SSH keys"
        )
        return valid_keys

    def _fetch_github_ssh_keys(
        self,
        github_users: List[str],
        timeout: int = 10,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ) -> List[str]:
        """Fetch SSH keys from GitHub for a list of users."""
        if not isinstance(github_users, list):
            raise FactError("github_users must be a list")

        if not github_users:
            logger.info("No GitHub users provided, returning empty key list")
            return []

        keys = []

        for github_user in github_users:
            if not github_user or not isinstance(github_user, str):
                logger.warning(f"Skipping invalid GitHub username: {github_user}")
                continue

            github_user = github_user.strip()
            if not self._is_valid_github_username(github_user):
                logger.warning(f"Skipping invalid GitHub username format: {github_user}")
                continue

            logger.info(f"Fetching SSH keys for GitHub user: {github_user}")
            user_keys = self._fetch_user_keys_with_retry(
                github_user, timeout, max_retries, retry_delay
            )
            keys.extend(user_keys)
            logger.info(f"Successfully fetched {len(user_keys)} keys for {github_user}")

        logger.info(f"Total SSH keys fetched: {len(keys)}")
        return keys

    def _fetch_user_keys_with_retry(
        self, github_user: str, timeout: int, max_retries: int, retry_delay: float
    ) -> List[str]:
        """Fetch SSH keys for a single GitHub user with retry logic."""
        url = f"https://github.com/{github_user}.keys"

        for attempt in range(max_retries + 1):
            try:
                logger.debug(f"Attempt {attempt + 1}/{max_retries + 1} for {github_user}")

                response = requests.get(
                    url,
                    timeout=timeout,
                    headers={"User-Agent": "infraninja/1.0", "Accept": "text/plain"},
                )

                if response.status_code == 200:
                    return self._parse_ssh_keys(response.text, github_user)
                elif response.status_code == 404:
                    raise FactError(f"GitHub user '{github_user}' not found")
                else:
                    error_msg = (
                        f"HTTP {response.status_code} when fetching keys for {github_user}"
                    )
                    if attempt < max_retries:
                        logger.warning(f"{error_msg}, retrying in {retry_delay}s...")
                        time.sleep(retry_delay)
                        continue
                    else:
                        raise DeployError(error_msg)

            except requests.exceptions.Timeout:
                error_msg = f"Timeout fetching SSH keys for {github_user}"
                if attempt < max_retries:
                    logger.warning(f"{error_msg}, retrying in {retry_delay}s...")
                    time.sleep(retry_delay)
                    continue
                else:
                    raise DeployError(error_msg)

            except requests.exceptions.RequestException as e:
                error_msg = f"Network error fetching SSH keys for {github_user}: {e}"
                if attempt < max_retries:
                    logger.warning(f"{error_msg}, retrying in {retry_delay}s...")
                    time.sleep(retry_delay)
                    continue
                else:
                    raise DeployError(error_msg)

        raise DeployError(
            f"Failed to fetch SSH keys for {github_user} after {max_retries + 1} attempts"
        )

    def _parse_ssh_keys(self, response_text: str, github_user: str) -> List[str]:
        """Parse SSH keys from GitHub API response text."""
        keys = []

        for line_num, line in enumerate(response_text.split("\n"), 1):
            line = line.strip()

            if not line:
                continue

            if not self._is_valid_ssh_key_format(line):
                logger.warning(
                    f"Skipping invalid SSH key format for {github_user} (line {line_num})"
                )
                continue

            formatted_key = f"{line} {github_user}@github"
            keys.append(formatted_key)

        return keys

    def _is_valid_github_username(self, username: str) -> bool:
        """Validate GitHub username format."""
        if not username:
            return False

        if len(username) > 39:
            return False

        if username.startswith("-") or username.endswith("-"):
            return False

        return all(c.isalnum() or c == "-" for c in username)

    def _is_valid_ssh_key_format(self, key: str) -> bool:
        """Basic validation of SSH key format."""
        if not key:
            return False

        parts = key.strip().split()

        if len(parts) < 2:
            return False

        key_type = parts[0].lower()
        valid_types = {
            "ssh-rsa",
            "ssh-dss",
            "ssh-ed25519",
            "ecdsa-sha2-nistp256",
            "ecdsa-sha2-nistp384",
            "ecdsa-sha2-nistp521",
            "ssh-ed448",
        }

        return key_type in valid_types
