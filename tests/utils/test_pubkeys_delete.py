import unittest
from unittest.mock import Mock, patch
import threading

from infraninja.utils.pubkeys_delete import SSHKeyDeletion, SSHKeyManagerError


class TestSSHKeyDeletion(unittest.TestCase):
    """Test cases for the SSHKeyDeletion class."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        # Clear singleton instance before each test
        SSHKeyDeletion._instance = None

    def tearDown(self):
        """Clean up after each test method."""
        # Clear singleton instance after each test
        SSHKeyDeletion._instance = None

    def test_singleton_pattern(self):
        """Test that SSHKeyDeletion follows singleton pattern."""
        deleter1 = SSHKeyDeletion.get_instance()
        deleter2 = SSHKeyDeletion.get_instance()

        self.assertIs(deleter1, deleter2, "Should return the same instance")

    def test_singleton_thread_safety(self):
        """Test that singleton pattern is thread-safe."""
        instances = []

        def create_instance():
            instances.append(SSHKeyDeletion.get_instance())

        # Create multiple threads
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=create_instance)
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # All instances should be the same
        first_instance = instances[0]
        for instance in instances:
            self.assertIs(instance, first_instance, "All instances should be the same")

    @patch("infraninja.utils.pubkeys_delete.SSHKeyManager")
    def test_initialization_with_parameters(self, mock_ssh_key_manager):
        """Test initialization with API URL and key parameters."""
        api_url = "https://test-api.com"
        api_key = "test-key"

        deleter = SSHKeyDeletion.get_instance(api_url=api_url, api_key=api_key)

        # Verify that SSHKeyManager.get_instance was called with correct parameters
        mock_ssh_key_manager.get_instance.assert_called_once_with(
            api_url=api_url, api_key=api_key
        )

        self.assertIsNotNone(deleter)

    @patch("infraninja.utils.pubkeys_delete.SSHKeyManager")
    def test_fetch_keys_to_delete_success(self, mock_ssh_key_manager_class):
        """Test successful fetching of keys to delete."""
        # Mock the SSHKeyManager instance
        mock_manager = Mock()
        mock_ssh_key_manager_class.get_instance.return_value = mock_manager

        # Mock the fetch_ssh_keys method
        test_keys = [
            "ssh-rsa AAAAB3NzaC1yc2ETEST1 user@test.com",
            "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5TEST2 user2@test.com",
        ]
        mock_manager.fetch_ssh_keys.return_value = test_keys

        deleter = SSHKeyDeletion.get_instance()
        keys = deleter.fetch_keys_to_delete(force_refresh=True)

        self.assertEqual(keys, test_keys)
        mock_manager.fetch_ssh_keys.assert_called_once_with(True)

    @patch("infraninja.utils.pubkeys_delete.SSHKeyManager")
    def test_fetch_keys_to_delete_no_keys(self, mock_ssh_key_manager_class):
        """Test fetching keys when no keys are available."""
        # Mock the SSHKeyManager instance
        mock_manager = Mock()
        mock_ssh_key_manager_class.get_instance.return_value = mock_manager

        # Mock empty keys response
        mock_manager.fetch_ssh_keys.return_value = None

        deleter = SSHKeyDeletion.get_instance()
        keys = deleter.fetch_keys_to_delete()

        self.assertIsNone(keys)
        mock_manager.fetch_ssh_keys.assert_called_once_with(False)

    @patch("infraninja.utils.pubkeys_delete.SSHKeyManager")
    def test_fetch_keys_to_delete_api_error(self, mock_ssh_key_manager_class):
        """Test handling of API errors when fetching keys."""
        # Mock the SSHKeyManager instance
        mock_manager = Mock()
        mock_ssh_key_manager_class.get_instance.return_value = mock_manager

        # Mock API error
        mock_manager.fetch_ssh_keys.side_effect = SSHKeyManagerError("API Error")

        deleter = SSHKeyDeletion.get_instance()

        with self.assertRaises(SSHKeyManagerError):
            deleter.fetch_keys_to_delete()

    @patch("infraninja.utils.pubkeys_delete.SSHKeyManager")
    def test_clear_cache(self, mock_ssh_key_manager_class):
        """Test cache clearing functionality."""
        # Mock the SSHKeyManager instance
        mock_manager = Mock()
        mock_ssh_key_manager_class.get_instance.return_value = mock_manager
        mock_manager.clear_cache.return_value = True

        deleter = SSHKeyDeletion.get_instance()
        result = deleter.clear_cache()

        self.assertTrue(result)
        mock_manager.clear_cache.assert_called_once()

    def test_key_processing_format(self):
        """Test that SSH key format processing works correctly."""
        # This would test the internal key processing logic
        # For now, we'll just test that the methods exist and can be called
        deleter = SSHKeyDeletion.get_instance()

        # Verify that the methods exist
        self.assertTrue(hasattr(deleter, "_delete_ssh_keys_impl"))
        self.assertTrue(hasattr(deleter, "_delete_specific_keys_impl"))
        self.assertTrue(hasattr(deleter, "fetch_keys_to_delete"))
        self.assertTrue(hasattr(deleter, "clear_cache"))


class TestGlobalFunctions(unittest.TestCase):
    """Test cases for the global functions."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        # Clear singleton instance before each test
        SSHKeyDeletion._instance = None

    def tearDown(self):
        """Clean up after each test method."""
        # Clear singleton instance after each test
        SSHKeyDeletion._instance = None

    def test_global_functions_exist(self):
        """Test that global functions are available."""
        from infraninja.utils.pubkeys_delete import (
            delete_ssh_keys,
            delete_specific_ssh_keys,
        )

        # Verify functions are callable
        self.assertTrue(callable(delete_ssh_keys))
        self.assertTrue(callable(delete_specific_ssh_keys))

    @patch("infraninja.utils.pubkeys_delete.SSHKeyDeletion")
    def test_delete_ssh_keys_global(self, mock_deleter_class):
        """Test the global delete_ssh_keys function."""
        from infraninja.utils.pubkeys_delete import delete_ssh_keys

        # Mock the deleter instance
        mock_deleter = Mock()
        mock_deleter_class.get_instance.return_value = mock_deleter
        mock_deleter._delete_ssh_keys_impl.return_value = True

        # This would normally be called in a pyinfra deployment context
        # For testing, we just verify the function exists and can be imported
        self.assertTrue(callable(delete_ssh_keys))

    @patch("infraninja.utils.pubkeys_delete.SSHKeyDeletion")
    def test_delete_specific_ssh_keys_global(self, mock_deleter_class):
        """Test the global delete_specific_ssh_keys function."""
        from infraninja.utils.pubkeys_delete import delete_specific_ssh_keys

        # Mock the deleter instance
        mock_deleter = Mock()
        mock_deleter_class.get_instance.return_value = mock_deleter
        mock_deleter._delete_specific_keys_impl.return_value = True

        # This would normally be called in a pyinfra deployment context
        # For testing, we just verify the function exists and can be imported
        self.assertTrue(callable(delete_specific_ssh_keys))


if __name__ == "__main__":
    unittest.main()
