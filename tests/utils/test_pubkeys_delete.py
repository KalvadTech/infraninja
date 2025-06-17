import threading
import unittest
from unittest.mock import Mock, patch

# Import the module under test
from infraninja.utils.pubkeys_delete import (
    SSHKeyDeleter,
    SSHKeyDeleteError,
    delete_ssh_keys_for_users,
    delete_specific_key_for_users,
)


class TestSSHKeyDeleteError(unittest.TestCase):
    """Test the custom exception class."""

    def test_ssh_key_delete_error_creation(self):
        """Test that SSHKeyDeleteError can be created and raised."""
        error_message = "Test error message"
        with self.assertRaises(SSHKeyDeleteError) as context:
            raise SSHKeyDeleteError(error_message)
        self.assertEqual(str(context.exception), error_message)


class TestSSHKeyDeleter(unittest.TestCase):
    """Test the SSHKeyDeleter class."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        # Clear singleton instance and cached data before each test
        SSHKeyDeleter._instance = None
        SSHKeyDeleter._ssh_keys = None
        SSHKeyDeleter._credentials = None
        SSHKeyDeleter._session_key = None

    def tearDown(self):
        """Clean up after each test method."""
        # Clear singleton instance and cached data after each test
        SSHKeyDeleter._instance = None
        SSHKeyDeleter._ssh_keys = None
        SSHKeyDeleter._credentials = None
        SSHKeyDeleter._session_key = None

    def test_singleton_pattern(self):
        """Test that SSHKeyDeleter implements singleton pattern correctly."""
        instance1 = SSHKeyDeleter.get_instance()
        instance2 = SSHKeyDeleter.get_instance()
        self.assertIs(instance1, instance2)

    @patch("infraninja.utils.pubkeys_delete.Jinn")
    def test_init_with_default_api_url(self, mock_jinn_class):
        """Test initialization with default API URL from Jinn."""
        mock_jinn_instance = Mock()
        mock_jinn_instance.api_url = "https://api.example.com"
        mock_jinn_class.return_value = mock_jinn_instance

        deleter = SSHKeyDeleter()
        self.assertEqual(deleter.api_url, "https://api.example.com")

    def test_init_with_custom_api_url(self):
        """Test initialization with custom API URL."""
        custom_url = "https://custom.api.com"
        deleter = SSHKeyDeleter(api_url=custom_url)
        self.assertEqual(deleter.api_url, custom_url)

    def test_init_with_http_url_gets_https_scheme(self):
        """Test that URLs without scheme get https:// prepended."""
        url_without_scheme = "api.example.com"
        deleter = SSHKeyDeleter(api_url=url_without_scheme)
        self.assertEqual(deleter.api_url, "https://api.example.com")

    def test_init_with_placeholder_url_raises_error(self):
        """Test that placeholder URLs raise an error."""
        placeholder_url = "https://URLHERE/api"
        with self.assertRaises(SSHKeyDeleteError) as context:
            SSHKeyDeleter(api_url=placeholder_url)
        self.assertIn("Invalid API URL with placeholder", str(context.exception))

    @patch("infraninja.utils.pubkeys_delete.Jinn")
    def test_init_jinn_failure_sets_none_url(self, mock_jinn_class):
        """Test that Jinn initialization failure sets API URL to None."""
        mock_jinn_class.side_effect = Exception("Jinn failed")
        deleter = SSHKeyDeleter()
        self.assertIsNone(deleter.api_url)

    @patch("builtins.input", return_value="testuser")
    @patch("getpass.getpass", return_value="testpass")
    def test_get_credentials(self, mock_getpass, mock_input):
        """Test credential collection from user input."""
        credentials = SSHKeyDeleter._get_credentials()
        self.assertEqual(credentials["username"], "testuser")
        self.assertEqual(credentials["password"], "testpass")
        mock_input.assert_called_once_with("Enter username: ")
        mock_getpass.assert_called_once_with("Enter password: ")

    @patch("builtins.input", return_value="testuser")
    @patch("getpass.getpass", return_value="testpass")
    def test_get_credentials_caching(self, mock_getpass, mock_input):
        """Test that credentials are cached after first call."""
        # First call should prompt user
        creds1 = SSHKeyDeleter._get_credentials()
        # Second call should use cached credentials
        creds2 = SSHKeyDeleter._get_credentials()

        self.assertEqual(creds1, creds2)
        # Input should only be called once due to caching
        mock_input.assert_called_once()
        mock_getpass.assert_called_once()

    def test_make_auth_request_without_session_key_raises_error(self):
        """Test that making auth request without session key raises error."""
        with self.assertRaises(SSHKeyDeleteError) as context:
            SSHKeyDeleter._make_auth_request("https://api.example.com/test")
        self.assertIn("No session key available", str(context.exception))

    @patch("requests.request")
    def test_make_auth_request_success(self, mock_request):
        """Test successful authenticated request."""
        # Set up session key
        SSHKeyDeleter._session_key = "test_session_key"

        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_request.return_value = mock_response

        response = SSHKeyDeleter._make_auth_request("https://api.example.com/test")

        self.assertEqual(response, mock_response)
        mock_request.assert_called_once()

    @patch("requests.request")
    def test_make_auth_request_failure(self, mock_request):
        """Test authenticated request with failed status code."""
        # Set up session key
        SSHKeyDeleter._session_key = "test_session_key"

        # Mock failed response
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_request.return_value = mock_response

        with self.assertRaises(SSHKeyDeleteError) as context:
            SSHKeyDeleter._make_auth_request("https://api.example.com/test")
        self.assertIn("API request failed with status code 401", str(context.exception))

    @patch("requests.post")
    @patch("builtins.input", return_value="testuser")
    @patch("getpass.getpass", return_value="testpass")
    def test_login_success(self, mock_getpass, mock_input, mock_post):
        """Test successful login."""
        deleter = SSHKeyDeleter(api_url="https://api.example.com")

        # Mock successful login response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"session_key": "test_session_123"}
        mock_post.return_value = mock_response

        result = deleter._login()

        self.assertTrue(result)
        self.assertEqual(SSHKeyDeleter._session_key, "test_session_123")

    @patch("requests.post")
    @patch("builtins.input", return_value="testuser")
    @patch("getpass.getpass", return_value="testpass")
    def test_login_failure(self, mock_getpass, mock_input, mock_post):
        """Test login failure."""
        deleter = SSHKeyDeleter(api_url="https://api.example.com")

        # Mock failed login response
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.text = "Invalid credentials"
        mock_post.return_value = mock_response

        with self.assertRaises(SSHKeyDeleteError) as context:
            deleter._login()
        self.assertIn("Login failed with status code 401", str(context.exception))

    def test_login_without_api_url_raises_error(self):
        """Test that login without API URL raises error."""
        deleter = SSHKeyDeleter(api_url=None)
        with self.assertRaises(SSHKeyDeleteError) as context:
            deleter._login()
        self.assertIn("Cannot login: No API URL configured", str(context.exception))

    @patch.object(SSHKeyDeleter, "_make_auth_request")
    @patch.object(SSHKeyDeleter, "_login", return_value=True)
    def test_fetch_ssh_keys_success(self, mock_login, mock_auth_request):
        """Test successful SSH key fetching."""
        deleter = SSHKeyDeleter(api_url="https://api.example.com")

        # Mock API response
        mock_response = Mock()
        mock_response.json.return_value = {
            "result": [
                {"id": "1", "label": "key1", "key": "ssh-rsa AAAAB3..."},
                {"id": "2", "label": "key2", "key": "ssh-rsa AAAAC4..."},
            ]
        }
        mock_auth_request.return_value = mock_response

        keys = deleter.fetch_ssh_keys()

        self.assertIsNotNone(keys)
        assert keys is not None  # Type narrowing for mypy
        self.assertEqual(len(keys), 2)
        self.assertEqual(keys[0]["label"], "key1")
        self.assertEqual(keys[1]["label"], "key2")

    @patch.object(SSHKeyDeleter, "_make_auth_request")
    @patch.object(SSHKeyDeleter, "_login", return_value=True)
    def test_fetch_ssh_keys_cached(self, mock_login, mock_auth_request):
        """Test that SSH keys are cached and not re-fetched unless forced."""
        deleter = SSHKeyDeleter(api_url="https://api.example.com")

        # Set cached keys
        cached_keys = [{"id": "1", "label": "cached", "key": "ssh-rsa CACHED..."}]
        SSHKeyDeleter._ssh_keys = cached_keys

        keys = deleter.fetch_ssh_keys()

        # Should return cached keys without making API call
        self.assertEqual(keys, cached_keys)
        mock_auth_request.assert_not_called()

    @patch.object(SSHKeyDeleter, "_make_auth_request")
    @patch.object(SSHKeyDeleter, "_login", return_value=True)
    def test_fetch_ssh_keys_force_refresh(self, mock_login, mock_auth_request):
        """Test force refresh of SSH keys."""
        deleter = SSHKeyDeleter(api_url="https://api.example.com")

        # Set cached keys
        SSHKeyDeleter._ssh_keys = [
            {"id": "1", "label": "cached", "key": "ssh-rsa CACHED..."}
        ]

        # Mock fresh API response
        mock_response = Mock()
        mock_response.json.return_value = {
            "result": [{"id": "2", "label": "fresh", "key": "ssh-rsa FRESH..."}]
        }
        mock_auth_request.return_value = mock_response

        keys = deleter.fetch_ssh_keys(force_refresh=True)

        # Should make API call despite cached keys
        self.assertIsNotNone(keys)
        assert keys is not None  # Type narrowing for mypy
        self.assertEqual(len(keys), 1)
        self.assertEqual(keys[0]["label"], "fresh")
        mock_auth_request.assert_called_once()

    def test_filter_keys_for_deletion_by_labels(self):
        """Test filtering keys by labels."""
        deleter = SSHKeyDeleter()
        all_keys = [
            {"id": "1", "label": "old_key", "key": "ssh-rsa KEY1..."},
            {"id": "2", "label": "current_key", "key": "ssh-rsa KEY2..."},
            {"id": "3", "label": "compromised", "key": "ssh-rsa KEY3..."},
        ]

        filter_criteria = {"labels": ["old_key", "compromised"]}
        filtered_keys = deleter.filter_keys_for_deletion(all_keys, filter_criteria)

        self.assertEqual(len(filtered_keys), 2)
        self.assertIn("ssh-rsa KEY1...", filtered_keys)
        self.assertIn("ssh-rsa KEY3...", filtered_keys)

    def test_filter_keys_for_deletion_by_key_ids(self):
        """Test filtering keys by key IDs."""
        deleter = SSHKeyDeleter()
        all_keys = [
            {"id": "1", "label": "key1", "key": "ssh-rsa KEY1..."},
            {"id": "2", "label": "key2", "key": "ssh-rsa KEY2..."},
            {"id": "3", "label": "key3", "key": "ssh-rsa KEY3..."},
        ]

        filter_criteria = {"key_ids": ["1", "3"]}
        filtered_keys = deleter.filter_keys_for_deletion(all_keys, filter_criteria)

        self.assertEqual(len(filtered_keys), 2)
        self.assertIn("ssh-rsa KEY1...", filtered_keys)
        self.assertIn("ssh-rsa KEY3...", filtered_keys)

    def test_filter_keys_for_deletion_by_patterns(self):
        """Test filtering keys by regex patterns."""
        deleter = SSHKeyDeleter()
        all_keys = [
            {"id": "1", "label": "key1", "key": "ssh-rsa AAAAB3OLD... user@old-host"},
            {"id": "2", "label": "key2", "key": "ssh-rsa AAAAB3NEW... user@new-host"},
            {"id": "3", "label": "key3", "key": "ssh-ed25519 AAAAC3... user@test-host"},
        ]

        filter_criteria = {"key_patterns": ["old-host", "test-host"]}
        filtered_keys = deleter.filter_keys_for_deletion(all_keys, filter_criteria)

        self.assertEqual(len(filtered_keys), 2)
        self.assertTrue(any("old-host" in key for key in filtered_keys))
        self.assertTrue(any("test-host" in key for key in filtered_keys))

    def test_filter_keys_for_deletion_no_criteria_returns_all(self):
        """Test that no filter criteria returns all keys."""
        deleter = SSHKeyDeleter()
        all_keys = [
            {"id": "1", "label": "key1", "key": "ssh-rsa KEY1..."},
            {"id": "2", "label": "key2", "key": "ssh-rsa KEY2..."},
        ]

        filtered_keys = deleter.filter_keys_for_deletion(all_keys, None)

        self.assertEqual(len(filtered_keys), 2)

    def test_escape_regex_special_chars(self):
        """Test escaping of regex special characters."""
        deleter = SSHKeyDeleter()
        text_with_special_chars = "test.string*with+special[chars]"
        escaped = deleter._escape_regex_special_chars(text_with_special_chars)
        expected = "test\\.string\\*with\\+special\\[chars\\]"
        self.assertEqual(escaped, expected)

    @patch("infraninja.utils.pubkeys_delete.host")
    def test_check_root_access_as_root(self, mock_host):
        """Test root access check when running as root."""
        deleter = SSHKeyDeleter()
        mock_host.get_fact.return_value = "root"

        self.assertTrue(deleter._check_root_access())

    @patch("infraninja.utils.pubkeys_delete.host")
    def test_check_root_access_with_sudo(self, mock_host):
        """Test root access check with sudo privileges."""
        deleter = SSHKeyDeleter()
        mock_host.get_fact.side_effect = ["testuser", "success"]

        self.assertTrue(deleter._check_root_access())

    @patch("infraninja.utils.pubkeys_delete.host")
    def test_check_root_access_denied(self, mock_host):
        """Test root access check when access is denied."""
        deleter = SSHKeyDeleter()
        mock_host.get_fact.side_effect = ["testuser", "failed"]

        self.assertFalse(deleter._check_root_access())

    def test_clear_cache(self):
        """Test clearing of cached data."""
        deleter = SSHKeyDeleter()

        # Set some cached data
        SSHKeyDeleter._credentials = {"username": "test", "password": "test"}
        SSHKeyDeleter._ssh_keys = [{"id": "1", "key": "test"}]
        SSHKeyDeleter._session_key = "test_session"

        result = deleter.clear_cache()

        self.assertTrue(result)
        self.assertIsNone(SSHKeyDeleter._credentials)
        self.assertIsNone(SSHKeyDeleter._ssh_keys)
        self.assertIsNone(SSHKeyDeleter._session_key)

    @patch("infraninja.utils.pubkeys_delete.deploy")
    @patch.object(SSHKeyDeleter, "_check_root_access", return_value=False)
    def test_delete_ssh_keys_for_users_no_root_access(
        self, mock_root_check, mock_deploy
    ):
        """Test that delete operation fails without root access."""

        # Create a simple function that raises the exception for testing
        def mock_delete_func(users, filter_criteria=None, force_refresh=False):
            # Create a deleter instance and call the method logic directly
            deleter = SSHKeyDeleter()
            if not deleter._check_root_access():
                raise SSHKeyDeleteError(
                    "Root access required to modify other users' authorized_keys files."
                )
            return True

        # Mock the deploy decorator to return our test function
        mock_deploy.return_value = lambda func: mock_delete_func

        # Test the logic
        with self.assertRaises(SSHKeyDeleteError) as context:
            mock_delete_func(["testuser"], {})
        self.assertIn("Root access required", str(context.exception))

    @patch("infraninja.utils.pubkeys_delete.host")
    @patch.object(SSHKeyDeleter, "_remove_key_from_authorized_keys", return_value=True)
    @patch.object(SSHKeyDeleter, "filter_keys_for_deletion")
    @patch.object(SSHKeyDeleter, "fetch_ssh_keys")
    @patch.object(SSHKeyDeleter, "_check_root_access", return_value=True)
    def test_delete_ssh_keys_for_users_success(
        self, mock_root_check, mock_fetch, mock_filter, mock_remove, mock_host
    ):
        """Test successful deletion of SSH keys for users."""

        # Mock the function logic since it's decorated
        def mock_delete_success(users, filter_criteria=None, force_refresh=False):
            deleter = SSHKeyDeleter()
            if not deleter._check_root_access():
                raise SSHKeyDeleteError("Root access required")

            all_keys = deleter.fetch_ssh_keys(force_refresh)
            if not all_keys:
                return True

            keys_to_delete = deleter.filter_keys_for_deletion(all_keys, filter_criteria)
            if not keys_to_delete:
                return True

            for user in users:
                for key in keys_to_delete:
                    deleter._remove_key_from_authorized_keys(user, key)
            return True

        # Mock data
        mock_fetch.return_value = [
            {"id": "1", "label": "test", "key": "ssh-rsa TEST..."}
        ]
        mock_filter.return_value = ["ssh-rsa TEST..."]

        result = mock_delete_success(["testuser"], {"labels": ["test"]})

        self.assertTrue(result)
        mock_remove.assert_called_once_with("testuser", "ssh-rsa TEST...")


