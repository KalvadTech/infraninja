#!/usr/bin/env python3

import logging
import time
from typing import List

import requests
from pyinfra.api import DeployError, FactError


logger = logging.getLogger(__name__)


def fetch_github_ssh_keys(
    github_users: List[str],
    timeout: int = 10,
    max_retries: int = 3,
    retry_delay: float = 1.0,
) -> List[str]:
    """
    Fetch SSH keys from GitHub for a list of users.

    Args:
        github_users: List of GitHub usernames
        timeout: Request timeout in seconds (default: 10)
        max_retries: Maximum number of retry attempts per user (default: 3)
        retry_delay: Delay between retries in seconds (default: 1.0)

    Returns:
        List of SSH keys with GitHub username appended as comments

    Raises:
        DeployError: If fetching keys fails for any user after all retries
        FactError: If github_users is not a list or contains invalid usernames
    """
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
        if not _is_valid_github_username(github_user):
            logger.warning(f"Skipping invalid GitHub username format: {github_user}")
            continue

        logger.info(f"Fetching SSH keys for GitHub user: {github_user}")
        user_keys = _fetch_user_keys_with_retry(
            github_user, timeout, max_retries, retry_delay
        )
        keys.extend(user_keys)
        logger.info(f"Successfully fetched {len(user_keys)} keys for {github_user}")

    logger.info(f"Total SSH keys fetched: {len(keys)}")
    return keys


def _fetch_user_keys_with_retry(
    github_user: str, timeout: int, max_retries: int, retry_delay: float
) -> List[str]:
    """
    Fetch SSH keys for a single GitHub user with retry logic.

    Args:
        github_user: GitHub username
        timeout: Request timeout in seconds
        max_retries: Maximum number of retry attempts
        retry_delay: Delay between retries in seconds

    Returns:
        List of formatted SSH keys for the user

    Raises:
        DeployError: If all retry attempts fail
    """
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
                return _parse_ssh_keys(response.text, github_user)
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

    # This should never be reached, but just in case
    raise DeployError(
        f"Failed to fetch SSH keys for {github_user} after {max_retries + 1} attempts"
    )


def _parse_ssh_keys(response_text: str, github_user: str) -> List[str]:
    """
    Parse SSH keys from GitHub API response text.

    Args:
        response_text: Raw response text from GitHub
        github_user: GitHub username for key comments

    Returns:
        List of formatted SSH keys
    """
    keys = []

    for line_num, line in enumerate(response_text.split("\n"), 1):
        line = line.strip()

        if not line:
            continue

        # Basic validation of SSH key format
        if not _is_valid_ssh_key_format(line):
            logger.warning(
                f"Skipping invalid SSH key format for {github_user} (line {line_num})"
            )
            continue

        # Add GitHub username as comment to the key
        formatted_key = f"{line} {github_user}@github"
        keys.append(formatted_key)

    return keys


def _is_valid_github_username(username: str) -> bool:
    """
    Validate GitHub username format.

    Args:
        username: Username to validate

    Returns:
        True if username appears valid, False otherwise
    """
    if not username:
        return False

    # GitHub username rules: alphanumeric and hyphens, cannot start/end with hyphen
    # Length: 1-39 characters
    if len(username) > 39:
        return False

    if username.startswith("-") or username.endswith("-"):
        return False

    # Allow only alphanumeric characters and hyphens
    return all(c.isalnum() or c == "-" for c in username)


def _is_valid_ssh_key_format(key: str) -> bool:
    """
    Basic validation of SSH key format.

    Args:
        key: SSH key string to validate

    Returns:
        True if key appears to be in valid SSH format, False otherwise
    """
    if not key:
        return False

    parts = key.strip().split()

    # SSH key should have at least 2 parts: type and key data
    if len(parts) < 2:
        return False

    # Check if first part looks like a valid SSH key type
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
