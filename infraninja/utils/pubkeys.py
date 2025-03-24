import getpass
import json
import logging
import os
import threading
from typing import Any, Dict, List, Optional

import requests
from pyinfra import host
from pyinfra.api import deploy
from pyinfra.facts.server import User, Users
from pyinfra.operations import server

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
)
logger = logging.getLogger(__name__)


class SSHKeyManager:
    """
    Manages SSH key operations including fetching from API and deploying to hosts.

    This class follows the singleton pattern to ensure only one instance
    exists and uses thread safety for multi-threaded environments.
    """

    _ssh_keys: Optional[List[str]] = None
    _credentials: Optional[Dict[str, str]] = None
    _session_key: Optional[str] = None
    _base_url: Optional[str] = None
    _lock: threading.RLock = threading.RLock()
    _instance: Optional["SSHKeyManager"] = None  # Singleton instance

    @classmethod
    def get_instance(cls) -> "SSHKeyManager":
        """Get or create the singleton instance of SSHKeyManager."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = SSHKeyManager()
        return cls._instance

    def __init__(self) -> None:
        """
        Initialize the SSHKeyManager.

        Checks and sets the base URL from environment variables.
        """
        with self._lock:
            if SSHKeyManager._base_url is None:
                SSHKeyManager._base_url = os.getenv("JINN_API_URL")
                if not SSHKeyManager._base_url:
                    logger.error("Error: JINN_API_URL environment variable not set")

    def _get_base_url(self) -> Optional[str]:
        """
        Get API base URL from environment.

        Returns:
            Optional[str]: The base URL or None if not set
        """
        if not self._base_url:
            self._base_url = os.getenv("JINN_API_URL")
            if not self._base_url:
                logger.error("Error: JINN_API_URL environment variable not set")
                return None
        return self._base_url

    def _get_credentials(self) -> Dict[str, str]:
        """
        Get user credentials either from cache or user input.

        Returns:
            Dict[str, str]: A dictionary with username and password
        """
        if self._credentials:
            logger.debug("Using cached credentials")
            return self._credentials

        username: str = input("Enter username: ")
        password: str = getpass.getpass("Enter password: ")

        self._credentials = {"username": username, "password": password}
        logger.debug("Credentials obtained from user input")
        return self._credentials

    def _make_auth_request(
        self, endpoint: str, method: str = "get", **kwargs: Any
    ) -> Optional[requests.Response]:
        """
        Make authenticated request to API.

        Args:
            endpoint: The API endpoint URL
            method: HTTP method to use (default: 'get')
            **kwargs: Additional arguments to pass to requests.request

        Returns:
            Optional[requests.Response]: API response if successful, None otherwise
        """
        if not self._session_key:
            logger.error("Cannot make authenticated request: No session key available")
            return None

        headers = {
            "Authorization": f"Bearer {self._session_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        cookies = {"sessionid": self._session_key}

        try:
            response = requests.request(
                method, endpoint, headers=headers, cookies=cookies, timeout=30, **kwargs
            )
            if response.status_code != 200:
                logger.error(
                    "API request failed with status code %s: %s",
                    response.status_code,
                    response.text[:100],  # Limit response text in logs
                )
                return None
            return response

        except requests.exceptions.Timeout:
            logger.error("API request timed out for %s", endpoint)
        except requests.exceptions.ConnectionError:
            logger.error("Connection error when accessing %s", endpoint)
        except requests.exceptions.RequestException as e:
            logger.error("API request failed: %s", str(e))
        return None

    def _login(self) -> bool:
        """
        Authenticate with the API and get a session key.

        Returns:
            bool: True if authentication succeeded, False otherwise
        """
        # Return early if already authenticated
        if self._session_key:
            return True

        base_url = self._get_base_url()
        if not base_url:
            return False

        credentials = self._get_credentials()
        login_endpoint = f"{base_url}/login/"
        headers = {"Content-Type": "application/json", "Accept": "application/json"}

        try:
            response = requests.post(
                login_endpoint,
                json=credentials,
                headers=headers,
                timeout=30,
            )

            if response.status_code != 200:
                logger.error(
                    "Login failed with status code %s: %s",
                    response.status_code,
                    response.text[:100],  # Limit response text in logs
                )
                return False

            response_data = response.json()
            self._session_key = response_data.get("session_key")

            if not self._session_key:
                logger.error("Login succeeded but no session key in response")
                return False

            return True

        except requests.exceptions.Timeout:
            logger.error("Login request timed out")
        except requests.exceptions.ConnectionError:
            logger.error("Connection error when attempting to login")
        except json.JSONDecodeError:
            logger.error("Received invalid JSON in login response")
        except requests.exceptions.RequestException as e:
            logger.error("Login request failed: %s", str(e))

        return False

    def fetch_ssh_keys(self, force_refresh: bool = False) -> Optional[List[str]]:
        """
        Fetch SSH keys from the API server.

        Args:
            force_refresh: If True, ignore cached keys and force a new fetch

        Returns:
            Optional[List[str]]: List of SSH public keys or None if fetch fails
        """
        # Return cached keys if available and not forcing refresh
        if self._ssh_keys and not force_refresh:
            return self._ssh_keys

        if not self._login():
            logger.error("Failed to authenticate with API")
            return None

        base_url = self._get_base_url()
        if not base_url:
            logger.error("Cannot fetch SSH keys: No API URL configured")
            return None

        endpoint = f"{base_url}/ssh-tools/ssh-keylist/"
        response = self._make_auth_request(endpoint)
        if not response:
            logger.error("Failed to retrieve SSH keys from API")
            return None

        # Parse the response
        try:
            ssh_data = response.json()

            if "result" not in ssh_data:
                logger.error("SSH key API response missing 'result' field")
                return None

            self._ssh_keys = [
                key_data["key"] for key_data in ssh_data["result"] if "key" in key_data
            ]

            if not self._ssh_keys:
                logger.warning("No SSH keys found in API response")

            return self._ssh_keys

        except KeyError as e:
            logger.error("Missing expected field in SSH keys response: %s", e)
            return None
        except json.JSONDecodeError as e:
            logger.error("Failed to parse SSH keys response as JSON: %s", e)
            return None
        except Exception as e:
            logger.error("Unexpected error parsing SSH keys response: %s", e)
            return None

    @deploy("Add SSH keys to authorized_keys")
    def add_ssh_keys(self, force_refresh: bool = False) -> bool:
        """
        Add SSH keys to the authorized_keys file.

        Args:
            force_refresh: If True, force a refresh of SSH keys from API

        Returns:
            bool: True if keys were added successfully, False otherwise
        """
        # Get the SSH keys
        keys = self.fetch_ssh_keys(force_refresh)
        if not keys:
            logger.error("No SSH keys available to deploy")
            return False

        try:
            # Get current user information
            current_user = host.get_fact(User)
            if not current_user:
                logger.error("Failed to determine current user")
                return False

            # Get user details
            users = host.get_fact(Users)
            if not users or current_user not in users:
                logger.error("Failed to retrieve details for user: %s", current_user)
                return False

            user_details = users[current_user]

            server.user_authorized_keys(
                name=f"Add SSH keys for {current_user}",
                user=current_user,
                group=user_details["group"],
                public_keys=keys,
                delete_keys=False,
            )

            logger.info(
                "Successfully added %d SSH keys for user %s", len(keys), current_user
            )
            return True

        except KeyError as e:
            logger.error("Missing user information: %s", e)
            return False
        except Exception as e:
            logger.error("Error setting up SSH keys: %s", str(e))
            return False

    def clear_cache(self) -> bool:
        """
        Clear all cached credentials and keys.

        Returns:
            bool: True if cache was cleared successfully.
        """
        with self._lock:
            SSHKeyManager._credentials = None
            SSHKeyManager._ssh_keys = None
            SSHKeyManager._session_key = None
            logger.debug("Cache cleared")
            return True


def add_ssh_keys() -> bool:
    """
    Backward compatibility function that uses the singleton instance.

    Returns:
        bool: True if keys were added successfully, False otherwise.
    """
    manager: SSHKeyManager = SSHKeyManager.get_instance()
    return manager.add_ssh_keys()
