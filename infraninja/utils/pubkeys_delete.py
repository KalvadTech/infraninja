import logging
import threading
from typing import List, Optional

from pyinfra.context import host
from pyinfra.api.deploy import deploy
from pyinfra.facts.server import User, Users
from pyinfra.operations import server
from pyinfra.api.exceptions import PyinfraError
from infraninja.utils.pubkeys import SSHKeyManager, SSHKeyManagerError

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
)
logger = logging.getLogger(__name__)


class SSHKeyDeleter:
    """
    Manages SSH key deletion operations by removing keys from authorized_keys files.
    This class leverages the existing SSHKeyManager to fetch keys and then removes them.

    Usage:
        # Example usage of SSHKeyDeleter

        # Initialize the SSHKeyDeleter with API credentials
        key_deleter = SSHKeyDeleter(
            api_url="https://example.com/api",
            api_key="your_api_key_here"
        )

        # Delete SSH keys from the current user's authorized_keys
        key_deleter.delete_ssh_keys()
    """

    _lock: threading.RLock = threading.RLock()
    _instance: Optional["SSHKeyDeleter"] = None

    @classmethod
    def get_instance(cls, *args, **kwargs) -> "SSHKeyDeleter":
        """Get or create the singleton instance of SSHKeyDeleter."""
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
        # Initialize the SSH key manager to handle API communication
        self.key_manager = SSHKeyManager.get_instance(api_url=api_url, api_key=api_key)

    def fetch_keys_to_delete(self, force_refresh: bool = False) -> Optional[List[str]]:
        """
        Fetch SSH keys from the API that should be deleted.

        Args:
            force_refresh: If True, ignore cached keys and force a new fetch

        Returns:
            Optional[List[str]]: List of SSH public keys to delete or None if fetch fails

        Raises:
            SSHKeyManagerError: If keys cannot be fetched from the API
        """
        try:
            keys = self.key_manager.fetch_ssh_keys(force_refresh)
            if not keys:
                logger.warning("No SSH keys found to delete")
                return None

            logger.info(f"Found {len(keys)} SSH keys to delete")
            return keys

        except SSHKeyManagerError as e:
            logger.error(f"Failed to fetch SSH keys for deletion: {str(e)}")
            raise

    @deploy("Remove SSH keys from authorized_keys")
    def delete_ssh_keys(self, force_refresh: bool = False) -> bool:
        """
        Remove SSH keys from the authorized_keys file.

        Args:
            force_refresh: If True, force a refresh of SSH keys from API

        Returns:
            bool: True if keys were removed successfully, False otherwise

        Raises:
            SSHKeyManagerError: If keys cannot be fetched or there's an error during deletion
        """
        return self._delete_ssh_keys_impl(force_refresh)

    def _delete_ssh_keys_impl(self, force_refresh: bool = False) -> bool:
        """
        Internal implementation for removing SSH keys from the authorized_keys file.

        Args:
            force_refresh: If True, force a refresh of SSH keys from API

        Returns:
            bool: True if keys were removed successfully, False otherwise

        Raises:
            SSHKeyManagerError: If keys cannot be fetched or there's an error during deletion
        """
        try:
            # Get the SSH keys to delete
            keys_to_delete = self.fetch_keys_to_delete(force_refresh)
            if not keys_to_delete:
                logger.info("No SSH keys to delete")
                return True

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

            # Remove each SSH key from authorized_keys
            for i, key in enumerate(keys_to_delete):
                try:
                    # Extract just the key part (remove key type and comment if present)
                    key_parts = key.strip().split()
                    if len(key_parts) >= 2:
                        # Use the key type and key data, ignore comment
                        key_to_remove = f"{key_parts[0]} {key_parts[1]}"
                    else:
                        key_to_remove = key.strip()

                    server.user_authorized_keys(
                        name=f"Remove SSH key {i + 1} for {current_user}",
                        user=current_user,
                        group=user_details["group"],
                        public_keys=[key_to_remove],
                        delete_keys=True,  # This tells pyinfra to remove the keys
                    )

                    logger.debug(f"Removed SSH key {i + 1}/{len(keys_to_delete)}")

                except Exception as key_error:
                    logger.error(f"Failed to remove SSH key {i + 1}: {str(key_error)}")
                    # Continue with other keys even if one fails

            logger.info(
                "Successfully processed removal of %d SSH keys for user %s",
                len(keys_to_delete),
                current_user,
            )
            return True

        except KeyError as e:
            raise SSHKeyManagerError(f"Missing user information: {e}")
        except Exception as e:
            raise SSHKeyManagerError(f"Error removing SSH keys: {str(e)}")

    @deploy("Remove specific SSH keys from authorized_keys")
    def delete_specific_keys(self, keys_to_delete: List[str]) -> bool:
        """
        Remove specific SSH keys from the authorized_keys file.

        Args:
            keys_to_delete: List of SSH public keys to remove

        Returns:
            bool: True if keys were removed successfully, False otherwise

        Raises:
            SSHKeyManagerError: If there's an error during deletion
        """
        return self._delete_specific_keys_impl(keys_to_delete)

    def _delete_specific_keys_impl(self, keys_to_delete: List[str]) -> bool:
        """
        Internal implementation for removing specific SSH keys from the authorized_keys file.

        Args:
            keys_to_delete: List of SSH public keys to remove

        Returns:
            bool: True if keys were removed successfully, False otherwise

        Raises:
            SSHKeyManagerError: If there's an error during deletion
        """
        try:
            if not keys_to_delete:
                logger.info("No SSH keys provided for deletion")
                return True

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

            # Remove each SSH key from authorized_keys
            for i, key in enumerate(keys_to_delete):
                try:
                    # Extract just the key part (remove key type and comment if present)
                    key_parts = key.strip().split()
                    if len(key_parts) >= 2:
                        # Use the key type and key data, ignore comment
                        key_to_remove = f"{key_parts[0]} {key_parts[1]}"
                    else:
                        key_to_remove = key.strip()

                    server.user_authorized_keys(
                        name=f"Remove specific SSH key {i + 1} for {current_user}",
                        user=current_user,
                        group=user_details["group"],
                        public_keys=[key_to_remove],
                        delete_keys=True,  # This tells pyinfra to remove the keys
                    )

                    logger.debug(
                        f"Removed specific SSH key {i + 1}/{len(keys_to_delete)}"
                    )

                except Exception as key_error:
                    logger.error(
                        f"Failed to remove specific SSH key {i + 1}: {str(key_error)}"
                    )
                    # Continue with other keys even if one fails

            logger.info(
                "Successfully processed removal of %d specific SSH keys for user %s",
                len(keys_to_delete),
                current_user,
            )
            return True

        except KeyError as e:
            raise SSHKeyManagerError(f"Missing user information: {e}")
        except Exception as e:
            raise SSHKeyManagerError(f"Error removing specific SSH keys: {str(e)}")

    def clear_cache(self) -> bool:
        """
        Clear all cached credentials and keys from the underlying key manager.

        Returns:
            bool: True if cache was cleared successfully.

        Raises:
            SSHKeyManagerError: If there is an error while clearing the cache
        """
        return self.key_manager.clear_cache()


# Global functions for backward compatibility and ease of use
@deploy("Remove SSH keys from authorized_keys")
def delete_ssh_keys(force_refresh: bool = False, **kwargs) -> bool:
    """
    Backward compatibility function that uses the singleton instance to delete SSH keys.

    Args:
        force_refresh: If True, force a refresh of SSH keys from API

    Returns:
        bool: True if keys were removed successfully, False otherwise.
    """
    deleter: SSHKeyDeleter = SSHKeyDeleter.get_instance(**kwargs)
    # Call the internal method without the decorator
    return deleter._delete_ssh_keys_impl(force_refresh)


@deploy("Remove specific SSH keys from authorized_keys")
def delete_specific_ssh_keys(keys_to_delete: List[str], **kwargs) -> bool:
    """
    Delete specific SSH keys from authorized_keys.

    Args:
        keys_to_delete: List of SSH public keys to remove

    Returns:
        bool: True if keys were removed successfully, False otherwise.
    """
    deleter: SSHKeyDeleter = SSHKeyDeleter.get_instance(**kwargs)
    # Call the internal method without the decorator
    return deleter._delete_specific_keys_impl(keys_to_delete)
