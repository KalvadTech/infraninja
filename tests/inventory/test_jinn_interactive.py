#!/usr/bin/env python3
# tests/inventory/test_jinn_interactive.py

import sys

from pathlib import Path
from unittest.mock import patch, Mock

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from infraninja.inventory.jinn import (
    get_valid_filename,
    get_group_selection,
    process_tag_selection,
    select_ssh_key,
    fetch_servers,
)


class TestUserInputHandling:
    """Test suite for functions that handle user input."""

    @patch("infraninja.inventory.jinn.input")
    def test_get_valid_filename_default(self, mock_input):
        """Test get_valid_filename returns default when no input is provided."""
        # Setup mock to return empty string (user just presses Enter)
        mock_input.return_value = ""

        # Call function with a default filename
        result = get_valid_filename("default_name")

        # Assert the result is the default
        assert result == "default_name"

    @patch("infraninja.inventory.jinn.input")
    def test_get_valid_filename_valid_input(self, mock_input):
        """Test get_valid_filename with valid input."""
        # Setup mock to return a valid filename
        mock_input.return_value = "my_config"

        # Call function
        result = get_valid_filename("default_name")

        # Assert the result is the user input
        assert result == "my_config"

    @patch("infraninja.inventory.jinn.input")
    @patch("infraninja.inventory.jinn.logger")
    def test_get_valid_filename_invalid_then_valid(self, mock_logger, mock_input):
        """Test get_valid_filename handles invalid input followed by valid input."""
        # Setup mock to return an invalid filename first, then a valid one
        mock_input.side_effect = ["my/invalid/path", "valid_name"]

        # Call function
        result = get_valid_filename("default_name")

        # Assert the result is the second (valid) input
        assert result == "valid_name"
        # Assert warning was logged
        mock_logger.warning.assert_called_once()

    @patch("infraninja.inventory.jinn.input")
    @patch("infraninja.inventory.jinn.logger")
    def test_get_valid_filename_with_invalid_chars(self, mock_logger, mock_input):
        """Test get_valid_filename handles filenames with invalid characters."""
        # Setup mock to return an invalid filename with special chars, then a valid one
        mock_input.side_effect = ["invalid!@#$%^&*", "valid_name"]

        # Call function
        result = get_valid_filename("default_name")

        # Assert the result is the second (valid) input
        assert result == "valid_name"
        # Assert warning was logged
        mock_logger.warning.assert_called_once()

    @patch("infraninja.inventory.jinn.input")
    def test_get_group_selection_all(self, mock_input):
        """Test get_group_selection when user selects all groups."""
        # Setup
        groups = ["production", "staging", "development"]
        mock_input.return_value = "*"

        # Execute
        selected = get_group_selection(groups)

        # Assert
        assert selected == groups

    @patch("infraninja.inventory.jinn.input")
    def test_get_group_selection_empty(self, mock_input):
        """Test get_group_selection when user provides empty input (also means all)."""
        # Setup
        groups = ["production", "staging", "development"]
        mock_input.return_value = ""

        # Execute
        selected = get_group_selection(groups)

        # Assert
        assert selected == groups

    @patch("infraninja.inventory.jinn.input")
    def test_get_group_selection_specific(self, mock_input):
        """Test get_group_selection when user selects specific groups."""
        # Setup
        groups = ["production", "staging", "development"]
        mock_input.return_value = "1 3"  # Select production and development

        # Execute
        selected = get_group_selection(groups)

        # Assert
        assert selected == ["production", "development"]

    @patch("infraninja.inventory.jinn.input")
    @patch("infraninja.inventory.jinn.logger")
    def test_get_group_selection_invalid_then_valid(self, mock_logger, mock_input):
        """Test get_group_selection handles invalid input followed by valid input."""
        # Setup
        groups = ["production", "staging", "development"]
        mock_input.side_effect = ["invalid", "1 2"]

        # Execute
        selected = get_group_selection(groups)

        # Assert
        assert selected == ["production", "staging"]
        mock_logger.warning.assert_called_once()

    @patch("infraninja.inventory.jinn.input")
    @patch("infraninja.inventory.jinn.logger")
    def test_get_group_selection_out_of_range(self, mock_logger, mock_input):
        """Test get_group_selection handles out-of-range input followed by valid input."""
        # Setup
        groups = ["production", "staging", "development"]
        mock_input.side_effect = ["1 4", "2 3"]  # 4 is out of range, then valid input

        # Execute
        selected = get_group_selection(groups)

        # Assert
        assert selected == ["staging", "development"]
        mock_logger.warning.assert_called_once()

    @patch("infraninja.inventory.jinn.os.environ.get")
    def test_get_group_selection_from_env(self, mock_env_get):
        """Test get_group_selection reads from environment variable if set."""
        # Setup
        groups = ["production", "staging", "development"]
        mock_env_get.return_value = "2"  # Select staging

        # Execute
        selected = get_group_selection(groups)

        # Assert
        assert selected == ["staging"]

    def test_process_tag_selection_all_tags(self):
        """Test process_tag_selection when all tags are selected."""
        # Setup
        tags = ["web", "db", "cache"]
        servers = [
            {"hostname": "server1", "tags": ["web"]},
            {"hostname": "server2", "tags": ["db"]},
        ]

        with patch("infraninja.inventory.jinn.input", return_value="*"):
            # Execute
            result = process_tag_selection(tags, servers)

            # Assert - should return all servers
            assert len(result) == 2
            assert result[0]["hostname"] == "server1"
            assert result[1]["hostname"] == "server2"

    def test_process_tag_selection_specific_tags(self):
        """Test process_tag_selection when specific tags are selected."""
        # Setup
        tags = ["web", "db", "cache"]
        servers = [
            {"hostname": "server1", "tags": ["web"]},
            {"hostname": "server2", "tags": ["db"]},
            {"hostname": "server3", "tags": ["cache"]},
        ]

        with patch(
            "infraninja.inventory.jinn.input", return_value="1"
        ):  # Select "web" tag
            # Execute
            result = process_tag_selection(tags, servers)

            # Assert - should only return servers with "web" tag
            assert len(result) == 1
            assert result[0]["hostname"] == "server1"

    def test_process_tag_selection_no_tags(self):
        """Test process_tag_selection when no tags are available."""
        # Setup
        tags = []
        servers = [{"hostname": "server1"}, {"hostname": "server2"}]

        # Execute
        result = process_tag_selection(tags, servers)

        # Assert - should return all servers without asking for input
        assert len(result) == 2
        assert result[0]["hostname"] == "server1"
        assert result[1]["hostname"] == "server2"

    @patch("infraninja.inventory.jinn.os.environ.get")
    def test_process_tag_selection_from_env(self, mock_env_get):
        """Test process_tag_selection reads from environment variable if set."""
        # Setup
        tags = ["web", "db", "cache"]
        servers = [
            {"hostname": "server1", "tags": ["web"]},
            {"hostname": "server2", "tags": ["db"]},
            {"hostname": "server3", "tags": ["cache"]},
        ]

        mock_env_get.return_value = "2"  # Select "db" tag

        # Execute
        result = process_tag_selection(tags, servers)

        # Assert - should only return servers with "db" tag
        assert len(result) == 1
        assert result[0]["hostname"] == "server2"


