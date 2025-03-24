#!/usr/bin/env python3
# tests/inventory/test_jinn_inventory.py

import os
import sys
from pathlib import Path
from unittest.mock import patch

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from infraninja.inventory.jinn import (
    get_groups_from_data,
    get_tags_from_data,
    get_project_name,
    save_ssh_config,
    update_main_ssh_config,
    format_host_list,
    find_ssh_keys,
)


class TestDataExtractionFunctions:
    """Test suite for data extraction functions in jinn.py."""

    def test_get_groups_from_data(self, sample_server_data):
        """Test that get_groups_from_data properly extracts unique groups."""
        groups = get_groups_from_data(sample_server_data)

        # Should extract 'production' and 'staging' groups in alphabetical order
        assert groups == ["production", "staging"]

    def test_get_groups_from_empty_data(self):
        """Test get_groups_from_data with empty data."""
        empty_data = {"result": []}
        groups = get_groups_from_data(empty_data)
        assert groups == []

    def test_get_groups_from_data_with_missing_group(self, sample_server_data):
        """Test get_groups_from_data with a server missing group information."""
        # Add a server with missing group info
        modified_data = sample_server_data.copy()
        modified_data["result"].append({"hostname": "server4", "group": {}})

        groups = get_groups_from_data(modified_data)
        # Should still extract only 'production' and 'staging'
        assert groups == ["production", "staging"]

    def test_get_tags_from_data(self, sample_server_data):
        """Test that get_tags_from_data properly extracts unique tags."""
        # Extract the servers from the sample data
        servers = sample_server_data["result"]
    
        tags = get_tags_from_data(servers)
        # Should extract all tags in alphabetical order
        assert tags == ["api", "backup", "db", "inactive", "web"]

    def test_get_tags_from_empty_data(self):
        """Test get_tags_from_data with empty data."""
        empty_servers = []
        tags = get_tags_from_data(empty_servers)
        assert tags == []

    def test_get_tags_with_whitespace_and_empty(self):
        """Test get_tags_from_data handles whitespace and empty tags properly."""
        servers = [
            {"hostname": "server1", "tags": ["valid", "", "  ", "another"]},
        ]

        tags = get_tags_from_data(servers)
        # Should only include non-empty, non-whitespace tags
        assert tags == ["another", "valid"]


class TestProjectNameExtraction:
    """Test suite for project name extraction functionality."""

    def test_get_project_name_valid(self, sample_server_data):
        """Test get_project_name with valid project data."""
        project_name = get_project_name(sample_server_data)
        assert project_name == "test_project"

    def test_get_project_name_empty_data(self):
        """Test get_project_name with empty data."""
        empty_data = {"result": []}
        project_name = get_project_name(empty_data)
        assert project_name == "default"

    def test_get_project_name_missing_project(self):
        """Test get_project_name with missing project information."""
        data = {
            "result": [
                {"hostname": "server1", "group": {"name_en": "group_without_project"}}
            ]
        }
        project_name = get_project_name(data)
        assert project_name == "default"


class TestSSHConfigManagement:
    """Test suite for SSH config management functions."""

    def test_save_ssh_config(self, tmp_path, monkeypatch, mock_config):
        """Test save_ssh_config creates directory and saves file correctly."""
        # Set up a temporary directory for testing
        ssh_config_dir = tmp_path / "configs"
        mock_config.ssh_config_dir = str(ssh_config_dir)

        # Mock the config object
        monkeypatch.setattr("infraninja.inventory.jinn.config", mock_config)

        # Test data
        config_content = "Host test\n  HostName test.example.com"
        filename = "test_config"

        # Execute the function
        with patch("infraninja.inventory.jinn.logger") as mock_logger:
            save_ssh_config(config_content, filename)

            # Check that the directory was created
            assert ssh_config_dir.exists()

            # Check that the file was created with correct content
            config_file = ssh_config_dir / filename
            assert config_file.exists()
            assert config_file.read_text() == config_content

            # Check that logging happened
            mock_logger.info.assert_called_once()

    def test_update_main_ssh_config_new_file(self, tmp_path, monkeypatch, mock_config):
        """Test update_main_ssh_config creates a new config file if it doesn't exist."""
        # Set up a temporary file for the main SSH config
        main_config = tmp_path / "config"
        mock_config.main_ssh_config = str(main_config)
        mock_config.ssh_config_dir = "/home/user/.ssh/configs"

        # Mock the config object
        monkeypatch.setattr("infraninja.inventory.jinn.config", mock_config)

        # Execute the function
        with patch("infraninja.inventory.jinn.logger") as mock_logger:
            update_main_ssh_config()

            # Check that the file was created with the include line
            assert main_config.exists()
            assert (
                f"\nInclude {mock_config.ssh_config_dir}/*\n" in main_config.read_text()
            )

            # Check that logging happened
            mock_logger.info.assert_called_once()

    def test_update_main_ssh_config_existing_file(
        self, tmp_path, monkeypatch, mock_config
    ):
        """Test update_main_ssh_config appends to an existing config file."""
        # Set up a temporary file for the main SSH config with existing content
        main_config = tmp_path / "config"
        main_config.write_text("# Existing SSH config\n\nHost *\n  ForwardAgent yes\n")

        mock_config.main_ssh_config = str(main_config)
        mock_config.ssh_config_dir = "/home/user/.ssh/configs"

        # Mock the config object
        monkeypatch.setattr("infraninja.inventory.jinn.config", mock_config)

        # Execute the function
        with patch("infraninja.inventory.jinn.logger") as mock_logger:
            update_main_ssh_config()

            # Check that the file was updated with the include line
            content = main_config.read_text()
            assert "# Existing SSH config" in content
            assert f"\nInclude {mock_config.ssh_config_dir}/*\n" in content

            # Check that logging happened
            mock_logger.info.assert_called_once()

    def test_update_main_ssh_config_already_included(
        self, tmp_path, monkeypatch, mock_config
    ):
        """Test update_main_ssh_config doesn't duplicate include lines."""
        # Set up config dir path
        config_dir = "/home/user/.ssh/configs"

        # Set up a temporary file for the main SSH config with the include line already present
        main_config = tmp_path / "config"
        main_config.write_text(f"# Existing SSH config\n\nInclude {config_dir}/*\n")

        mock_config.main_ssh_config = str(main_config)
        mock_config.ssh_config_dir = config_dir

        # Mock the config object
        monkeypatch.setattr("infraninja.inventory.jinn.config", mock_config)

        # Execute the function
        with patch("infraninja.inventory.jinn.logger") as mock_logger:
            update_main_ssh_config()

            # Check that the file wasn't modified
            content = main_config.read_text()
            assert content == f"# Existing SSH config\n\nInclude {config_dir}/*\n"

            # Check that no logging happened (no changes made)
            mock_logger.info.assert_not_called()


