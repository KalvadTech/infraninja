#!/usr/bin/env python3

import logging
from typing import Any, Dict, List

from pyinfra import host
from pyinfra.api import DeployError, deploy
from pyinfra.operations import server

from .defaults import DEFAULTS
from .util import (
    _is_valid_github_username,
    _is_valid_ssh_key_format,
    fetch_github_ssh_keys,
)

logger = logging.getLogger(__name__)


@deploy("Setup SSH keys", data_defaults=DEFAULTS)
def ssh_keys(
    timeout: int = 10,
    max_retries: int = 3,
    retry_delay: float = 1.0,
    validate_keys: bool = True,
) -> None:
    """
    Deploy SSH keys for a user from multiple sources.

    Fetches SSH keys from GitHub users and combines them with manually specified
    keys, then configures them for the target user's authorized_keys file.

    Args:
        timeout: Timeout for GitHub API requests in seconds
        max_retries: Maximum retry attempts for failed GitHub requests
        retry_delay: Delay between retry attempts in seconds
        validate_keys: Whether to validate SSH key formats

    Raises:
        DeployError: If configuration is invalid or deployment fails
    """
    logger.info("Starting SSH keys deployment")

    # Get and validate configuration
    config = _get_and_validate_config()
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
            all_keys = _validate_and_filter_keys(all_keys)

        # Fetch GitHub keys if users are specified
        github_users = ssh_config.get("github_users", [])
        if github_users:
            logger.info(
                f"Fetching SSH keys from {len(github_users)} GitHub users: {github_users}"
            )
            try:
                github_keys = fetch_github_ssh_keys(
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


def _get_and_validate_config() -> Dict[str, Any]:
    """
    Get and validate the SSH keys configuration from host data.

    Returns:
        Validated configuration dictionary

    Raises:
        DeployError: If configuration is missing or invalid
    """
    # Get infraninja configuration
    infraninja_config = host.data.get("infraninja")
    if not infraninja_config:
        raise DeployError("Missing 'infraninja' configuration in host data")

    if not isinstance(infraninja_config, dict):
        raise DeployError("'infraninja' configuration must be a dictionary")

    # Get SSH keys configuration
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

        # Validate required fields
        target_user = ssh_config.get("user")
        if not target_user:
            raise DeployError(
                f"SSH keys configuration at position {i} missing required 'user' field"
            )

        if not isinstance(target_user, str) or not target_user.strip():
            raise DeployError(
                f"'user' field at position {i} must be a non-empty string"
            )

        # Validate optional fields with defaults
        ssh_keys = ssh_config.get("ssh_keys", [])
        if not isinstance(ssh_keys, list):
            raise DeployError(f"'ssh_keys' field at position {i} must be a list")

        github_users = ssh_config.get("github_users", [])
        if not isinstance(github_users, list):
            raise DeployError(f"'github_users' field at position {i} must be a list")

        delete_keys = ssh_config.get("delete", False)
        if not isinstance(delete_keys, bool):
            raise DeployError(f"'delete' field at position {i} must be a boolean")

        # Validate GitHub usernames using util function
        for username in github_users:
            if not isinstance(username, str):
                raise DeployError(
                    f"GitHub username in config {i} must be a string, got: {type(username).__name__}"
                )
            if not username.strip():
                raise DeployError(f"GitHub username in config {i} cannot be empty")
            if not _is_valid_github_username(username.strip()):
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


def _validate_and_filter_keys(keys: List[str]) -> List[str]:
    """
    Validate and filter SSH keys, removing invalid ones.

    Uses the validation function from util.py to ensure consistency.

    Args:
        keys: List of SSH key strings to validate

    Returns:
        List of valid SSH keys
    """
    valid_keys = []

    for i, key in enumerate(keys):
        key = key.strip()
        if not key:
            logger.warning(f"Skipping empty SSH key at position {i}")
            continue

        if _is_valid_ssh_key_format(key):
            valid_keys.append(key)
        else:
            logger.warning(f"Skipping invalid SSH key at position {i}: {key[:50]}...")

    logger.info(
        f"Validated {len(valid_keys)} out of {len(keys)} manually specified SSH keys"
    )
    return valid_keys
