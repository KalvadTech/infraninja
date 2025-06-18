#!/usr/bin/env python3
# tests/inventory/test_jinn.py

import json
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import requests

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from infraninja.inventory.jinn import Jinn, JinnAPIError, JinnSSHError


class TestJinn(unittest.TestCase):
    """Test cases for the Jinn class."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        # Create mock SSH key file
        self.mock_ssh_key_path = Path("/home/test/.ssh/id_rsa")

        # Mock API configuration
        self.api_url = "https://test-jinn-api.example.com"
        self.api_key = "test-api-key"

        # Mock filter configuration
        self.groups = ["group1", "group2"]
        self.tags = ["tag1", "tag2"]

        # Updated sample server data to include bastion_host in attributes
        self.sample_server_data = {
            "result": [
                {
                    "hostname": "server1",
                    "ssh_hostname": "server1.example.com",
                    "ssh_user": "admin",
                    "is_active": True,
                    "group": {"name_en": "group1"},
                    "tags": ["tag1", "web"],
                    "attributes": {
                        "role": "webserver",
                        "environment": "prod",
                        "ssh_hostname": "server1.example.com",
                        "bastion_host": "bastion.example.com",
                        "bastion_user": "bastion_user",
                        "bastion_port": 22,
                    },
                },
                {
                    "hostname": "server2",
                    "ssh_hostname": "server2.example.com",
                    "ssh_user": "admin",
                    "is_active": True,
                    "group": {"name_en": "group2"},
                    "tags": ["tag2", "db"],
                    "attributes": {
                        "role": "database",
                        "environment": "prod",
                        "ssh_hostname": "server2.example.com",
                    },
                },
                {
                    "hostname": "server3",
                    "ssh_hostname": "server3.example.com",
                    "ssh_user": "admin",
                    "is_active": False,
                    "group": {"name_en": "group3"},
                    "tags": ["tag3"],
                    "attributes": {
                        "role": "backup",
                        "environment": "staging",
                        "ssh_hostname": "server3.example.com",
                    },
                },
            ]
        }

        # Updated mock SSH config to include ProxyCommand for bastion
        self.mock_ssh_config = """
Host server1
    HostName server1.example.com
    User admin
    IdentityFile ~/.ssh/id_rsa
    Port 22
    ProxyCommand ssh -W %h:%p bastion_user@bastion.example.com

Host server2
    HostName server2.example.com
    User admin
    IdentityFile ~/.ssh/id_rsa
    Port 22