class TestSSHKeySelection:
    """Test suite for SSH key selection functionality."""

    @patch("infraninja.inventory.jinn.find_ssh_keys")
    @patch("infraninja.inventory.jinn.input")
    def test_select_ssh_key_with_available_keys(self, mock_input, mock_find_keys):
        """Test select_ssh_key when keys are available and user selects one."""
        # Setup
        available_keys = ["/home/user/.ssh/id_rsa", "/home/user/.ssh/id_ed25519"]
        mock_find_keys.return_value = available_keys
        mock_input.return_value = "2"  # Select the second key

        with patch("infraninja.inventory.jinn.logger"):
            # Execute
            selected_key = select_ssh_key()

            # Assert
            assert selected_key == "/home/user/.ssh/id_ed25519"

    @patch("infraninja.inventory.jinn.find_ssh_keys")
    @patch("infraninja.inventory.jinn.input")
    @patch("infraninja.inventory.jinn.logger")
    def test_select_ssh_key_default(self, mock_logger, mock_input, mock_find_keys):
        """Test select_ssh_key when user selects the default option."""
        # Setup
        available_keys = ["/home/user/.ssh/id_rsa", "/home/user/.ssh/id_ed25519"]
        mock_find_keys.return_value = available_keys
        mock_input.return_value = ""  # Empty input (default)

        # Execute
        selected_key = select_ssh_key()

        # Assert
        assert selected_key == "/home/user/.ssh/id_rsa"

    @patch("infraninja.inventory.jinn.find_ssh_keys")
    @patch("infraninja.inventory.jinn.input")
    @patch("infraninja.inventory.jinn.logger")
    def test_select_ssh_key_custom_path(self, mock_logger, mock_input, mock_find_keys):
        """Test select_ssh_key when user chooses to specify a custom path."""
        # Setup
        available_keys = ["/home/user/.ssh/id_rsa", "/home/user/.ssh/id_ed25519"]
        mock_find_keys.return_value = available_keys
        # First input selects the custom option, second input is the custom path
        mock_input.side_effect = ["3", "/custom/path/to/key"]

        # Execute
        selected_key = select_ssh_key()

        # Assert
        assert selected_key == "/custom/path/to/key"

    @patch("infraninja.inventory.jinn.find_ssh_keys")
    @patch("infraninja.inventory.jinn.input")
    @patch("infraninja.inventory.jinn.logger")
    @patch("infraninja.inventory.jinn.os.path.expanduser")
    def test_select_ssh_key_no_keys_found(
        self, mock_expanduser, mock_logger, mock_input, mock_find_keys
    ):
        """Test select_ssh_key when no keys are found and user must specify a path."""
        # Setup
        mock_find_keys.return_value = []  # No keys found
        mock_input.return_value = "/custom/path/to/key"
        mock_expanduser.side_effect = (
            lambda x: x
        )  # Return input unchanged for this test

        # Execute
        selected_key = select_ssh_key()

        # Assert
        assert selected_key == "/custom/path/to/key"
        mock_logger.warning.assert_called_once()  # Should warn that no keys were found