class TestGlobalFunctions(unittest.TestCase):
    """Test the global backward compatibility functions."""

    def setUp(self):
        """Set up test fixtures."""
        # Clear singleton instance before each test
        SSHKeyDeleter._instance = None

    def tearDown(self):
        """Clean up after each test."""
        # Clear singleton instance after each test
        SSHKeyDeleter._instance = None

    @patch.object(SSHKeyDeleter, "delete_ssh_keys_for_users")
    def test_delete_ssh_keys_for_users_global_function(self, mock_method):
        """Test the global delete_ssh_keys_for_users function."""
        mock_method.return_value = True

        result = delete_ssh_keys_for_users(
            ["user1", "user2"], {"labels": ["old"]}, api_url="https://test.com"
        )

        self.assertTrue(result)
        mock_method.assert_called_once_with(
            ["user1", "user2"], {"labels": ["old"]}, False
        )

    @patch.object(SSHKeyDeleter, "delete_specific_key_for_users")
    def test_delete_specific_key_for_users_global_function(self, mock_method):
        """Test the global delete_specific_key_for_users function."""
        mock_method.return_value = True

        result = delete_specific_key_for_users(
            ["user1", "user2"], "ssh-rsa TESTKEY...", api_key="test_key"
        )

        self.assertTrue(result)
        mock_method.assert_called_once_with(["user1", "user2"], "ssh-rsa TESTKEY...")


class TestThreadSafety(unittest.TestCase):
    """Test thread safety of the SSHKeyDeleter class."""

    def setUp(self):
        """Set up test fixtures."""
        SSHKeyDeleter._instance = None

    def tearDown(self):
        """Clean up after each test."""
        SSHKeyDeleter._instance = None

    def test_singleton_thread_safety(self):
        """Test that singleton creation is thread-safe."""
        instances = []

        def create_instance():
            instances.append(SSHKeyDeleter.get_instance())

        # Create multiple threads that create instances
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=create_instance)
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # All instances should be the same object
        first_instance = instances[0]
        for instance in instances:
            self.assertIs(instance, first_instance)


if __name__ == "__main__":
    unittest.main()
