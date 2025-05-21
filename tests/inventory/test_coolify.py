#!/usr/bin/env python3
# tests/inventory/test_coolify.py

import sys
import json
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

from infraninja.inventory.coolify import Coolify, CoolifyAPIError, CoolifySSHError
import requests

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class TestCoolify(unittest.TestCase):
    """Test cases for the Coolify class."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.mock_ssh_key_path_str = "/home/testuser/.ssh/id_rsa"
        self.mock_ssh_config_dir_str = "/home/testuser/.ssh/config.d"
        self.mock_home_path = Path("/home/testuser")

        self.api_url = "https://mock-coolify.example.com/api"  # Test specific API URL
        self.api_key = "test-coolify-api-key"
        self.tags = ["prod", "web"]

        self.sample_server_data_raw = [
            {
                "id": "server-id-1",
                "uuid": "uuid-1",
                "name": "prod-web-server1",
                "description": "Prod Web Server",
                "ip": "1.1.1.1",
                "user": "testuser",
                "port": 22,
                "settings": {"is_reachable": True, "is_usable": True},
            },
            {
                "id": "server-id-2",
                "uuid": "uuid-2",
                "name": "staging-db-server2",
                "description": "Staging DB",
                "ip": "2.2.2.2",
                "user": "root",
                "port": 2222,
                "settings": {"is_reachable": True, "is_usable": True},
            },
            {
                "id": "server-id-3",
                "uuid": "uuid-3",
                "name": "unusable-server3",
                "description": "Unusable Server",
                "ip": "3.3.3.3",
                "user": "testuser",
                "port": 22,
                "settings": {"is_reachable": False, "is_usable": True},
            },
            {
                "id": "server-id-4",
                "uuid": "uuid-4",
                "name": "generic-server4-prod",
                "description": "Generic Server Prod",
                "ip": "4.4.4.4",
                "user": "anotheruser",
                "port": 22,
                "settings": {"is_reachable": True, "is_usable": True},
            },
        ]

        self.expected_formatted_servers_no_tags = [
            (
                "prod-web-server1",
                {
                    "hostname": "1.1.1.1",
                    "ssh_user": "testuser",
                    "ssh_port": 22,
                    "ssh_key": self.mock_ssh_key_path_str,
                    "is_active": True,
                    "uuid": "uuid-1",
                    "server_id": "server-id-1",
                    "description": "Prod Web Server",
                },
            ),
            (
                "staging-db-server2",
                {
                    "hostname": "2.2.2.2",
                    "ssh_user": "root",
                    "ssh_port": 2222,
                    "ssh_key": self.mock_ssh_key_path_str,
                    "is_active": True,
                    "uuid": "uuid-2",
                    "server_id": "server-id-2",
                    "description": "Staging DB",
                },
            ),
            (
                "generic-server4-prod",
                {
                    "hostname": "4.4.4.4",
                    "ssh_user": "anotheruser",
                    "ssh_port": 22,
                    "ssh_key": self.mock_ssh_key_path_str,
                    "is_active": True,
                    "uuid": "uuid-4",
                    "server_id": "server-id-4",
                    "description": "Generic Server Prod",
                },
            ),
        ]

        self.patchers = []

        # Mock Path methods
        patch_path_exists = patch("pathlib.Path.exists", return_value=True)
        self.mock_path_exists = patch_path_exists.start()
        self.patchers.append(patch_path_exists)

        # Mock open function to avoid actual file operations
        mock_file = MagicMock()
        mock_open = MagicMock(return_value=mock_file)
        patch_open = patch("builtins.open", mock_open)
        self.mock_open = patch_open.start()
        self.patchers.append(patch_open)

        patch_path_mkdir = patch("pathlib.Path.mkdir")
        self.mock_path_mkdir = patch_path_mkdir.start()
        self.patchers.append(patch_path_mkdir)

        patch_path_home = patch("pathlib.Path.home", return_value=self.mock_home_path)
        self.mock_path_home = patch_path_home.start()
        self.patchers.append(patch_path_home)

        # Mock os.path.expanduser to respect the mocked home
        def mock_os_expanduser_func(path_str):
            if path_str.startswith("~"):
                return str(self.mock_home_path / path_str[2:])
            return path_str

        patch_os_expanduser = patch(
            "os.path.expanduser", side_effect=mock_os_expanduser_func
        )
        self.mock_os_expanduser = patch_os_expanduser.start()
        self.patchers.append(patch_os_expanduser)

        # Mock requests.get for _make_api_request
        patch_requests_get = patch("requests.get")
        self.mock_requests_get = patch_requests_get.start()
        self.patchers.append(patch_requests_get)

        # Configure default mock response for server loading
        self.mock_api_response = MagicMock()
        self.mock_api_response.status_code = 200
        self.mock_api_response.json.return_value = self.sample_server_data_raw
        self.mock_requests_get.return_value = self.mock_api_response

        # Patch Coolify.load_servers for __init__ tests to avoid API calls during basic init checks
        # Store the patcher object to control it (stop/start)
        self.patcher_coolify_load_servers = patch(
            "infraninja.inventory.coolify.Coolify.load_servers", MagicMock()
        )
        self.mock_coolify_load_servers_method = (
            self.patcher_coolify_load_servers.start()
        )
        self.patchers.append(self.patcher_coolify_load_servers)

    def tearDown(self):
        """Tear down test fixtures after each test method."""
        for patcher in self.patchers:
            patcher.stop()

    def test_init_with_defaults(self):
        """Test initialization with default parameters."""
        self.patcher_coolify_load_servers.stop()  # Allow real load_servers to run

        self.mock_requests_get.reset_mock()
        self.mock_requests_get.return_value = self.mock_api_response
        # Also ensure the mock_api_response itself is reset to its default state from setUp
        self.mock_api_response.status_code = 200
        self.mock_api_response.json.return_value = self.sample_server_data_raw
        self.mock_api_response.raise_for_status.side_effect = None

        coolify = Coolify(api_key=self.api_key)

        self.assertEqual(coolify.ssh_key_path, self.mock_home_path / ".ssh/id_rsa")
        self.assertEqual(
            coolify.api_url, "https://coolify.example.com/api"
        )  # Check against Coolify's actual default
        self.assertEqual(coolify.api_key, self.api_key)
        self.assertEqual(coolify.ssh_config_dir, self.mock_home_path / ".ssh/config.d")
        self.mock_path_mkdir.assert_called_with(parents=True, exist_ok=True)

        # The global self.mock_requests_get (from setUp) should be called
        self.mock_requests_get.assert_called_once()
        self.assertEqual(len(coolify.servers), 3)

        self.patcher_coolify_load_servers.start()  # Restore for other tests if necessary (though tests should be isolated)

    def test_init_with_custom_params(self):
        """Test initialization with custom parameters."""
        # self.mock_coolify_load_servers_method is active from setUp
        custom_ssh_key = "~/custom_key"
        custom_config_dir = "~/custom_config"

        coolify = Coolify(
            ssh_key_path=custom_ssh_key,
            api_url=self.api_url,  # Use test's api_url
            api_key=self.api_key,
            tags=self.tags,
            ssh_config_dir=custom_config_dir,
        )
        self.assertEqual(coolify.ssh_key_path, self.mock_home_path / "custom_key")
        self.assertEqual(coolify.api_url, self.api_url)
        self.assertEqual(coolify.tags, self.tags)
        self.assertEqual(coolify.ssh_config_dir, self.mock_home_path / "custom_config")
        self.mock_coolify_load_servers_method.assert_called_once()

    def test_init_missing_ssh_key(self):
        """Test initialization with a missing SSH key."""
        self.mock_path_exists.return_value = False
        with self.assertRaises(CoolifySSHError):
            Coolify(api_key=self.api_key)

    def test_init_missing_api_key(self):
        """Test initialization with a missing API key."""
        with self.assertRaises(CoolifyAPIError):
            Coolify(api_key=None)

    def test_make_api_request_success(self):
        """Test _make_api_request for a successful GET."""
        self.patcher_coolify_load_servers.stop()

        # Instantiate Coolify with the test's api_url
        coolify = Coolify(api_key=self.api_key, api_url=self.api_url)

        # Reset the global mock_requests_get for this specific test call
        self.mock_requests_get.reset_mock()
        mock_response_data = {"data": "success"}
        self.mock_api_response.json.return_value = mock_response_data
        self.mock_requests_get.return_value = self.mock_api_response
        response = coolify._make_api_request("test/endpoint")

        self.mock_requests_get.assert_called_once_with(
            f"{self.api_url}/test/endpoint",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            timeout=30,
        )
        self.assertEqual(response, mock_response_data)

        self.patcher_coolify_load_servers.start()

    def test_make_api_request_http_error(self):
        """Test _make_api_request with an HTTP error."""
        self.patcher_coolify_load_servers.stop()
        coolify = Coolify(api_key=self.api_key, api_url=self.api_url)

        self.mock_requests_get.reset_mock()
        self.mock_api_response.status_code = 404
        self.mock_api_response.raise_for_status.side_effect = requests.HTTPError(
            "Not Found"
        )
        self.mock_requests_get.return_value = self.mock_api_response

        with self.assertRaises(CoolifyAPIError):
            coolify._make_api_request("test/error")

        # Restore mock_api_response defaults for other tests if modified
        self.mock_api_response.status_code = 200
        self.mock_api_response.raise_for_status.side_effect = None
        self.mock_api_response.json.return_value = self.sample_server_data_raw

    def test_make_api_request_json_decode_error(self):
        """Test _make_api_request with a JSON decode error."""
        self.patcher_coolify_load_servers.stop()
        coolify = Coolify(api_key=self.api_key, api_url=self.api_url)
        self.mock_requests_get.reset_mock()
        self.mock_api_response.status_code = 200
        self.mock_api_response.json.side_effect = json.JSONDecodeError(
            "Error", "doc", 0
        )
        self.mock_requests_get.return_value = self.mock_api_response

        with self.assertRaises(CoolifyAPIError):
            coolify._make_api_request("test/json_error")

        # Restore mock_api_response defaults
        self.mock_api_response.json.side_effect = None
        self.mock_api_response.json.return_value = self.sample_server_data_raw

    def test_filter_server(self):
        """Test the _filter_server method."""
        # load_servers is mocked by default
        coolify = Coolify(api_key=self.api_key, tags=["prod", "web"])

        server_prod_web = {"name": "prod-web-server1"}
        server_staging_db = {"name": "staging-db-server2"}
        server_generic_prod = {"name": "generic-server-prod"}

        self.assertTrue(coolify._filter_server(server_prod_web))
        self.assertFalse(
            coolify._filter_server(server_staging_db)
        )  # 'staging' or 'db' not in tags
        self.assertTrue(
            coolify._filter_server(server_generic_prod)
        )  # 'prod' is in tags

        coolify.tags = None  # No tags
        self.assertTrue(
            coolify._filter_server(server_staging_db)
        )  # Should pass if no tags

    @patch("infraninja.inventory.coolify.Coolify._make_api_request")
    def test_load_servers_success(self, mock_make_request):
        """Test successful server loading."""
        self.patcher_coolify_load_servers.stop()

        mock_make_request.return_value = self.sample_server_data_raw

        coolify = Coolify(api_key=self.api_key, api_url=self.api_url)

        self.assertEqual(len(coolify.servers), 3)
        self.assertEqual(coolify.servers[0][0], "prod-web-server1")
        self.assertEqual(coolify.servers[1][0], "staging-db-server2")
        self.assertEqual(coolify.servers[2][0], "generic-server4-prod")

        # Check attributes of the first server
        name, attrs = coolify.servers[0]
        self.assertEqual(name, self.expected_formatted_servers_no_tags[0][0])
        self.assertEqual(attrs, self.expected_formatted_servers_no_tags[0][1])

        mock_make_request.assert_called_once_with("api/v1/servers")

    @patch("infraninja.inventory.coolify.Coolify._make_api_request")
    def test_load_servers_api_error(self, mock_make_request):
        """Test server loading with an API error."""
        self.patcher_coolify_load_servers.stop()

        mock_make_request.side_effect = CoolifyAPIError("API Failed")

        with self.assertRaises(CoolifyAPIError):
            Coolify(api_key=self.api_key, api_url=self.api_url)

    @patch("infraninja.inventory.coolify.Coolify._make_api_request")
    def test_load_servers_no_servers_found(self, mock_make_request):
        """Test server loading when API returns no servers."""
        self.patcher_coolify_load_servers.stop()

        mock_make_request.return_value = []

        coolify = Coolify(api_key=self.api_key, api_url=self.api_url)

        self.assertEqual(len(coolify.servers), 0)
        mock_make_request.assert_called_once_with("api/v1/servers")

    def test_get_servers(self):
        """Test the get_servers method."""
        self.patcher_coolify_load_servers.stop()

        # The global self.mock_requests_get is already configured in setUp
        # to return self.mock_api_response.
        # Ensure self.mock_requests_get is reset if previous tests changed its state.
        self.mock_requests_get.reset_mock()
        self.mock_requests_get.return_value = (
            self.mock_api_response
        )  # Ensure it's correctly set
        self.mock_api_response.json.return_value = (
            self.sample_server_data_raw
        )  # Ensure JSON data is correct

        coolify = Coolify(
            api_key=self.api_key, api_url=self.api_url
        )  # Use test api_url
        servers = coolify.get_servers()

        self.assertEqual(len(servers), 3)
        self.assertEqual(servers, self.expected_formatted_servers_no_tags[:3])

    def test_get_server_by_name(self):
        """Test get_server_by_name method."""
        self.patcher_coolify_load_servers.stop()

        self.mock_requests_get.reset_mock()
        self.mock_requests_get.return_value = self.mock_api_response
        self.mock_api_response.json.return_value = self.sample_server_data_raw

        coolify = Coolify(
            api_key=self.api_key, api_url=self.api_url
        )  # Use test api_url

        server1_attrs = coolify.get_server_by_name("prod-web-server1")
        self.assertIsNotNone(server1_attrs)
        self.assertEqual(server1_attrs["hostname"], "1.1.1.1")

        non_existent_attrs = coolify.get_server_by_name("non-existent-server")
        self.assertIsNone(non_existent_attrs)

    @patch("infraninja.inventory.coolify.Coolify.load_servers")
    def test_get_servers_by_tag(self, mock_load_servers_method_for_test):
        """Test get_servers_by_tag method."""
        # The @patch replaces Coolify.load_servers for this test's scope.
        # So, Coolify.__init__ will call this mock_load_servers_method_for_test.

        # Initial call during Coolify instantiation
        coolify = Coolify(api_key=self.api_key, api_url=self.api_url, tags=["initial"])
        original_tags = coolify.tags

        # Reset the mock that was called during __init__ before we set new side_effect for the specific test call
        mock_load_servers_method_for_test.reset_mock()

        def side_effect_load_servers():
            filtered_raw = [
                s for s in self.sample_server_data_raw if coolify._filter_server(s)
            ]
            coolify.servers = coolify.format_host_list(filtered_raw)

        mock_load_servers_method_for_test.side_effect = side_effect_load_servers

        tag_to_find = "prod"
        coolify.get_servers_by_tag(tag_to_find)

        mock_load_servers_method_for_test.assert_called_once()  # Now this should be true for the call within get_servers_by_tag
        self.assertEqual(coolify.tags, original_tags)
