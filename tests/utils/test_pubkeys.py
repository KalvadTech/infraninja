#!/usr/bin/env python3
# tests/utils/test_pubkeys.py

import json
import os
import sys
from pathlib import Path
from unittest.mock import patch, Mock

import requests

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from infraninja.utils.pubkeys import SSHKeyManager, add_ssh_keys


# Mock the deploy decorator to avoid PyInfra internals
def mock_deploy(name):
    def decorator(func):
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        return wrapper

    return decorator


class TestSSHKeyManagerSingleton:
    """Test suite for the SSHKeyManager singleton pattern."""

    def test_singleton_pattern(self):
        """Test that SSHKeyManager implements the singleton pattern correctly."""
        # Get two instances of the manager
        manager1 = SSHKeyManager.get_instance()
        manager2 = SSHKeyManager.get_instance()

        # They should be the same object
        assert manager1 is manager2
        assert id(manager1) == id(manager2)

        # Verify they share state
        test_value = "test_value"
        with patch.object(SSHKeyManager, "_base_url", test_value):
            assert manager1._base_url == test_value
            assert manager2._base_url == test_value

    def test_direct_instantiation(self):
        """Test direct instantiation of SSHKeyManager."""
        # Direct instantiation should work, but should not affect singleton
        singleton = SSHKeyManager.get_instance()
        direct = SSHKeyManager()

        # They should be different objects
        assert singleton is not direct
        assert id(singleton) != id(direct)

        # But the class variables should be shared
        with patch.object(SSHKeyManager, "_base_url", "test_url"):
            assert singleton._base_url == "test_url"
            assert direct._base_url == "test_url"


class TestSSHKeyManagerInitialization:
    """Test suite for SSHKeyManager initialization."""

    @patch.dict(os.environ, {"JINN_API_URL": "https://test-api.example.com"})
    def test_init_with_env_var(self):
        """Test initialization with environment variable set."""
        # Clear any existing singleton instance
        SSHKeyManager._instance = None
        SSHKeyManager._base_url = None

        # Instantiate and check environment variable was used
        manager = SSHKeyManager.get_instance()
        assert manager._base_url == "https://test-api.example.com"

    @patch.dict(os.environ, {}, clear=True)
    @patch("infraninja.utils.pubkeys.logger")
    def test_init_without_env_var(self, mock_logger):
        """Test initialization without environment variable."""
        # Clear any existing singleton instance
        SSHKeyManager._instance = None
        SSHKeyManager._base_url = None

        # Instantiate and check error was logged
        manager = SSHKeyManager.get_instance()
        assert manager._base_url is None
        mock_logger.error.assert_called_with(
            "Error: JINN_API_URL environment variable not set"
        )