class TestServerFetching:
    """Test suite for server fetching functionality."""

    @patch("infraninja.inventory.jinn.requests.get")
    @patch("infraninja.inventory.jinn.get_groups_from_data")
    @patch("infraninja.inventory.jinn.get_project_name")
    @patch("infraninja.inventory.jinn.get_group_selection")
    @patch("infraninja.inventory.jinn.process_tag_selection")
    @patch("infraninja.inventory.jinn.get_tags_from_data")
    @patch("infraninja.inventory.jinn.format_host_list")
    @patch("infraninja.inventory.jinn.logger")
    @patch("infraninja.inventory.jinn.config")
    def test_fetch_servers_success(
        self,
        mock_config,
        mock_logger,
        mock_format_host_list,
        mock_get_tags,
        mock_process_tags,
        mock_get_group_selection,
        mock_get_project_name,
        mock_get_groups,
        mock_requests_get,
    ):
        """Test fetch_servers with a successful API response."""
        # Setup
        mock_config.inventory_endpoint = "/inventory"

        # Mock API response
        mock_response = Mock()
        mock_response.json.return_value = {"result": [{"hostname": "server1"}]}
        mock_response.raise_for_status = Mock()
        mock_requests_get.return_value = mock_response

        # Mock function returns
        mock_get_project_name.return_value = "test_project"
        mock_get_groups.return_value = ["production", "staging"]
        mock_get_group_selection.return_value = ["production"]
        mock_get_tags.return_value = ["web", "db"]

        # Mock filtered servers after group and tag selection
        filtered_servers = [{"hostname": "server1", "is_active": True}]
        mock_process_tags.return_value = filtered_servers

        # Mock final host list
        expected_host_list = [("server1", {"ssh_key": "/path/to/key"})]
        mock_format_host_list.return_value = expected_host_list

        # Execute
        host_list, project = fetch_servers("test_key", "https://api.example.com")

        # Assert
        mock_requests_get.assert_called_once_with(
            "https://api.example.com/inventory",
            headers={"Authentication": "test_key"},
            timeout=30,
        )
        assert host_list == expected_host_list
        assert project == "test_project"

    @patch("infraninja.inventory.jinn.requests.get")
    @patch("infraninja.inventory.jinn.logger")
    @patch("infraninja.inventory.jinn.config")
    def test_fetch_servers_with_http_error(
        self, mock_config, mock_logger, mock_requests_get
    ):
        """Test fetch_servers handles HTTP errors gracefully."""
        # Setup
        mock_config.inventory_endpoint = "/inventory"

        # Mock API response to raise an exception
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = Exception("HTTP Error")
        mock_requests_get.return_value = mock_response

        # Execute
        host_list, project = fetch_servers("test_key", "https://api.example.com")

        # Assert
        assert host_list == []
        assert project == "default"
        mock_logger.error.assert_called_once()

    @patch("infraninja.inventory.jinn.requests.get")
    @patch("infraninja.inventory.jinn.logger")
    @patch("infraninja.inventory.jinn.config")
    def test_fetch_servers_with_timeout(
        self, mock_config, mock_logger, mock_requests_get
    ):
        """Test fetch_servers handles request timeouts gracefully."""
        # Setup
        mock_config.inventory_endpoint = "/inventory"

        # Mock API request to time out
        from requests.exceptions import Timeout

        mock_requests_get.side_effect = Timeout("Request timed out")

        # Execute
        host_list, project = fetch_servers("test_key", "https://api.example.com")

        # Assert
        assert host_list == []
        assert project == "default"
        mock_logger.error.assert_called_once_with("API request timed out")

    @patch("infraninja.inventory.jinn.requests.get")
    @patch("infraninja.inventory.jinn.logger")
    @patch("infraninja.inventory.jinn.config")
    def test_fetch_servers_with_selected_group(
        self, mock_config, mock_logger, mock_requests_get
    ):
        """Test fetch_servers with a pre-selected group (no user selection)."""
        # Setup
        mock_config.inventory_endpoint = "/inventory"

        # Mock API response
        mock_response = Mock()
        mock_response.json.return_value = {
            "result": [
                {
                    "hostname": "server1",
                    "group": {"name_en": "production"},
                    "is_active": True,
                },
                {
                    "hostname": "server2",
                    "group": {"name_en": "staging"},
                    "is_active": True,
                },
            ]
        }
        mock_response.raise_for_status = Mock()
        mock_requests_get.return_value = mock_response

        # Execute - provide a pre-selected group
        host_list, project = fetch_servers(
            "test_key", "https://api.example.com", selected_group="production"
        )

        # Assert
        # Verify that only production servers are included
        assert len(host_list) == 1  # Only the production server should be included