class TestHostListFormatting:
    """Test suite for host list formatting functions."""

    def test_format_host_list(self, sample_server_data):
        """Test format_host_list correctly formats server data."""
        # Extract active servers from sample data
        active_servers = [s for s in sample_server_data["result"] if s.get("is_active")]

        # Define SSH key path for test
        ssh_key_path = "/path/to/ssh/key"

        # Format the host list
        host_list = format_host_list(active_servers, ssh_key_path)

        # Check structure and content
        assert len(host_list) == 2  # Only active servers

        # Check first server
        hostname1, attrs1 = host_list[0]
        assert hostname1 == "server1"
        assert attrs1["ssh_user"] == "admin"
        assert attrs1["is_active"] is True
        assert attrs1["group_name"] == "production"
        assert "web" in attrs1["tags"]
        assert "api" in attrs1["tags"]
        assert attrs1["ssh_key"] == ssh_key_path
        assert attrs1["location"] == "eu-west"
        assert attrs1["role"] == "webserver"

        # Check second server
        hostname2, attrs2 = host_list[1]
        assert hostname2 == "server2"
        assert attrs2["group_name"] == "staging"
        assert "db" in attrs2["tags"]
        assert "backup" in attrs2["tags"]

    def test_format_host_list_with_default_key(self, sample_server_data, mock_config):
        """Test format_host_list with default SSH key path."""
        # Extract active servers from sample data
        active_servers = [s for s in sample_server_data["result"] if s.get("is_active")]

        # Format the host list with None as ssh_key_path to test default behavior
        with patch("infraninja.inventory.jinn.config", mock_config):
            host_list = format_host_list(active_servers, None)

            # Check that default SSH key path was used
            hostname, attrs = host_list[0]
            assert attrs["ssh_key"] == str(mock_config.ssh_key_path)


class TestSSHKeyFinding:
    """Test suite for SSH key finding functionality."""

    @patch("infraninja.inventory.jinn.os.path.expanduser")
    @patch("infraninja.inventory.jinn.glob.glob")
    @patch("infraninja.inventory.jinn.os.path.isfile")
    def test_find_ssh_keys(self, mock_isfile, mock_glob, mock_expanduser):
        """Test find_ssh_keys finds and sorts SSH keys correctly."""
        # Mock the expanduser function to return a fixed path
        mock_expanduser.return_value = "/home/user/.ssh"

        # Mock glob to return a list of files
        mock_glob.return_value = [
            "/home/user/.ssh/random_key",
            "/home/user/.ssh/id_rsa",
            "/home/user/.ssh/id_rsa.pub",  # Should be filtered out
            "/home/user/.ssh/known_hosts",  # Should be filtered out
            "/home/user/.ssh/config",  # Should be filtered out
            "/home/user/.ssh/id_ed25519",
            "/home/user/.ssh/.hidden_file",  # Should be filtered out
        ]

        # Mock isfile to return True for all files
        mock_isfile.return_value = True

        # Call the function
        keys = find_ssh_keys()

        # Check results
        assert len(keys) == 3
        # id_rsa should be first, followed by id_ed25519, then random_key
        assert keys[0] == "/home/user/.ssh/id_rsa"
        assert keys[1] == "/home/user/.ssh/id_ed25519"
        assert keys[2] == "/home/user/.ssh/random_key"

    def test_find_ssh_keys_with_temp_dir(self, monkeypatch, temp_ssh_dir):
        """Test find_ssh_keys with an actual temporary directory."""

        # Mock expanduser to return our temp directory
        def mock_expanduser(path):
            if path == "~/.ssh":
                return str(temp_ssh_dir)
            return path

        monkeypatch.setattr("os.path.expanduser", mock_expanduser)

        # Call the function
        keys = find_ssh_keys()

        # Check results
        assert (
            len(keys) == 2
        )  # Should find id_rsa and id_ed25519, but not .pub, config, or known_hosts

        # The keys should be sorted with id_rsa first
        assert os.path.basename(keys[0]) == "id_rsa"
        assert os.path.basename(keys[1]) == "id_ed25519"