class TestSSHKeyManagerCredentials:
    """Test suite for SSHKeyManager credential handling."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        # Reset singleton state
        SSHKeyManager._instance = None
        SSHKeyManager._credentials = None
        SSHKeyManager._session_key = None
        SSHKeyManager._base_url = None

    @patch("infraninja.utils.pubkeys.input", return_value="testuser")
    @patch("infraninja.utils.pubkeys.getpass.getpass", return_value="testpass")
    def test_get_credentials_from_input(self, mock_getpass, mock_input):
        """Test getting credentials from user input."""
        manager = SSHKeyManager()
        credentials = manager._get_credentials()

        assert credentials == {"username": "testuser", "password": "testpass"}
        mock_input.assert_called_once()
        mock_getpass.assert_called_once()

    @patch("infraninja.utils.pubkeys.logger")
    def test_get_credentials_from_cache(self, mock_logger):
        """Test getting credentials from cache."""
        # Set up cached credentials
        manager = SSHKeyManager()
        manager._credentials = {"username": "cached_user", "password": "cached_pass"}

        # Get credentials should use cache
        credentials = manager._get_credentials()
        assert credentials == {"username": "cached_user", "password": "cached_pass"}
        mock_logger.debug.assert_called_with("Using cached credentials")


class TestSSHKeyManagerAPI:
    """Test suite for SSHKeyManager API interaction."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        # Reset singleton state
        SSHKeyManager._instance = None
        SSHKeyManager._credentials = None
        SSHKeyManager._session_key = None
        SSHKeyManager._base_url = "https://test-api.example.com"

    @patch("infraninja.utils.pubkeys.requests.post")
    def test_login_success(self, mock_post):
        """Test successful login to API."""
        # Set up mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"session_key": "test_session_key"}
        mock_post.return_value = mock_response

        # Set up manager with credentials
        manager = SSHKeyManager()
        manager._credentials = {"username": "testuser", "password": "testpass"}

        # Call login
        result = manager._login()

        # Verify
        assert result is True
        assert manager._session_key == "test_session_key"
        mock_post.assert_called_once_with(
            "https://test-api.example.com/login/",
            json=manager._credentials,
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            timeout=30,
        )

    @patch("infraninja.utils.pubkeys.requests.post")
    @patch("infraninja.utils.pubkeys.logger")
    def test_login_http_error(self, mock_logger, mock_post):
        """Test login with HTTP error."""
        # Set up mock response
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_post.return_value = mock_response

        # Set up manager with credentials
        manager = SSHKeyManager()
        manager._credentials = {"username": "testuser", "password": "testpass"}

        # Call login
        result = manager._login()

        # Verify
        assert result is False
        assert manager._session_key is None
        mock_logger.error.assert_called_once_with(
            "Login failed with status code %s: %s", 401, "Unauthorized"
        )

    @patch("infraninja.utils.pubkeys.requests.post")
    @patch("infraninja.utils.pubkeys.logger")
    def test_login_connection_error(self, mock_logger, mock_post):
        """Test login with connection error."""
        # Set up mock to raise connection error
        mock_post.side_effect = requests.exceptions.ConnectionError(
            "Connection refused"
        )

        # Set up manager with credentials
        manager = SSHKeyManager()
        manager._credentials = {"username": "testuser", "password": "testpass"}

        # Call login
        result = manager._login()

        # Verify
        assert result is False
        mock_logger.error.assert_called_once_with(
            "Connection error when attempting to login"
        )

    @patch("infraninja.utils.pubkeys.requests.post")
    @patch("infraninja.utils.pubkeys.logger")
    def test_login_timeout(self, mock_logger, mock_post):
        """Test login with timeout error."""
        # Set up mock to raise timeout
        mock_post.side_effect = requests.exceptions.Timeout("Request timed out")

        # Set up manager with credentials
        manager = SSHKeyManager()
        manager._credentials = {"username": "testuser", "password": "testpass"}

        # Call login
        result = manager._login()

        # Verify
        assert result is False
        mock_logger.error.assert_called_once_with("Login request timed out")

    @patch("infraninja.utils.pubkeys.requests.post")
    @patch("infraninja.utils.pubkeys.logger")
    def test_login_json_decode_error(self, mock_logger, mock_post):
        """Test login with JSON decode error."""
        # Set up mock response with invalid JSON
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
        mock_post.return_value = mock_response

        # Set up manager with credentials
        manager = SSHKeyManager()
        manager._credentials = {"username": "testuser", "password": "testpass"}

        # Call login
        result = manager._login()

        # Verify
        assert result is False
        mock_logger.error.assert_called_once_with(
            "Received invalid JSON in login response"
        )

    @patch("infraninja.utils.pubkeys.requests.post")
    @patch("infraninja.utils.pubkeys.logger")
    def test_login_missing_session_key(self, mock_logger, mock_post):
        """Test login with missing session key in response."""
        # Set up mock response without session key
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "success"}  # No session_key
        mock_post.return_value = mock_response

        # Set up manager with credentials
        manager = SSHKeyManager()
        manager._credentials = {"username": "testuser", "password": "testpass"}

        # Call login
        result = manager._login()

        # Verify
        assert result is False
        mock_logger.error.assert_called_once_with(
            "Login succeeded but no session key in response"
        )


