import getpass
import json
import logging
import threading
from typing import Any, Dict, List, Optional

import requests
from pyinfra.api.deploy import deploy
from pyinfra.context import host
from pyinfra.facts.server import User, Users
from pyinfra.operations import server

from infraninja.inventory.jinn import Jinn

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
)
logger = logging.getLogger(__name__)


class SSHKeyDeleteError(Exception):
    """Custom exception for SSH key deletion errors."""

    pass


class SSHKeyDeleter:
    """
    Manages SSH key deletion operations including fetching keys from API
    and removing them from users' authorized_keys files.
    This class follows the singleton pattern to ensure only one instance
    exists and uses thread safety for multi-threaded environments.

    Usage:
        # Example usage of SSHKeyDeleter
            .. code-block:: python

                # Get the singleton instance
                deleter = SSHKeyDeleter.get_instance(
                    api_url="https://api.example.com",
                    api_key="your_api_key"
                )
        # Delete keys for specific users based on filter criteria
        filter_criteria = {"labels": ["old_key", "compromised"]}
        key_deleter.delete_ssh_keys_for_users(["user1", "user2"], filter_criteria)
    """

    # Make class variables shared across all instances
    _ssh_keys: Optional[List[Dict[str, str]]] = None
    _credentials: Optional[Dict[str, str]] = None
    _session_key: Optional[str] = None
    _lock: threading.RLock = threading.RLock()
    _instance: Optional["SSHKeyDeleter"] = None

    @classmethod
    def get_instance(cls, *args, **kwargs) -> "SSHKeyDeleter":
        """
        Get or create the singleton instance of SSHKeyDeleter.

        This method implements the singleton pattern to ensure only one instance
        of SSHKeyDeleter exists per application. Thread-safe.

        Args:
            *args: Positional arguments to pass to the constructor if creating a new instance
            **kwargs: Keyword arguments to pass to the constructor if creating a new instance

        Returns:
            SSHKeyDeleter: The singleton instance of SSHKeyDeleter
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
        Initialize the SSHKeyDeleter with API URL and API key.

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
                    raise SSHKeyDeleteError(
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
                creds = SSHKeyDeleter._get_credentials()
                username = creds['username']
                password = creds['password']
        """
        # Use class-level cached credentials across all instances
        if SSHKeyDeleter._credentials:
            logger.debug("Using cached credentials")
            return SSHKeyDeleter._credentials

        # Only prompt once for credentials
        username: str = input("Enter username: ")
        password: str = getpass.getpass("Enter password: ")

        # Store credentials at class level to share across all instances
        SSHKeyDeleter._credentials = {"username": username, "password": password}
        logger.debug("Credentials obtained from user input")
        return SSHKeyDeleter._credentials

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
            SSHKeyDeleteError: If no session key is available or request fails

        Example:
            .. code-block:: python

                # Make a GET request to an endpoint
                response = SSHKeyDeleter._make_auth_request(
                    "https://api.example.com/keys",
                    method="get"
                )
        """
        if not SSHKeyDeleter._session_key:
            raise SSHKeyDeleteError(
                "Cannot make authenticated request: No session key available"
            )

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        cookies = {"sessionid": SSHKeyDeleter._session_key}

        try:
            response = requests.request(
                method, endpoint, headers=headers, cookies=cookies, timeout=30, **kwargs
            )
            if response.status_code != 200:
                raise SSHKeyDeleteError(
                    f"API request failed with status code {response.status_code}: {response.text[:100]}"
                )
            return response

        except Exception as e:
            raise SSHKeyDeleteError(f"API request failed: {str(e)}")

    def _login(self) -> bool:
        """
        Authenticate with the API and get a session key.

        This method authenticates with the API using username/password credentials
        and obtains a session key for subsequent authenticated requests.

        Returns:
            bool: True if authentication succeeded, False otherwise

        Raises:
            SSHKeyDeleteError: If API URL is not configured, login fails, or response is invalid

        Example:
            .. code-block:: python

                # Authenticate with the API
                deleter = SSHKeyDeleter()
                if deleter._login():
                    print("Authentication successful")
        """
        # Return early if already authenticated using class variable
        if SSHKeyDeleter._session_key:
            return True

        if not self.api_url:
            raise SSHKeyDeleteError("Cannot login: No API URL configured")

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
                raise SSHKeyDeleteError(
                    f"Login failed with status code {response.status_code}: {response.text[:100]}"
                )

            response_data = response.json()
            # Store session key at class level
            SSHKeyDeleter._session_key = response_data.get("session_key")

            if not SSHKeyDeleter._session_key:
                raise SSHKeyDeleteError(
                    "Login succeeded but no session key in response"
                )

            return True

        except json.JSONDecodeError:
            raise SSHKeyDeleteError("Received invalid JSON in login response")
        except Exception as e:
            raise SSHKeyDeleteError(f"Login request failed: {str(e)}")

    def fetch_ssh_keys(
        self, force_refresh: bool = False
    ) -> Optional[List[Dict[str, str]]]:
        """
        Fetch all SSH keys from the API server using the ssh-keylist endpoint.

        This method retrieves SSH key objects from the configured API endpoint.
        Keys are cached to improve performance on subsequent calls.

        Args:
            force_refresh: If True, ignore cached keys and force a new fetch from API

        Returns:
            Optional[List[Dict[str, str]]]: List of SSH key objects with id, label, and key

        Raises:
            SSHKeyDeleteError: If authentication fails, API is not configured, or API response is invalid

        Example:
            .. code-block:: python

                # Fetch SSH keys from API
                deleter = SSHKeyDeleter(api_url="https://api.example.com", api_key="key")
                keys = deleter.fetch_ssh_keys()
                if keys:
                    print(f"Fetched {len(keys)} SSH key objects")
        """
        # Return cached keys if available and not forcing refresh
        if SSHKeyDeleter._ssh_keys and not force_refresh:
            return SSHKeyDeleter._ssh_keys

        if not self._login():
            raise SSHKeyDeleteError("Failed to authenticate with API")

        if not self.api_url:
            raise SSHKeyDeleteError("Cannot fetch SSH keys: No API URL configured")

        # Use the correct endpoint from the API spec
        endpoint = f"{self.api_url}/ssh-tools/ssh-keylist/"
        response = self._make_auth_request(endpoint)
        if not response:
            raise SSHKeyDeleteError("Failed to retrieve SSH keys from API")

        # Parse the response
        try:
            ssh_data = response.json()

            if "result" not in ssh_data:
                raise SSHKeyDeleteError("SSH key API response missing 'result' field")

            # Store the full key objects for more flexibility
            SSHKeyDeleter._ssh_keys = ssh_data["result"]

            if not SSHKeyDeleter._ssh_keys:
                logger.warning("No SSH keys found in API response")

            return SSHKeyDeleter._ssh_keys

        except KeyError as e:
            raise SSHKeyDeleteError(f"Missing expected field in SSH keys response: {e}")
        except json.JSONDecodeError as e:
            raise SSHKeyDeleteError(f"Failed to parse SSH keys response as JSON: {e}")
        except Exception as e:
            raise SSHKeyDeleteError(f"Unexpected error parsing SSH keys response: {e}")

    def filter_keys_for_deletion(
        self,
        all_keys: List[Dict[str, str]],
        filter_criteria: Optional[Dict[str, Any]] = None,
    ) -> List[str]:
        """
        Filter SSH keys based on criteria to determine which ones to delete.

        This method applies various filtering criteria to determine which SSH keys
        should be marked for deletion. Supported criteria include labels, key patterns,
        and key IDs.

        Args:
            all_keys: List of all SSH key objects from the API
            filter_criteria: Dictionary with filtering criteria like labels, key_patterns, etc.

        Returns:
            List[str]: List of SSH key content strings to delete

        Warning:
            If no filter_criteria is provided, ALL keys will be marked for deletion.
            Use with extreme caution.

        Example:
            .. code-block:: python

                # Filter keys by labels
                deleter = SSHKeyDeleter()
                all_keys = deleter.fetch_ssh_keys()
                criteria = {"labels": ["old_key", "compromised"]}
                keys_to_delete = deleter.filter_keys_for_deletion(all_keys, criteria)
        """
        if not filter_criteria:
            # If no criteria provided, return all keys (be careful with this!)
            logger.warning(
                "No filter criteria provided - this will delete ALL SSH keys!"
            )
            return [key_data["key"] for key_data in all_keys if "key" in key_data]

        keys_to_delete = []

        # Filter by labels if provided
        if "labels" in filter_criteria:
            target_labels = filter_criteria["labels"]
            if not isinstance(target_labels, list):
                target_labels = [target_labels]

            for key_data in all_keys:
                if key_data.get("label") in target_labels:
                    keys_to_delete.append(key_data["key"])

        # Filter by key patterns if provided
        if "key_patterns" in filter_criteria:
            import re

            patterns = filter_criteria["key_patterns"]
            if not isinstance(patterns, list):
                patterns = [patterns]

            for key_data in all_keys:
                key_content = key_data.get("key", "")
                for pattern in patterns:
                    if re.search(pattern, key_content):
                        keys_to_delete.append(key_data["key"])
                        break

        # Filter by key IDs if provided
        if "key_ids" in filter_criteria:
            target_ids = filter_criteria["key_ids"]
            if not isinstance(target_ids, list):
                target_ids = [target_ids]

            for key_data in all_keys:
                if key_data.get("id") in target_ids:
                    keys_to_delete.append(key_data["key"])

        return list(set(keys_to_delete))  # Remove duplicates

    def _check_root_access(self) -> bool:
        """
        Check if current user has root access.

        This method determines whether the current user has root privileges
        or sudo access required for modifying other users' authorized_keys files.

        Returns:
            bool: True if user has root access, False otherwise

        Raises:
            SSHKeyDeleteError: If unable to determine root access

        Example:
            .. code-block:: python

                # Check if we have the necessary permissions
                deleter = SSHKeyDeleter()
                if deleter._check_root_access():
                    print("Can modify other users' SSH keys")
                else:
                    print("Need root or sudo access")
        """
        try:
            current_user = host.get_fact(User)
            if current_user == "root":
                return True

            # Check if user can sudo by testing a simple sudo command
            from pyinfra.facts.server import Command

            sudo_check = host.get_fact(
                Command, "sudo -n true 2>/dev/null && echo 'success' || echo 'failed'"
            )
            return sudo_check is not None and "success" in str(sudo_check)

        except Exception as e:
            raise SSHKeyDeleteError(f"Failed to check root access: {str(e)}")

    def _escape_regex_special_chars(self, text: str) -> str:
        """
        Escape special regex characters in SSH key text.

        This method escapes regex metacharacters in SSH key strings to prevent
        them from being interpreted as regex patterns during text processing.

        Args:
            text: The text to escape

        Returns:
            str: Text with regex special characters escaped

        Example:
            .. code-block:: python

                # Escape special characters in an SSH key
                deleter = SSHKeyDeleter()
                escaped_key = deleter._escape_regex_special_chars("ssh-rsa AAAA+key/data==")
        """
        # Regex special characters that need escaping
        special_chars = r"\.^$*+?{}[]|()"
        escaped = text
        for char in special_chars:
            escaped = escaped.replace(char, f"\\{char}")
        return escaped

    def _remove_key_from_authorized_keys(self, user: str, key_to_delete: str) -> bool:
        """
        Remove a specific SSH key from a user's authorized_keys file using pyinfra's server.user_authorized_keys.

        This method safely removes an SSH key from a user's authorized_keys file,
        preserving other keys and maintaining proper file permissions.

        Args:
            user: Username whose authorized_keys file to modify
            key_to_delete: SSH key string to remove

        Returns:
            bool: True if operation completed, False if user not found

        Raises:
            SSHKeyDeleteError: If there's an error accessing or modifying the file

        Example:
            .. code-block:: python

                # Remove a specific key from a user
                deleter = SSHKeyDeleter()
                success = deleter._remove_key_from_authorized_keys(
                    "username",
                    "ssh-rsa AAAA...key_data..."
                )
        """
        try:
            # Get user details
            users = host.get_fact(Users)
            if not users or user not in users:
                logger.warning(f"User '{user}' not found on system")
                return False

            user_details = users[user]
            home_dir = user_details.get("home", f"/home/{user}")
            authorized_keys_path = f"{home_dir}/.ssh/authorized_keys"

            # Check if authorized_keys file exists
            from pyinfra.facts.files import File

            file_info = host.get_fact(File, authorized_keys_path)
            if not file_info:
                logger.info(f"No authorized_keys file found for user {user}")
                return False

            # Read current authorized_keys content using cat command
            from pyinfra.facts.server import Command

            cat_result = host.get_fact(
                Command, f"cat {authorized_keys_path} 2>/dev/null || echo ''"
            )
            if not cat_result:
                logger.info(f"Could not read authorized_keys file for user {user}")
                return False

            current_content = str(cat_result).strip()
            if not current_content:
                logger.info(f"Empty authorized_keys file for user {user}")
                return False

            # Parse current keys and filter out the key to delete
            current_lines = current_content.strip().split("\n")
            remaining_keys = []

            # Extract the key part (ignore key type and comment) for comparison
            key_parts = key_to_delete.strip().split()
            if len(key_parts) < 2:
                raise SSHKeyDeleteError(f"Invalid SSH key format: {key_to_delete}")

            key_to_delete_data = key_parts[1]  # The actual key data

            for line in current_lines:
                line = line.strip()
                if not line or line.startswith("#"):
                    remaining_keys.append(line)
                    continue

                # Check if this line contains the key to delete
                line_parts = line.split()
                if len(line_parts) >= 2:
                    line_key_data = line_parts[1]
                    if line_key_data != key_to_delete_data:
                        remaining_keys.append(line)
                else:
                    remaining_keys.append(line)

            # Update the user's authorized_keys with only the remaining keys
            server.user_authorized_keys(
                name=f"Remove SSH key from {user}'s authorized_keys",
                user=user,
                public_keys=remaining_keys,
                delete_keys=True,  # Remove any keys not in our list
                _sudo=True if user != host.get_fact(User) else False,
            )

            removed_count = len(current_lines) - len(remaining_keys)
            if removed_count > 0:
                logger.info(f"Removed {removed_count} SSH key(s) from user {user}")
            else:
                logger.info(f"Key not found in {user}'s authorized_keys")

            return True

        except Exception as e:
            raise SSHKeyDeleteError(
                f"Error removing key from {user}'s authorized_keys: {str(e)}"
            )

    @deploy("Delete SSH keys from users' authorized_keys files")
    def delete_ssh_keys_for_users(
        self,
        users: List[str],
        filter_criteria: Optional[Dict[str, Any]] = None,
        force_refresh: bool = False,
    ) -> bool:
        """
        Delete SSH keys from specified users' authorized_keys files.

        Args:
            users: List of usernames to process
            filter_criteria: Dictionary with filtering criteria (labels, key_patterns, key_ids)
            force_refresh: If True, force a refresh of keys from API

        Returns:
            bool: True if operation completed successfully

        Raises:
            SSHKeyDeleteError: If there's no root access or other errors occur
        """
        try:
            # Check root access first
            if not self._check_root_access():
                raise SSHKeyDeleteError(
                    "Root access required to modify other users' authorized_keys files. "
                    "Please run as root or ensure sudo access."
                )

            # Get all SSH keys from the API
            all_keys = self.fetch_ssh_keys(force_refresh)
            if not all_keys:
                logger.info("No SSH keys found in API")
                return True

            # Filter keys based on criteria
            keys_to_delete = self.filter_keys_for_deletion(all_keys, filter_criteria)
            if not keys_to_delete:
                logger.info("No SSH keys match deletion criteria")
                return True

            logger.info(
                f"Found {len(keys_to_delete)} keys to delete for {len(users)} users"
            )

            # Process each user
            for user in users:
                logger.info(f"Processing user: {user}")
                keys_removed = 0

                # Try to remove each key from this user's authorized_keys
                for key in keys_to_delete:
                    try:
                        if self._remove_key_from_authorized_keys(user, key):
                            keys_removed += 1
                    except Exception as e:
                        logger.warning(
                            f"Failed to remove key for user {user}: {str(e)}"
                        )
                        continue

                logger.info(f"Processed {keys_removed} keys for user {user}")

            logger.info("SSH key deletion completed successfully")
            return True

        except Exception as e:
            raise SSHKeyDeleteError(f"Error during SSH key deletion: {str(e)}")

    @deploy("Delete specific SSH key from users' authorized_keys files")
    def delete_specific_key_for_users(
        self, users: List[str], key_to_delete: str
    ) -> bool:
        """
        Delete a specific SSH key from specified users' authorized_keys files.

        Args:
            users: List of usernames to process
            key_to_delete: The SSH key string to remove

        Returns:
            bool: True if operation completed successfully

        Raises:
            SSHKeyDeleteError: If there's no root access or other errors occur
        """
        try:
            # Check root access first
            if not self._check_root_access():
                raise SSHKeyDeleteError(
                    "Root access required to modify other users' authorized_keys files. "
                    "Please run as root or ensure sudo access."
                )

            logger.info(f"Deleting specific key for {len(users)} users")

            # Process each user
            for user in users:
                logger.info(f"Processing user: {user}")
                try:
                    if self._remove_key_from_authorized_keys(user, key_to_delete):
                        logger.info(
                            f"Successfully processed key removal for user {user}"
                        )
                    else:
                        logger.info(f"Key not found or user not found: {user}")
                except Exception as e:
                    logger.warning(f"Failed to remove key for user {user}: {str(e)}")
                    continue

            logger.info("Specific SSH key deletion completed successfully")
            return True

        except Exception as e:
            raise SSHKeyDeleteError(f"Error during specific SSH key deletion: {str(e)}")

    def clear_cache(self) -> bool:
        """
        Clear all cached credentials and keys.

        Returns:
            bool: True if cache was cleared successfully.

        Raises:
            SSHKeyDeleteError: If there is an error while clearing the cache
        """
        try:
            with self._lock:
                SSHKeyDeleter._credentials = None
                SSHKeyDeleter._ssh_keys = None
                SSHKeyDeleter._session_key = None
                logger.debug("Cache cleared")
                return True
        except Exception as e:
            raise SSHKeyDeleteError(f"Error clearing cache: {str(e)}")


# Global functions for backward compatibility and ease of use
def delete_ssh_keys_for_users(
    users: List[str],
    filter_criteria: Optional[Dict[str, Any]] = None,
    force_refresh: bool = False,
    **kwargs,
) -> Any:
    """
    Backward compatibility function that uses the singleton instance to delete keys for users.

    Args:
        users: List of usernames to process
        filter_criteria: Dictionary with filtering criteria (labels, key_patterns, key_ids)
        force_refresh: If True, force a refresh of keys from API
        **kwargs: Additional arguments to pass to SSHKeyDeleter constructor

    Returns:
        Any: Returns the OperationMeta object from the decorated delete_ssh_keys_for_users method.
    """
    deleter: SSHKeyDeleter = SSHKeyDeleter.get_instance(**kwargs)
    return deleter.delete_ssh_keys_for_users(users, filter_criteria, force_refresh)


def delete_specific_key_for_users(
    users: List[str], key_to_delete: str, **kwargs
) -> Any:
    """
    Backward compatibility function that uses the singleton instance to delete a specific key.

    Args:
        users: List of usernames to process
        key_to_delete: The SSH key string to remove
        **kwargs: Additional arguments to pass to SSHKeyDeleter constructor

    Returns:
        Any: Returns the OperationMeta object from the decorated delete_specific_key_for_users method.
    """
    deleter: SSHKeyDeleter = SSHKeyDeleter.get_instance(**kwargs)
    return deleter.delete_specific_key_for_users(users, key_to_delete)
