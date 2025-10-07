"""SSH keys deployment action"""

import logging
import time
from typing import Any, List, Optional

import requests
from pyinfra.api import DeployError
from pyinfra.operations import server

from infraninja.actions.base import Action

logger = logging.getLogger(__name__)


class SSHKeysAction(Action):
    """
    Deploy and manage SSH keys for a single system user.

    Fetches SSH keys from URLs and/or uses manually specified keys,
    then configures them in the user's authorized_keys file for secure authentication.

    Example:
        .. code:: python

            from infraninja.actions.ssh_keys import SSHKeysAction

            action = SSHKeysAction()
            action.execute(
                user="deploy",
                urls=["https://github.com/username.keys"],
                ssh_keys=["ssh-ed25519 AAAAC3..."],
                delete=False
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
    os_available = [
        "ubuntu",
        "debian",
        "alpine",
        "freebsd",
        "rhel",
        "centos",
        "fedora",
        "arch",
        "opensuse",
    ]

    def execute(
        self,
        user: str,
        urls: Optional[List[str]] = None,
        ssh_keys: Optional[List[str]] = None,
        delete: bool = False,
        timeout: int = 10,
        max_retries: int = 3,
        retry_delay: float = 5.0,
        validate_keys: bool = True,
    ) -> Any:
        """
        Execute SSH keys deployment for a single user.

        Args:
            user: Target system user to deploy SSH keys for (required)
            urls: List of URLs to fetch SSH keys from (e.g., GitHub .keys URLs)
            ssh_keys: List of manually specified SSH public keys
            delete: Whether to delete keys not specified in urls or ssh_keys (default: False)
            timeout: Timeout for URL requests in seconds (default: 10)
            max_retries: Maximum retry attempts for failed requests (default: 3)
            retry_delay: Delay between retry attempts in seconds (default: 5.0)
            validate_keys: Whether to validate SSH key formats (default: True)

        Returns:
            Result of the deployment operation

        Raises:
            DeployError: If user is not specified or if neither urls nor ssh_keys are provided
        """
        # Validate required parameters
        if not user or not isinstance(user, str) or not user.strip():
            msg = "'user' parameter is required and must be a non-empty string"
            raise DeployError(
                msg
            )

        if not urls and not ssh_keys:
            msg = "At least one of 'urls' or 'ssh_keys' must be provided"
            raise DeployError(msg)

        # Initialize lists if None
        if urls is None:
            urls = []
        if ssh_keys is None:
            ssh_keys = []

        logger.info(f"Starting SSH keys deployment for user: {user}")

        # Start with manually specified keys
        all_keys = ssh_keys.copy()
        logger.info(f"Found {len(all_keys)} manually specified SSH keys")

        # Validate manual keys if requested
        if validate_keys and all_keys:
            all_keys = self._validate_and_filter_keys(all_keys)

        # Fetch keys from URLs if specified
        if urls:
            logger.info(f"Fetching SSH keys from {len(urls)} URLs: {urls}")
            try:
                url_keys = self._fetch_keys_from_urls(
                    urls=urls,
                    timeout=timeout,
                    max_retries=max_retries,
                    retry_delay=retry_delay,
                )
                all_keys.extend(url_keys)
                logger.info(f"Successfully fetched {len(url_keys)} keys from URLs")
            except Exception as e:
                logger.error(f"Failed to fetch SSH keys from URLs: {e}")
                msg = f"Failed to fetch SSH keys from URLs: {e}"
                raise DeployError(msg)
        else:
            logger.info("No URLs specified, skipping URL key fetch")

        # Check if we have any keys to deploy
        if not all_keys:
            logger.warning(f"No SSH keys to deploy for user {user}")
            return

        logger.info(f"Deploying {len(all_keys)} total SSH keys for user {user}")

        # Deploy the keys
        try:
            server.user_authorized_keys(
                user=user,
                group=user,
                public_keys=all_keys,
                delete_keys=delete,
            )
            logger.info(f"SSH keys deployment completed successfully for user {user}")
        except Exception as e:
            logger.error(f"Failed to deploy SSH keys for user {user}: {e}")
            msg = f"Failed to deploy SSH keys for user {user}: {e}"
            raise DeployError(msg)

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
                logger.warning(
                    f"Skipping invalid SSH key at position {i}: {key[:50]}..."
                )

        logger.info(
            f"Validated {len(valid_keys)} out of {len(keys)} manually specified SSH keys"
        )
        return valid_keys

    def _fetch_keys_from_urls(
        self,
        urls: List[str],
        timeout: int = 10,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ) -> List[str]:
        """Fetch SSH keys from a list of URLs."""
        if not isinstance(urls, list):
            msg = "urls must be a list"
            raise DeployError(msg)

        if not urls:
            logger.info("No URLs provided, returning empty key list")
            return []

        keys = []

        for url in urls:
            if not url or not isinstance(url, str):
                logger.warning(f"Skipping invalid URL: {url}")
                continue

            url = url.strip()
            logger.info(f"Fetching SSH keys from URL: {url}")
            url_keys = self._fetch_url_keys_with_retry(
                url, timeout, max_retries, retry_delay
            )
            keys.extend(url_keys)
            logger.info(f"Successfully fetched {len(url_keys)} keys from {url}")

        logger.info(f"Total SSH keys fetched from URLs: {len(keys)}")
        return keys

    def _fetch_url_keys_with_retry(
        self, url: str, timeout: int, max_retries: int, retry_delay: float
    ) -> List[str]:
        """Fetch SSH keys from a single URL with retry logic."""

        for attempt in range(max_retries + 1):
            try:
                logger.debug(f"Attempt {attempt + 1}/{max_retries + 1} for {url}")

                response = requests.get(
                    url,
                    timeout=timeout,
                    headers={"User-Agent": "infraninja/1.0", "Accept": "text/plain"},
                )

                if response.status_code == 200:
                    return self._parse_ssh_keys(response.text, url)
                elif response.status_code == 404:
                    msg = f"URL not found: '{url}'"
                    raise DeployError(msg)
                else:
                    error_msg = (
                        f"HTTP {response.status_code} when fetching keys from {url}"
                    )
                    if attempt < max_retries:
                        logger.warning(f"{error_msg}, retrying in {retry_delay}s...")
                        time.sleep(retry_delay)
                        continue
                    else:
                        raise DeployError(error_msg)

            except requests.exceptions.Timeout:
                error_msg = f"Timeout fetching SSH keys from {url}"
                if attempt < max_retries:
                    logger.warning(f"{error_msg}, retrying in {retry_delay}s...")
                    time.sleep(retry_delay)
                    continue
                else:
                    raise DeployError(error_msg)

            except requests.exceptions.RequestException as e:
                error_msg = f"Network error fetching SSH keys from {url}: {e}"
                if attempt < max_retries:
                    logger.warning(f"{error_msg}, retrying in {retry_delay}s...")
                    time.sleep(retry_delay)
                    continue
                else:
                    raise DeployError(error_msg)

        msg = f"Failed to fetch SSH keys from {url} after {max_retries + 1} attempts"
        raise DeployError(
            msg
        )

    def _parse_ssh_keys(self, response_text: str, source: str) -> List[str]:
        """Parse SSH keys from URL response text."""
        keys = []

        for line_num, line in enumerate(response_text.split("\n"), 1):
            line = line.strip()

            if not line:
                continue

            if not self._is_valid_ssh_key_format(line):
                logger.warning(
                    f"Skipping invalid SSH key format from {source} (line {line_num})"
                )
                continue

            keys.append(line)

        return keys

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