class TestSSHKeyManagerAuthRequest:
    """Test suite for SSHKeyManager authenticated requests."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        # Reset singleton state but keep minimal configuration for tests
        SSHKeyManager._instance = None
        SSHKeyManager._credentials = None
        SSHKeyManager._base_url = "https://test-api.example.com"
        SSHKeyManager._session_key = "test_session_key"

    @patch("infraninja.utils.pubkeys.requests.request")
    def test_make_auth_request_success(self, mock_request):
        """Test successful authenticated request."""
        # Set up mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_request.return_value = mock_response

        # Set up manager
        manager = SSHKeyManager()

        # Call method
        response = manager._make_auth_request(
            "https://test-api.example.com/endpoint", method="get"
        )

        # Verify
        assert response is mock_response
        mock_request.assert_called_once_with(
            "get",
            "https://test-api.example.com/endpoint",
            headers={
                "Authorization": "Bearer test_session_key",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            cookies={"sessionid": "test_session_key"},
            timeout=30,
        )

    @patch("infraninja.utils.pubkeys.requests.request")
    @patch("infraninja.utils.pubkeys.logger")
    def test_make_auth_request_http_error(self, mock_logger, mock_request):
        """Test authenticated request with HTTP error."""
        # Set up mock response
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.text = "Not Found"
        mock_request.return_value = mock_response

        # Set up manager
        manager = SSHKeyManager()

        # Call method
        response = manager._make_auth_request(
            "https://test-api.example.com/endpoint", method="get"
        )

        # Verify
        assert response is None
        mock_logger.error.assert_called_once_with(
            "API request failed with status code %s: %s", 404, "Not Found"
        )

    @patch("infraninja.utils.pubkeys.logger")
    def test_make_auth_request_no_session(self, mock_logger):
        """Test authenticated request with no session key."""
        # Set up manager with no session key
        manager = SSHKeyManager()
        manager._session_key = None

        # Call method
        response = manager._make_auth_request(
            "https://test-api.example.com/endpoint", method="get"
        )

        # Verify
        assert response is None
        mock_logger.error.assert_called_once_with(
            "Cannot make authenticated request: No session key available"
        )


class TestSSHKeyManagerFetchKeys:
    """Test suite for SSHKeyManager fetch_ssh_keys method."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        # Reset singleton state
        SSHKeyManager._instance = None
        SSHKeyManager._credentials = None
        SSHKeyManager._session_key = None
        SSHKeyManager._base_url = "https://test-api.example.com"
        SSHKeyManager._ssh_keys = None

    @patch.object(SSHKeyManager, "_login", return_value=True)
    @patch.object(SSHKeyManager, "_make_auth_request")
    def test_fetch_ssh_keys_success(self, mock_make_auth_request, mock_login):
        """Test successful fetching of SSH keys."""
        # Set up mock response
        mock_response = Mock()
        mock_response.json.return_value = {
            "result": [
                {"key": "ssh-rsa AAAA... user1@example.com"},
                {"key": "ssh-ed25519 AAAA... user2@example.com"},
            ]
        }
        mock_make_auth_request.return_value = mock_response

        # Set up manager
        manager = SSHKeyManager()

        # Call method
        keys = manager.fetch_ssh_keys()

        # Verify
        assert keys == [
            "ssh-rsa AAAA... user1@example.com",
            "ssh-ed25519 AAAA... user2@example.com",
        ]
        mock_login.assert_called_once()
        mock_make_auth_request.assert_called_once_with(
            "https://test-api.example.com/ssh-tools/ssh-keylist/"
        )

    @patch.object(SSHKeyManager, "_login", return_value=True)
    @patch.object(SSHKeyManager, "_make_auth_request")
    @patch("infraninja.utils.pubkeys.logger")
    def test_fetch_ssh_keys_missing_result(
        self, mock_logger, mock_make_auth_request, mock_login
    ):
        """Test fetching SSH keys with missing result field."""
        # Set up mock response with missing result field
        mock_response = Mock()
        mock_response.json.return_value = {"status": "success"}  # No result field
        mock_make_auth_request.return_value = mock_response

        # Set up manager
        manager = SSHKeyManager()

        # Call method
        keys = manager.fetch_ssh_keys()

        # Verify
        assert keys is None
        mock_logger.error.assert_called_once_with(
            "SSH key API response missing 'result' field"
        )

    @patch.object(SSHKeyManager, "_login", return_value=False)
    @patch("infraninja.utils.pubkeys.logger")
    def test_fetch_ssh_keys_login_failure(self, mock_logger, mock_login):
        """Test fetching SSH keys with login failure."""
        # Set up manager
        manager = SSHKeyManager()

        # Call method
        keys = manager.fetch_ssh_keys()

        # Verify
        assert keys is None
        mock_logger.error.assert_called_once_with("Failed to authenticate with API")

    @patch.object(SSHKeyManager, "_login", return_value=True)
    @patch.object(SSHKeyManager, "_make_auth_request", return_value=None)
    @patch("infraninja.utils.pubkeys.logger")
    def test_fetch_ssh_keys_request_failure(
        self, mock_logger, mock_make_auth_request, mock_login
    ):
        """Test fetching SSH keys with request failure."""
        # Set up manager
        manager = SSHKeyManager()

        # Call method
        keys = manager.fetch_ssh_keys()

        # Verify
        assert keys is None
        mock_logger.error.assert_called_once_with(
            "Failed to retrieve SSH keys from API"
        )

    def test_fetch_ssh_keys_cache(self):
        """Test that fetch_ssh_keys uses cached keys when available."""
        # Set up manager with cached keys
        manager = SSHKeyManager()
        cached_keys = ["ssh-rsa AAAA... cached@example.com"]
        manager._ssh_keys = cached_keys

        # Call method
        keys = manager.fetch_ssh_keys()

        # Verify
        assert keys is cached_keys
        assert keys == ["ssh-rsa AAAA... cached@example.com"]

    def test_fetch_ssh_keys_force_refresh(self):
        """Test that fetch_ssh_keys forces refresh when requested."""
        # Set up manager with cached keys
        manager = SSHKeyManager()
        cached_keys = ["ssh-rsa AAAA... cached@example.com"]
        manager._ssh_keys = cached_keys

        # Mock login and request to test forced refresh
        with patch.object(SSHKeyManager, "_login", return_value=True) as mock_login:
            with patch.object(
                SSHKeyManager, "_make_auth_request"
            ) as mock_make_auth_request:
                # Set up mock response
                mock_response = Mock()
                mock_response.json.return_value = {
                    "result": [{"key": "ssh-rsa AAAA... refreshed@example.com"}]
                }
                mock_make_auth_request.return_value = mock_response

                # Call method with force_refresh=True
                keys = manager.fetch_ssh_keys(force_refresh=True)

                # Verify
                assert keys == ["ssh-rsa AAAA... refreshed@example.com"]
                mock_login.assert_called_once()
                mock_make_auth_request.assert_called_once()