"""

        # Set up patches
        self.patchers = []

        # Patch Path.exists to return True for the SSH key path
        path_exists_patcher = patch("pathlib.Path.exists", return_value=True)
        self.mock_path_exists = path_exists_patcher.start()
        self.patchers.append(path_exists_patcher)

        # Patch Path.mkdir to do nothing
        path_mkdir_patcher = patch("pathlib.Path.mkdir")
        self.mock_path_mkdir = path_mkdir_patcher.start()
        self.patchers.append(path_mkdir_patcher)

        # Patch requests.get for API calls
        requests_get_patcher = patch("requests.get")
        self.mock_requests_get = requests_get_patcher.start()
        self.patchers.append(requests_get_patcher)

        # Patch Path.write_text to do nothing
        path_write_text_patcher = patch("pathlib.Path.write_text")
        self.mock_path_write_text = path_write_text_patcher.start()
        self.patchers.append(path_write_text_patcher)

        # Patch os.chmod to do nothing
        os_chmod_patcher = patch("os.chmod")
        self.mock_os_chmod = os_chmod_patcher.start()
        self.patchers.append(os_chmod_patcher)

        # Patch Path.read_text for the SSH config
        path_read_text_patcher = patch("pathlib.Path.read_text", return_value="")
        self.mock_path_read_text = path_read_text_patcher.start()
        self.patchers.append(path_read_text_patcher)

        # Set up mock responses
        self.mock_project_response = MagicMock()
        self.mock_project_response.json.return_value = {"name_en": "test-project"}
        self.mock_project_response.raise_for_status.return_value = None

        self.mock_servers_response = MagicMock()
        self.mock_servers_response.json.return_value = self.sample_server_data
        self.mock_servers_response.raise_for_status.return_value = None

        self.mock_ssh_response = MagicMock()
        self.mock_ssh_response.text = self.mock_ssh_config
        self.mock_ssh_response.raise_for_status.return_value = None

        self.mock_groups_response = MagicMock()
        self.mock_groups_response.json.return_value = {
            "result": [
                {"name_en": "group1"},
                {"name_en": "group2"},
                {"name_en": "group3"},
            ]
        }
        self.mock_groups_response.raise_for_status.return_value = None

        # Configure the mock_requests_get to return different responses based on URL
        def mock_get_side_effect(url, **kwargs):
            if "/inventory/project/" in url:
                return self.mock_project_response
            elif "/inventory/servers/" in url:
                return self.mock_servers_response
            elif "/ssh-tools/ssh-config/" in url:
                return self.mock_ssh_response
            elif "/inventory/groups/" in url:
                return self.mock_groups_response
            else:
                raise ValueError(f"Unexpected URL: {url}")

        self.mock_requests_get.side_effect = mock_get_side_effect

    def tearDown(self):
        """Tear down test fixtures after each test method."""
        # Stop all patches
        for patcher in self.patchers:
            patcher.stop()

    def test_init_with_defaults(self):
        """Test initialization with default parameters."""
        # Skip the refresh_ssh_config call during initialization
        with patch.object(Jinn, "refresh_ssh_config"):
            with patch(
                "pathlib.Path.expanduser", return_value=Path("/home/test/.ssh/id_rsa")
            ):
                with patch.object(Path, "home", return_value=Path("/home/test")):
                    jinn = Jinn(api_key=self.api_key)

                    # Check that the SSH key path was set correctly
                    self.assertEqual(jinn.ssh_key_path, Path("/home/test/.ssh/id_rsa"))

                    # Check that the API configuration was set correctly
                    self.assertEqual(jinn.api_url, "https://jinn-api.kalvad.cloud")
                    self.assertEqual(jinn.api_key, self.api_key)

                    # Check that the SSH config directory was created
                    self.mock_path_mkdir.assert_called()

    def test_init_with_custom_params(self):
        """Test initialization with custom parameters."""

        # Create a proper expanduser mock function with the path parameter
        def mock_expanduser(self_path):
            path_str = str(self_path)
            if path_str.startswith("~"):
                return Path(path_str.replace("~", "/home/test"))
            return self_path

        # Skip the refresh_ssh_config call during initialization
        with patch.object(Jinn, "refresh_ssh_config"):
            with patch.object(Path, "expanduser", mock_expanduser):
                with patch.object(Path, "home", return_value=Path("/home/test")):
                    jinn = Jinn(
                        ssh_key_path="~/custom_key",
                        api_url=self.api_url,
                        api_key=self.api_key,
                        groups=self.groups,
                        tags=self.tags,
                        use_bastion=True,
                        ssh_config_dir="~/custom_ssh_config",
                    )

                    # Check that the parameters were set correctly
                    self.assertEqual(jinn.ssh_key_path, Path("/home/test/custom_key"))
                    self.assertEqual(jinn.api_url, self.api_url)
                    self.assertEqual(jinn.api_key, self.api_key)
                    self.assertEqual(jinn.groups, self.groups)
                    self.assertEqual(jinn.tags, self.tags)
                    self.assertTrue(jinn.use_bastion)
                    self.assertEqual(
                        jinn.ssh_config_dir, Path("/home/test/custom_ssh_config")
                    )

    def test_init_missing_api_key(self):
        """Test initialization with a missing API key."""
        with self.assertRaises(JinnAPIError):
            Jinn(api_key=None)

    def test_str_to_bool(self):
        """Test the _str_to_bool method."""
        jinn = Jinn(api_key=self.api_key)

        # Test various values
        self.assertTrue(jinn._str_to_bool("True"))
        self.assertTrue(jinn._str_to_bool("true"))
        self.assertTrue(jinn._str_to_bool("t"))
        self.assertFalse(jinn._str_to_bool("False"))
        self.assertFalse(jinn._str_to_bool("false"))
        self.assertFalse(jinn._str_to_bool("f"))
        self.assertFalse(jinn._str_to_bool(None))
        self.assertFalse(jinn._str_to_bool(""))

    def test_get_groups_from_data(self):
        """Test the get_groups_from_data method."""
        jinn = Jinn(api_key=self.api_key)

        # Test with sample data
        groups = jinn.get_groups_from_data(self.sample_server_data)
        self.assertEqual(groups, ["group1", "group2", "group3"])

        # Test with empty data
        empty_data = {"result": []}
        empty_groups = jinn.get_groups_from_data(empty_data)
        self.assertEqual(empty_groups, [])

    def test_get_project_name(self):
        """Test the get_project_name method."""
        jinn = Jinn(api_key=self.api_key)

        # Test normal operation
        project_name = jinn.get_project_name()
        self.assertEqual(project_name, "test-project")
        self.assertEqual(jinn.project_name, "test-project")

        # Test API error
        self.mock_requests_get.side_effect = requests.RequestException("API Error")
        with self.assertRaises(JinnAPIError):
            jinn.get_project_name()

        # Reset the side effect
        def mock_get_side_effect(url, **kwargs):
            if "/inventory/project/" in url:
                return self.mock_project_response
            elif "/inventory/servers/" in url:
                return self.mock_servers_response
            elif "/ssh-tools/ssh-config/" in url:
                return self.mock_ssh_response
            elif "/inventory/groups/" in url:
                return self.mock_groups_response
            else:
                raise ValueError(f"Unexpected URL: {url}")

        self.mock_requests_get.side_effect = mock_get_side_effect

    def test_get_groups(self):
        """Test the get_groups method."""
        jinn = Jinn(api_key=self.api_key)

        # Test normal operation without saving
        groups = jinn.get_groups(save=False)
        self.assertEqual(groups, ["group1", "group2", "group3"])
        self.assertNotEqual(jinn.groups, groups)  # Not saved

        # Test normal operation with saving
        groups = jinn.get_groups(save=True)
        self.assertEqual(groups, ["group1", "group2", "group3"])
        self.assertEqual(jinn.groups, groups)  # Saved

        # Test API error
        self.mock_requests_get.side_effect = requests.RequestException("API Error")
        with self.assertRaises(JinnAPIError):
            jinn.get_groups()

        # Reset the side effect
        def mock_get_side_effect(url, **kwargs):
            if "/inventory/project/" in url:
                return self.mock_project_response
            elif "/inventory/servers/" in url:
                return self.mock_servers_response
            elif "/ssh-tools/ssh-config/" in url:
                return self.mock_ssh_response
            elif "/inventory/groups/" in url:
                return self.mock_groups_response
            else:
                raise ValueError(f"Unexpected URL: {url}")

        self.mock_requests_get.side_effect = mock_get_side_effect

    def test_format_host_list(self):
        """Test the format_host_list method."""
        jinn = Jinn(api_key=self.api_key)

        # Test with sample server data
        filtered_servers = self.sample_server_data["result"]
        host_list = jinn.format_host_list(filtered_servers)

        # Check the first server in the list
        hostname, attributes = host_list[0]
        self.assertEqual(hostname, "server1")
        self.assertEqual(attributes["ssh_user"], "admin")
        self.assertEqual(attributes.get("ssh_hostname"), "server1.example.com")
        self.assertEqual(attributes.get("bastion_host"), "bastion.example.com")
        self.assertEqual(attributes.get("bastion_user"), "bastion_user")
        self.assertEqual(attributes.get("bastion_port"), 22)
        self.assertTrue(attributes["is_active"])
        self.assertEqual(attributes["group_name"], "group1")
        self.assertEqual(attributes["tags"], ["tag1", "web"])
        self.assertEqual(attributes["role"], "webserver")
        self.assertEqual(attributes["environment"], "prod")

        # Check the second server in the list (no bastion)
        hostname, attributes = host_list[1]
        self.assertEqual(hostname, "server2")
        self.assertEqual(attributes["ssh_user"], "admin")
        self.assertEqual(attributes.get("ssh_hostname"), "server2.example.com")
        self.assertIsNone(attributes.get("bastion_host"))
        self.assertIsNone(attributes.get("bastion_user"))
        self.assertIsNone(attributes.get("bastion_port"))

    def test_filter_server(self):
        """Test the _filter_server method."""
        # Test with no filters
        jinn = Jinn(api_key=self.api_key)
        server1 = self.sample_server_data["result"][
            0
        ]  # Active server in group1 with tag1
        server3 = self.sample_server_data["result"][2]

        # Server should pass with no filters if active
        self.assertTrue(jinn._filter_server(server1))

        # Inactive server should never pass
        self.assertFalse(jinn._filter_server(server3))

        # Test with group filter
        jinn.groups = ["group1"]
        self.assertTrue(jinn._filter_server(server1))

        # Test with non-matching group filter
        jinn.groups = ["group3"]
        self.assertFalse(jinn._filter_server(server1))

        # Test with tag filter
        jinn.groups = None
        jinn.tags = ["tag1"]
        self.assertTrue(jinn._filter_server(server1))

        # Test with non-matching tag filter
        jinn.tags = ["tag3"]
        self.assertFalse(jinn._filter_server(server1))

    def test_load_servers(self):
        """Test the load_servers method."""
        with patch.object(Jinn, "refresh_ssh_config"):
            with patch.object(Path, "home", return_value=Path("/home/test")):
                # Test normal operation
                jinn = Jinn(api_key=self.api_key)
                jinn.load_servers()

                # Should have loaded 2 servers (the active ones)
                self.assertEqual(len(jinn.servers), 2)
                self.assertEqual(jinn.servers[0][0], "server1")
                self.assertEqual(jinn.servers[1][0], "server2")

                # Test with filters that exclude all servers
                jinn.groups = ["nonexistent"]
                with self.assertRaises(JinnAPIError):
                    jinn.load_servers()

                # Test various API errors
                error_cases = [
                    ("timeout", requests.Timeout("Timeout")),
                    ("http_error", requests.HTTPError("HTTP Error")),
                    ("request_exception", requests.RequestException("Request Error")),
                    (
                        "json_decode_error",
                        json.JSONDecodeError("JSON Decode Error", "", 0),
                    ),
                    ("key_error", KeyError("Missing Key")),
                    ("unexpected_error", Exception("Unexpected Error")),
                ]

                for _, error_exception in error_cases:
                    # Test error handling in the load_servers method directly, not in __init__
                    self.mock_requests_get.side_effect = error_exception
                    with self.assertRaises(JinnAPIError):
                        # Create a fresh jinn object and then test load_servers
                        # This avoids the initialization errors that were causing test failures
                        with patch.object(Jinn, "get_project_name"):
                            with patch.object(Jinn, "load_servers"):
                                test_jinn = Jinn(api_key=self.api_key)
                        # Now test the load_servers method with the error
                        test_jinn.load_servers()

    def test_get_servers(self):
        """Test the get_servers method."""
        jinn = Jinn(api_key=self.api_key)
        servers = jinn.get_servers()

        # Should return the servers loaded in __init__
        self.assertEqual(len(servers), 2)
        self.assertEqual(servers[0][0], "server1")
        self.assertEqual(servers[1][0], "server2")

    def test_get_ssh_config(self):
        """Test the get_ssh_config method."""
        # Test normal operation
        with patch.object(Jinn, "refresh_ssh_config"):
            jinn = Jinn(api_key=self.api_key, api_url=self.api_url, use_bastion=True)
            ssh_config = jinn.get_ssh_config()

            # Should have returned the mock SSH config
            self.assertEqual(ssh_config, self.mock_ssh_config)

            # Test with bastion
            jinn.use_bastion = True
            jinn.get_ssh_config()
            self.mock_requests_get.assert_called_with(
                f"{self.api_url}/ssh-tools/ssh-config/",
                headers={"Authentication": self.api_key},
                params={"bastionless": False},
                timeout=30,
            )

            # Test without bastion
            jinn.use_bastion = False
            jinn.get_ssh_config()
            self.mock_requests_get.assert_called_with(
                f"{self.api_url}/ssh-tools/ssh-config/",
                headers={"Authentication": self.api_key},
                params={"bastionless": True},
                timeout=30,
            )

        # Test API error
        self.mock_requests_get.side_effect = requests.RequestException("API Error")
        with self.assertRaises(JinnAPIError):
            jinn.get_ssh_config()

    def test_save_ssh_config(self):
        """Test the save_ssh_config method."""
        with patch.object(Jinn, "refresh_ssh_config"):
            jinn = Jinn(api_key=self.api_key)

            # Reset the mock before the test
            self.mock_path_write_text.reset_mock()

            jinn.project_name = "test-project"
            jinn.save_ssh_config(self.mock_ssh_config)

            # The implementation now joins the lines with '\n' which modifies the input
            # So we don't check exact match, but verify the call was made
            self.mock_path_write_text.assert_called_once()

            # Check that the permissions were set
            self.mock_os_chmod.assert_called()

            # Test error handling
            self.mock_path_write_text.side_effect = Exception("Write Error")
            with self.assertRaises(JinnSSHError):
                jinn.save_ssh_config(self.mock_ssh_config)

    def test_update_main_ssh_config_new_file(self):
        """Test the update_main_ssh_config method with a new config file."""
        # Test when the main SSH config doesn't exist
        self.mock_path_read_text.side_effect = FileNotFoundError("File not found")

        # Define a proper exists mock function that takes a path parameter
        def mock_exists(path_obj):
            # Return False only for the SSH config file
            return not str(path_obj).endswith("/config")

        # Patch the Path.exists method and other necessary methods
        with patch.object(Jinn, "refresh_ssh_config"):
            with patch("pathlib.Path.exists", mock_exists):
                with patch.object(Path, "home", return_value=Path("/home/test")):
                    jinn = Jinn(api_key=self.api_key)

                    # Reset mocks for this specific test
                    self.mock_os_chmod.reset_mock()

                    # Mock the file operations
                    m = mock_open()
                    with patch("builtins.open", m):
                        jinn.update_main_ssh_config()

                    # Check that the file was opened for writing
                    m.assert_called_once()
                    file_handle = m()

                    # In the new implementation, with a new file we only write the include directive without a leading newline
                    include_directive = f"Include {jinn.ssh_config_dir}/*\n"
                    file_handle.write.assert_called_with(include_directive)

                    # Check that the permissions were set
                    self.mock_os_chmod.assert_called_once()

    def test_update_main_ssh_config_existing_file(self):
        """Test the update_main_ssh_config method with an existing config file."""
        # Test when the main SSH config exists but doesn't have the include directive
        self.mock_path_read_text.return_value = (
            "Host *\n    StrictHostKeyChecking yes\n"
        )

        with patch.object(Jinn, "refresh_ssh_config"):
            with patch("pathlib.Path.exists", return_value=True):
                jinn = Jinn(api_key=self.api_key)

                # Mock the file operations
                m = mock_open()
                with patch("builtins.open", m):
                    jinn.update_main_ssh_config()

                # Check that the file was opened for writing
                m.assert_called_once()
                file_handle = m()

                # The implementation now uses multiple write calls
                # Verify the include directive was written as the last call
                include_directive = f"Include {jinn.ssh_config_dir}/*\n"
                calls = file_handle.write.call_args_list
                self.assertTrue(
                    any(call[0][0] == include_directive for call in calls),
                    f"Include directive not found in calls: {calls}",
                )

                # Note: In the updated implementation, the file is always rewritten to ensure
                # there's only a single include directive, so we don't test for not opening the file anymore

                # Test error handling
                self.mock_path_read_text.side_effect = Exception("Read Error")
                with self.assertRaises(JinnSSHError):
                    jinn.update_main_ssh_config()

    def test_refresh_ssh_config(self):
        """Test the refresh_ssh_config method."""
        jinn = Jinn(api_key=self.api_key)

        # Mock the individual methods to check they're called
        with patch.object(jinn, "get_ssh_config") as mock_get_ssh_config:
            with patch.object(jinn, "save_ssh_config") as mock_save_ssh_config:
                with patch.object(
                    jinn, "update_main_ssh_config"
                ) as mock_update_main_ssh_config:
                    mock_get_ssh_config.return_value = self.mock_ssh_config

                    jinn.refresh_ssh_config()

                    # Check that all methods were called
                    mock_get_ssh_config.assert_called_once()
                    mock_save_ssh_config.assert_called_once_with(self.mock_ssh_config)
                    mock_update_main_ssh_config.assert_called_once()

    def test_get_server_by_hostname(self):
        """Test the get_server_by_hostname method."""
        jinn = Jinn(api_key=self.api_key)

        # Test finding an existing server
        server1 = jinn.get_server_by_hostname("server1")
        self.assertIsNotNone(server1)

        if server1 is not None:
            self.assertEqual(server1.get("ssh_hostname"), "server1.example.com")

        # Test finding a non-existent server
        server_nonexistent = jinn.get_server_by_hostname("nonexistent")
        self.assertIsNone(server_nonexistent)

    def test_get_servers_by_group(self):
        """Test the get_servers_by_group method."""
        with patch.object(Jinn, "refresh_ssh_config"):
            jinn = Jinn(api_key=self.api_key)

            # Save the original groups
            original_groups = jinn.groups

            # Mock load_servers to check it's called with the right group
            with patch.object(jinn, "load_servers") as mock_load_servers:
                # Mock the actual method implementation directly
                jinn.get_servers_by_group("group1")

                # Check that load_servers was called
                mock_load_servers.assert_called_once()

                # Verify groups was set to the expected value during the method call
                mock_load_servers.assert_called_with()  # No args as they're stored in the object
                self.assertEqual(
                    jinn.groups, original_groups
                )  # Should be restored after call

            # Test the functionality by directly setting the group and verifying the state
            jinn.groups = ["group1"]
            jinn.load_servers()  # Simulate loading servers with the group filter applied
            self.assertEqual(jinn.groups, ["group1"])

    def test_get_servers_by_tag(self):
        """Test the get_servers_by_tag method."""
        with patch.object(Jinn, "refresh_ssh_config"):
            jinn = Jinn(api_key=self.api_key)

            # Save the original tags
            original_tags = jinn.tags

            # Mock load_servers to check it's called with the right tag
            with patch.object(jinn, "load_servers") as mock_load_servers:
                # Call the tag method
                jinn.get_servers_by_tag("tag1")

                # Check that load_servers was called
                mock_load_servers.assert_called_once()

                # Verify tags was restored after the call
                self.assertEqual(jinn.tags, original_tags)

            # Test with actual servers using the real implementation
            # First reset the tags
            jinn.tags = None

            # Get servers with tag1
            servers_with_tag1 = jinn.get_servers_by_tag("tag1")

            # Verify we got the right servers
            self.assertTrue(len(servers_with_tag1) > 0)
            # Verify that all returned servers have the tag1
            for _, server_attrs in servers_with_tag1:
                self.assertIn("tag1", server_attrs["tags"])

            # Verify the original tags were restored
            self.assertEqual(jinn.tags, original_tags)


if __name__ == "__main__":
    unittest.main()
