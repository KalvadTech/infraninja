import sys
import json
import unittest
import requests
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from infraninja.utils.pubkeys import SSHKeyManager


class TestSSHKeyManager(unittest.TestCase):
    """Test cases for the SSHKeyManager class."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        # Mock API configuration
        self.api_url = "https://test-api.example.com"
        self.api_key = "test-api-key"
        
        # Mock credentials
        self.username = "testuser"
        self.password = "testpassword"
        
        # Mock session key
        self.session_key = "test-session-key"
        
        # Sample SSH keys for testing
        self.sample_ssh_keys = [
            "ssh-rsa AAAA... user1@example.com",
            "ssh-ed25519 AAAA... user2@example.com"
        ]
        
        self.ssh_keys_response = {
            "result": [
                {"id": 1, "key": self.sample_ssh_keys[0], "user": "user1"},
                {"id": 2, "key": self.sample_ssh_keys[1], "user": "user2"}
            ]
        }
        
        # Set up patches
        self.patchers = []
        
        # Patch requests.request for API calls
        requests_request_patcher = patch('requests.request')
        self.mock_requests_request = requests_request_patcher.start()
        self.patchers.append(requests_request_patcher)
        
        # Patch requests.post for login
        requests_post_patcher = patch('requests.post')
        self.mock_requests_post = requests_post_patcher.start()
        self.patchers.append(requests_post_patcher)
        
        # Patch input and getpass for credentials
        input_patcher = patch('builtins.input', return_value=self.username)
        self.mock_input = input_patcher.start()
        self.patchers.append(input_patcher)
        
        getpass_patcher = patch('getpass.getpass', return_value=self.password)
        self.mock_getpass = getpass_patcher.start()
        self.patchers.append(getpass_patcher)
        
        # Set up mock responses
        self.mock_login_response = MagicMock()
        self.mock_login_response.status_code = 200
        self.mock_login_response.json.return_value = {"session_key": self.session_key}
        
        self.mock_ssh_keys_response = MagicMock()
        self.mock_ssh_keys_response.status_code = 200
        self.mock_ssh_keys_response.json.return_value = self.ssh_keys_response
        
        # Configure mock responses
        self.mock_requests_post.return_value = self.mock_login_response
        self.mock_requests_request.return_value = self.mock_ssh_keys_response
        
        # Create a test instance of SSHKeyManager
        self.key_manager = SSHKeyManager(api_url=self.api_url, api_key=self.api_key)
        
        # Reset the singleton instance between tests
        SSHKeyManager._instance = None
        SSHKeyManager._ssh_keys = None
        SSHKeyManager._credentials = None
        SSHKeyManager._session_key = None

    def tearDown(self):
        """Tear down test fixtures after each test method."""
        # Stop all patches
        for patcher in self.patchers:
            patcher.stop()
        
        # Reset the singleton instance
        SSHKeyManager._instance = None
        SSHKeyManager._ssh_keys = None
        SSHKeyManager._credentials = None
        SSHKeyManager._session_key = None

    def test_singleton_pattern(self):
        """Test that the SSHKeyManager follows the singleton pattern."""
        # Create two instances
        manager1 = SSHKeyManager.get_instance()
        manager2 = SSHKeyManager.get_instance()
        
        # They should be the same object
        self.assertIs(manager1, manager2)
        
        # The instance should be stored in the class
        self.assertIs(manager1, SSHKeyManager._instance)

    def test_get_credentials(self):
        """Test the _get_credentials method."""
        # Get credentials for the first time
        credentials = self.key_manager._get_credentials()
        
        # Verify credentials were obtained from user input
        self.assertEqual(credentials, {"username": self.username, "password": self.password})
        self.mock_input.assert_called_once_with("Enter username: ")
        self.mock_getpass.assert_called_once_with("Enter password: ")
        
        # Reset mocks
        self.mock_input.reset_mock()
        self.mock_getpass.reset_mock()
        
        # Get credentials again
        credentials = self.key_manager._get_credentials()
        
        # Verify cached credentials were used (no more input calls)
        self.assertEqual(credentials, {"username": self.username, "password": self.password})
        self.mock_input.assert_not_called()
        self.mock_getpass.assert_not_called()

    def test_login_success(self):
        """Test successful login."""
        # Try to login
        result = self.key_manager._login()
        
        # Verify login was successful
        self.assertTrue(result)
        self.assertEqual(self.key_manager._session_key, self.session_key)
        
        # Check API call
        self.mock_requests_post.assert_called_once_with(
            f"{self.api_url}/login/",
            json={"username": self.username, "password": self.password},
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            timeout=30
        )

    def test_login_failure(self):
        """Test login failure."""
        # Configure mock to return 401
        self.mock_login_response.status_code = 401
        
        # Try to login
        result = self.key_manager._login()
        
        # Verify login failed
        self.assertFalse(result)
        self.assertIsNone(self.key_manager._session_key)

    def test_login_exceptions(self):
        """Test login with exceptions."""
        # Test various exceptions
        exceptions = [
            requests.exceptions.Timeout("Timeout"),
            requests.exceptions.ConnectionError("Connection Error"),
            json.JSONDecodeError("Invalid JSON", "", 0),
            requests.exceptions.RequestException("Request Error")
        ]
        
        for exception in exceptions:
            # Configure mock to raise exception
            self.mock_requests_post.side_effect = exception
            
            # Try to login
            result = self.key_manager._login()
            
            # Verify login failed
            self.assertFalse(result)
            self.assertIsNone(self.key_manager._session_key)
            
        # Reset side effect
        self.mock_requests_post.side_effect = None

    def test_make_auth_request_no_session(self):
        """Test _make_auth_request with no session key."""
        # Try to make request without login
        self.key_manager._session_key = None
        response = self.key_manager._make_auth_request(f"{self.api_url}/test/")
        
        # Verify no request was made
        self.assertIsNone(response)
        self.mock_requests_request.assert_not_called()

    def test_make_auth_request_success(self):
        """Test successful _make_auth_request."""
        # Set session key
        self.key_manager._session_key = self.session_key
        
        # Make request
        endpoint = f"{self.api_url}/test/"
        response = self.key_manager._make_auth_request(endpoint)
        
        # Verify request was made correctly
        self.assertEqual(response, self.mock_ssh_keys_response)
        self.mock_requests_request.assert_called_once_with(
            "get",
            endpoint,
            headers={
                "Authorization": f"Bearer {self.session_key}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            },
            cookies={"sessionid": self.session_key},
            timeout=30
        )

    def test_make_auth_request_failure(self):
        """Test failed _make_auth_request."""
        # Set session key
        self.key_manager._session_key = self.session_key
        
        # Configure mock to return non-200
        self.mock_ssh_keys_response.status_code = 404
        
        # Make request
        response = self.key_manager._make_auth_request(f"{self.api_url}/test/")
        
        # Verify request failed
        self.assertIsNone(response)

    def test_make_auth_request_exceptions(self):
        """Test _make_auth_request with exceptions."""
        # Set session key
        self.key_manager._session_key = self.session_key
        
        # Test various exceptions
        exceptions = [
            requests.exceptions.Timeout("Timeout"),
            requests.exceptions.ConnectionError("Connection Error"),
            requests.exceptions.RequestException("Request Error")
        ]
        
        for exception in exceptions:
            # Configure mock to raise exception
            self.mock_requests_request.side_effect = exception
            
            # Make request
            response = self.key_manager._make_auth_request(f"{self.api_url}/test/")
            
            # Verify request failed
            self.assertIsNone(response)
            
        # Reset side effect
        self.mock_requests_request.side_effect = None

    def test_fetch_ssh_keys_success(self):
        """Test successful fetch_ssh_keys."""
        # Set up mocks for login and request
        with patch.object(self.key_manager, '_login', return_value=True):
            # Fetch SSH keys
            keys = self.key_manager.fetch_ssh_keys()
            
            # Verify keys were extracted correctly
            self.assertEqual(keys, self.sample_ssh_keys)
            self.assertEqual(self.key_manager._ssh_keys, self.sample_ssh_keys)

    def test_fetch_ssh_keys_login_failure(self):
        """Test fetch_ssh_keys with login failure."""
        # Configure login to fail
        with patch.object(self.key_manager, '_login', return_value=False):
            # Try to fetch keys
            keys = self.key_manager.fetch_ssh_keys()
            
            # Verify fetch failed
            self.assertIsNone(keys)

    def test_fetch_ssh_keys_request_failure(self):
        """Test fetch_ssh_keys with request failure."""
        # Configure login to succeed but request to fail
        with patch.object(self.key_manager, '_login', return_value=True), \
             patch.object(self.key_manager, '_make_auth_request', return_value=None):
            # Try to fetch keys
            keys = self.key_manager.fetch_ssh_keys()
            
            # Verify fetch failed
            self.assertIsNone(keys)

    def test_fetch_ssh_keys_invalid_response(self):
        """Test fetch_ssh_keys with invalid API response."""
        # Configure login to succeed but response to be invalid
        with patch.object(self.key_manager, '_login', return_value=True):
            # Test missing 'result' field
            self.mock_ssh_keys_response.json.return_value = {}
            keys = self.key_manager.fetch_ssh_keys()
            self.assertIsNone(keys)
            
            # Test missing 'key' field in item
            self.mock_ssh_keys_response.json.return_value = {"result": [{"id": 1}]}
            keys = self.key_manager.fetch_ssh_keys()
            self.assertEqual(keys, [])
            
            # Test JSON decode error
            self.mock_ssh_keys_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
            keys = self.key_manager.fetch_ssh_keys()
            self.assertIsNone(keys)
            
            # Test generic exception
            self.mock_ssh_keys_response.json.side_effect = Exception("Unexpected error")
            keys = self.key_manager.fetch_ssh_keys()
            self.assertIsNone(keys)
            
            # Reset side effect
            self.mock_ssh_keys_response.json.side_effect = None

    def test_fetch_ssh_keys_cached(self):
        """Test fetch_ssh_keys using cached keys."""
        # Set cached keys
        self.key_manager._ssh_keys = ["cached-key"]
        
        # Fetch without force_refresh
        keys = self.key_manager.fetch_ssh_keys(force_refresh=False)
        
        # Verify cached keys were returned without API call
        self.assertEqual(keys, ["cached-key"])
        self.mock_requests_request.assert_not_called()
        
        # Fetch with force_refresh
        with patch.object(self.key_manager, '_login', return_value=True):
            keys = self.key_manager.fetch_ssh_keys(force_refresh=True)
            
            # Verify fresh keys were fetched
            self.assertEqual(keys, self.sample_ssh_keys)
            self.mock_requests_request.assert_called()

    @patch('pyinfra.context.host')
    def test_add_ssh_keys_success(self, mock_host):
        """Test successful add_ssh_keys."""
        # Set up mocks for fetch_ssh_keys and pyinfra facts
        with patch.object(self.key_manager, 'fetch_ssh_keys', return_value=self.sample_ssh_keys), \
             patch('pyinfra.operations.server.user_authorized_keys') as mock_user_auth_keys:
            
            # Setup host facts
            mock_host.get_fact.side_effect = [
                'testuser',  # User fact
                {'testuser': {'group': 'testgroup'}}  # Users fact
            ]
            
            # Add SSH keys
            result = self.key_manager.add_ssh_keys()
            
            # Verify keys were added correctly
            self.assertTrue(result)
            mock_user_auth_keys.assert_called_once_with(
                name='Add SSH keys for testuser',
                user='testuser',
                group='testgroup',
                public_keys=self.sample_ssh_keys,
                delete_keys=False
            )

    @patch('pyinfra.context.host')
    def test_add_ssh_keys_no_keys(self, mock_host):
        """Test add_ssh_keys with no keys available."""
        # Configure fetch_ssh_keys to return None
        with patch.object(self.key_manager, 'fetch_ssh_keys', return_value=None):
            # Try to add keys
            result = self.key_manager.add_ssh_keys()
            
            # Verify operation failed
            self.assertFalse(result)
            mock_host.get_fact.assert_not_called()

    @patch('pyinfra.context.host')
    def test_add_ssh_keys_user_error(self, mock_host):
        """Test add_ssh_keys with user lookup error."""
        # Set up mocks for fetch_ssh_keys
        with patch.object(self.key_manager, 'fetch_ssh_keys', return_value=self.sample_ssh_keys):
            # Configure host fact to return None for user
            mock_host.get_fact.return_value = None
            
            # Try to add keys
            result = self.key_manager.add_ssh_keys()
            
            # Verify operation failed
            self.assertFalse(result)

    @patch('pyinfra.context.host')
    def test_add_ssh_keys_exception(self, mock_host):
        """Test add_ssh_keys with exception."""
        # Set up mocks for fetch_ssh_keys
        with patch.object(self.key_manager, 'fetch_ssh_keys', return_value=self.sample_ssh_keys), \
             patch('pyinfra.operations.server.user_authorized_keys', side_effect=Exception("Operation failed")):
            
            # Setup host facts
            mock_host.get_fact.side_effect = [
                'testuser',  # User fact
                {'testuser': {'group': 'testgroup'}}  # Users fact
            ]
            
            # Try to add keys
            result = self.key_manager.add_ssh_keys()
            
            # Verify operation failed
            self.assertFalse(result)

    def test_clear_cache(self):
        """Test clear_cache method."""
        # Set some cached values
        SSHKeyManager._credentials = {"username": "cached", "password": "cached"}
        SSHKeyManager._ssh_keys = ["cached-key"]
        SSHKeyManager._session_key = "cached-session"
        
        # Clear cache
        result = self.key_manager.clear_cache()
        
        # Verify cache was cleared
        self.assertTrue(result)
        self.assertIsNone(SSHKeyManager._credentials)
        self.assertIsNone(SSHKeyManager._ssh_keys)
        self.assertIsNone(SSHKeyManager._session_key)

    def test_backward_compatibility_function(self):
        """Test the backward compatibility function."""
        # Import the standalone function
        from infraninja.utils.pubkeys import add_ssh_keys
        
        # Mock the singleton instance's add_ssh_keys method
        with patch.object(SSHKeyManager, 'get_instance') as mock_get_instance:
            mock_instance = MagicMock()
            mock_instance.add_ssh_keys.return_value = "operation result"
            mock_get_instance.return_value = mock_instance
            
            # Call the standalone function
            result = add_ssh_keys()
            
            # Verify the singleton instance's method was called
            self.assertEqual(result, "operation result")
            mock_instance.add_ssh_keys.assert_called_once()


if __name__ == "__main__":
    unittest.main()