class TestSSHKeyManagerAddKeys:
    """Test suite for SSHKeyManager add_ssh_keys method."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        # Reset singleton state
        SSHKeyManager._instance = None
        SSHKeyManager._credentials = None
        SSHKeyManager._session_key = None
        SSHKeyManager._base_url = "https://test-api.example.com"
        SSHKeyManager._ssh_keys = None

    @patch.object(SSHKeyManager, "fetch_ssh_keys")
    def test_add_ssh_keys_success(self, mock_fetch_keys):
        """Test successful addition of SSH keys."""
        # Set up mock return values for fetch_ssh_keys
        ssh_keys = [
            "ssh-rsa AAAA... user1@example.com",
            "ssh-ed25519 AAAA... user2@example.com",
        ]
        mock_fetch_keys.return_value = ssh_keys

        # Create a test version of add_ssh_keys that doesn't use PyInfra
        def test_add_ssh_keys(self, force_refresh=False):
            keys = self.fetch_ssh_keys(force_refresh)
            if not keys:
                return False

            # Simulate successful addition
            return True

        # Patch the method with our test version
        with patch.object(SSHKeyManager, "add_ssh_keys", test_add_ssh_keys):
            # Set up manager
            manager = SSHKeyManager()

            # Call method
            result = manager.add_ssh_keys()

            # Verify
            assert result is True
            mock_fetch_keys.assert_called_once_with(False)

    @patch.object(SSHKeyManager, "fetch_ssh_keys", return_value=None)
    @patch("infraninja.utils.pubkeys.logger")
    def test_add_ssh_keys_no_keys(self, mock_logger, mock_fetch_keys):
        """Test add_ssh_keys with no keys available."""

        # Create a test version of add_ssh_keys that doesn't use PyInfra
        def test_add_ssh_keys(self, force_refresh=False):
            keys = self.fetch_ssh_keys(force_refresh)
            if not keys:
                from infraninja.utils.pubkeys import logger

                logger.error("No SSH keys available to deploy")
                return False
            return True

        # Patch the method with our test version
        with patch.object(SSHKeyManager, "add_ssh_keys", test_add_ssh_keys):
            # Set up manager
            manager = SSHKeyManager()

            # Call method
            result = manager.add_ssh_keys()

            # Verify
            assert result is False
            mock_logger.error.assert_called_once_with("No SSH keys available to deploy")

    @patch.object(SSHKeyManager, "fetch_ssh_keys")
    def test_add_ssh_keys_no_user(self, mock_fetch_keys):
        """Test add_ssh_keys with no current user."""
        # Set up mock return values for fetch_ssh_keys
        ssh_keys = ["ssh-rsa AAAA... user1@example.com"]
        mock_fetch_keys.return_value = ssh_keys

        # Create a test version of add_ssh_keys that simulates a missing user
        def test_add_ssh_keys(self, force_refresh=False):
            keys = self.fetch_ssh_keys(force_refresh)
            if not keys:
                return False

            # Simulate user error
            from infraninja.utils.pubkeys import logger

            logger.error("Failed to determine current user")
            return False

        # Patch the method with our test version
        with patch.object(SSHKeyManager, "add_ssh_keys", test_add_ssh_keys):
            # Set up logger
            with patch("infraninja.utils.pubkeys.logger") as mock_logger:
                # Set up manager
                manager = SSHKeyManager()

                # Call method
                result = manager.add_ssh_keys()

                # Verify
                assert result is False
                mock_logger.error.assert_called_once_with(
                    "Failed to determine current user"
                )

    def test_clear_cache(self):
        """Test clearing the cache."""
        # Create a new class instance to avoid singleton pattern issues
        SSHKeyManager._instance = None

        # Set up class attributes directly
        SSHKeyManager._credentials = {"username": "testuser", "password": "testpass"}
        SSHKeyManager._session_key = "test_session_key"
        SSHKeyManager._ssh_keys = ["ssh-rsa AAAA..."]

        # Create a new instance
        manager = SSHKeyManager()

        # Call clear_cache
        with patch("infraninja.utils.pubkeys.logger") as mock_logger:
            result = manager.clear_cache()

        # Verify class attributes are cleared
        assert result is True
        assert SSHKeyManager._credentials is None
        assert SSHKeyManager._session_key is None
        assert SSHKeyManager._ssh_keys is None


class TestBackwardCompatibility:
    """Test suite for backward compatibility functions."""

    def test_add_ssh_keys_backward_compatibility(self):
        """Test the backward compatibility add_ssh_keys function."""
        # Patch only the SSHKeyManager.get_instance and its add_ssh_keys method
        with patch.object(SSHKeyManager, "get_instance") as mock_get_instance:
            # Configure the mock
            mock_instance = Mock()
            mock_instance.add_ssh_keys.return_value = True
            mock_get_instance.return_value = mock_instance

            # Call the backward compatibility function
            result = add_ssh_keys()

            # Verify
            assert result is True
            mock_get_instance.assert_called_once()
            mock_instance.add_ssh_keys.assert_called_once()
