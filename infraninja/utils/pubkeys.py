import getpass
import json
import logging
import threading
from typing import Any, Dict, List, Optional

import requests
from pyinfra.api.deploy import deploy
from pyinfra.api.exceptions import PyinfraError
from pyinfra.context import host
from pyinfra.facts.server import User, Users
from pyinfra.operations import server

from infraninja.inventory.jinn import Jinn

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
)
logger = logging.getLogger(__name__)


class SSHKeyManagerError(Exception):
    """Custom exception for SSHKeyManager errors."""

    pass


class SSHKeyManager:
    """
    Manages SSH key operations including fetching from API and deploying to hosts.
    This class follows the singleton pattern to ensure only one instance
    exists and uses thread safety for multi-threaded environments.

    Usage:
        # Example usage of SSHKeyManager

            .. code-block:: python

                # Get the singleton instance
                manager = SSHKeyManager.get_instance(
                    api_url="https://api.example.com",
                    api_key="your_api_key"
                )

    """

    # Make class variables shared across all instances
    _ssh_keys: Optional[List[str]] = None
    _credentials: Optional[Dict[str, str]] = None
    _session_key: Optional[str] = None
    _lock: threading.RLock = threading.RLock()
    _instance: Optional["SSHKeyManager"] = None

    @classmethod
    def get_instance(cls, *args, **kwargs) -> "SSHKeyManager":
        """
        Get or create the singleton instance of SSHKeyManager.

        This method implements the singleton pattern to ensure only one instance
        of SSHKeyManager exists per application. Thread-safe.

        Args:
            *args: Positional arguments to pass to the constructor if creating a new instance
            **kwargs: Keyword arguments to pass to the constructor if creating a new instance

        Returns:
            SSHKeyManager: The singleton instance of SSHKeyManager
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls(*args, **kwargs)
        return cls._instance

    def __init__(
        self,
        api_url: Optional[str] = None,
        api_key: Optional[str] = None,
    ) -> None:
        """
        Initialize the SSHKeyManager with API URL and API key.

        Args:
            api_url: The API URL to use, defaults to Jinn's default URL if not provided
            api_key: The API key to use for authentication
        """
        with self._lock:
            # Set default API URL if none provided
            self.api_url: Optional[str] = api_url
            if not self.api_url:
                # Use the default API URL from Jinn class
                try:
                    jinn_instance = Jinn()
                    self.api_url = jinn_instance.api_url
                    logger.debug(f"Got API URL from Jinn: {self.api_url}")
                except Exception as e:
                    logger.warning(f"Failed to get API URL from Jinn: {str(e)}")
                    self.api_url = None

            # Ensure URL has a scheme
            if self.api_url:
                if not self.api_url.startswith(("http://", "https://")):
                    self.api_url = f"https://{self.api_url}"
                    logger.debug(f"Added https:// scheme to API URL: {self.api_url}")

                # Basic URL validation
                if "URLHERE" in self.api_url:
                    logger.error(f"URL contains placeholder 'URLHERE': {self.api_url}")
                    raise SSHKeyManagerError(
                        f"Invalid API URL with placeholder: {self.api_url}. Please provide a valid URL."
                    )

            # Store the API key
            self.api_key: Optional[str] = api_key

    @staticmethod
    def _get_credentials() -> Dict[str, str]:
        """
        Get user credentials either from cache or user input.

        This method prompts the user for credentials if they are not already cached.
        Credentials are stored at the class level to be shared across all instances.

        Returns:
            Dict[str, str]: A dictionary containing 'username' and 'password' keys

        Example:
            .. code-block:: python

                # Get credentials (will prompt if not cached)
                creds = SSHKeyManager._get_credentials()
                username = creds['username']
                password = creds['password']
        """
        # Use class-level cached credentials across all instances
        if SSHKeyManager._credentials:
            logger.debug("Using cached credentials")
            return SSHKeyManager._credentials

        # Only prompt once for credentials
        username: str = input("Enter username: ")
        password: str = getpass.getpass("Enter password: ")

        # Store credentials at class level to share across all instances
        SSHKeyManager._credentials = {"username": username, "password": password}
        logger.debug("Credentials obtained from user input")
        return SSHKeyManager._credentials

    @staticmethod
    def _make_auth_request(
        endpoint: str, method: str = "get", **kwargs: Any
    ) -> Optional[requests.Response]:
        """
        Make authenticated request to API.

        This method makes HTTP requests to the API using the stored session key
        for authentication. It includes proper headers and cookie authentication.

        Args:
            endpoint: The API endpoint URL to request
            method: HTTP method to use (default: 'get')
            **kwargs: Additional arguments to pass to requests.request

        Returns:
            Optional[requests.Response]: API response if successful, None otherwise

        Raises:
            SSHKeyManagerError: If no session key is available or request fails

        Example:
            .. code-block:: python

                # Make a GET request to an endpoint
                response = SSHKeyManager._make_auth_request(
                    "https://api.example.com/keys",
                    method="get"
                )
        """
        if not SSHKeyManager._session_key:
            raise SSHKeyManagerError(
                "Cannot make authenticated request: No session key available"
            )

        headers = {
            "Authorization": f"Bearer {SSHKeyManager._session_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        cookies = {"sessionid": SSHKeyManager._session_key}

        try:
            response = requests.request(
                method, endpoint, headers=headers, cookies=cookies, timeout=30, **kwargs
            )
            if response.status_code != 200:
                raise SSHKeyManagerError(
                    f"API request failed with status code {response.status_code}: {response.text[:100]}"
                )
            return response

        except Exception as e:
            raise SSHKeyManagerError(f"API request failed: {str(e)}")

    def _login(self) -> bool:
        """
        Authenticate with the API and get a session key.

        This method authenticates with the API using username/password credentials
        and obtains a session key for subsequent authenticated requests.

        Returns:
            bool: True if authentication succeeded, False otherwise

        Raises:
            SSHKeyManagerError: If API URL is not configured, login fails, or response is invalid

        Example:
            .. code-block:: python

                # Authenticate with the API
                manager = SSHKeyManager()
                if manager._login():
                    print("Authentication successful")
        """
        # Return early if already authenticated using class variable
        if SSHKeyManager._session_key:
            return True

        if not self.api_url:
            raise SSHKeyManagerError("Cannot login: No API URL configured")

        login_endpoint = f"{self.api_url}/login/"
        headers = {"Content-Type": "application/json", "Accept": "application/json"}

        # Get credentials just once and store them at class level
        credentials = self._get_credentials()

        try:
            # Make the POST request to /login/ with username and password in the body
            response = requests.post(
                login_endpoint,
                json={
                    "username": credentials["username"],
                    "password": credentials["password"],
                },
                headers=headers,
                timeout=30,
            )

            if response.status_code != 200:
                raise SSHKeyManagerError(
                    f"Login failed with status code {response.status_code}: {response.text[:100]}"
                )

            response_data = response.json()
            # Store session key at class level
            SSHKeyManager._session_key = response_data.get("session_key")

            if not SSHKeyManager._session_key:
                raise SSHKeyManagerError(
                    "Login succeeded but no session key in response"
                )

            return True

        except json.JSONDecodeError:
            raise SSHKeyManagerError("Received invalid JSON in login response")
        except Exception as e:
            raise SSHKeyManagerError(f"Login request failed: {str(e)}")

    def fetch_ssh_keys(self, force_refresh: bool = False) -> Optional[List[str]]:
        """
        Fetch SSH keys from the API server.

        This method retrieves SSH public keys from the configured API endpoint.
        Keys are cached to improve performance on subsequent calls.

        Args:
            force_refresh: If True, ignore cached keys and force a new fetch from API

        Returns:
            Optional[List[str]]: List of SSH public key strings or None if fetch fails

        Raises:
            SSHKeyManagerError: If authentication fails, API is not configured, or API response is invalid

        Example:
            .. code-block:: python

                # Fetch SSH keys from API
                manager = SSHKeyManager(api_url="https://api.example.com", api_key="key")
                keys = manager.fetch_ssh_keys()
                if keys:
                    print(f"Fetched {len(keys)} SSH keys")
        """
        # Return cached keys if available and not forcing refresh
        if SSHKeyManager._ssh_keys and not force_refresh:
            return SSHKeyManager._ssh_keys

        if not self._login():
            raise SSHKeyManagerError("Failed to authenticate with API")

        if not self.api_url:
            raise SSHKeyManagerError("Cannot fetch SSH keys: No API URL configured")

        endpoint = f"{self.api_url}/ssh-tools/ssh-keylist/"
        response = self._make_auth_request(endpoint)
        if not response:
            raise SSHKeyManagerError("Failed to retrieve SSH keys from API")

        # Parse the response
        try:
            ssh_data = response.json()

            if "result" not in ssh_data:
                raise SSHKeyManagerError("SSH key API response missing 'result' field")

            SSHKeyManager._ssh_keys = [
                key_data["key"] for key_data in ssh_data["result"] if "key" in key_data
            ]

            if not SSHKeyManager._ssh_keys:
                logger.warning("No SSH keys found in API response")

            return SSHKeyManager._ssh_keys

        except KeyError as e:
            raise SSHKeyManagerError(
                f"Missing expected field in SSH keys response: {e}"
            )
        except json.JSONDecodeError as e:
            raise SSHKeyManagerError(f"Failed to parse SSH keys response as JSON: {e}")
        except Exception as e:
            raise SSHKeyManagerError(f"Unexpected error parsing SSH keys response: {e}")

    @deploy("Add SSH keys to authorized_keys")
    def add_ssh_keys(self, force_refresh: bool = False) -> bool:
        """
        Add SSH keys to the authorized_keys file.

        Args:
            force_refresh: If True, force a refresh of SSH keys from API

        Returns:
            bool: True if keys were added successfully, False otherwise

        Raises:
            SSHKeyManagerError: If keys cannot be fetched or there's an error during deployment
        """
        try:
            # Get the SSH keys - may raise SSHKeyManagerError from fetch_ssh_keys
            keys = self.fetch_ssh_keys(force_refresh)
            if not keys:
                raise SSHKeyManagerError("No SSH keys available to deploy")

            # Get current user information
            current_user = host.get_fact(User)
            if not current_user:
                raise PyinfraError("Failed to determine current user")

            # Get user details
            users = host.get_fact(Users)
            if not users or current_user not in users:
                raise PyinfraError(
                    f"Failed to retrieve details for user: {current_user}"
                )

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
            raise SSHKeyManagerError(f"Missing user information: {e}")
        except Exception as e:
            raise SSHKeyManagerError(f"Error setting up SSH keys: {str(e)}")

    def clear_cache(self) -> bool:
        """
        Clear all cached credentials and keys.

        Returns:
            bool: True if cache was cleared successfully.

        Raises:
            SSHKeyManagerError: If there is an error while clearing the cache
        """
        try:
            with self._lock:
                SSHKeyManager._credentials = None
                SSHKeyManager._ssh_keys = None
                SSHKeyManager._session_key = None
                logger.debug("Cache cleared")
                return True
        except Exception as e:
            raise SSHKeyManagerError(f"Error clearing cache: {str(e)}")


# Global function for backward compatibility
def add_ssh_keys(force_refresh: bool = False, **kwargs) -> Any:
    """
    Backward compatibility function that uses the singleton instance.

    Args:
        force_refresh: If True, force a refresh of SSH keys from API

    Returns:
        Any: Returns the OperationMeta object from the decorated add_ssh_keys method.
    """
    manager: SSHKeyManager = SSHKeyManager.get_instance(**kwargs)
    return manager.add_ssh_keys(force_refresh)
