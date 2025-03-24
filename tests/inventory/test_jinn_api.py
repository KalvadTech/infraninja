#!/usr/bin/env python3
# tests/inventory/test_jinn_api.py

import pytest
import sys
import json
from pathlib import Path
from unittest.mock import patch, Mock

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import requests
from infraninja.inventory.jinn import fetch_ssh_config, fetch_servers


class TestAPIIntegration:
    """Test suite for API integration functionality."""

    @patch("infraninja.inventory.jinn.requests.get")
    def test_fetch_ssh_config_url_formatting(self, mock_get):
        """Test fetch_ssh_config handles various URL formats correctly."""
        # Setup
        mock_response = Mock()
        mock_response.text = "Host example\n  HostName example.com"
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        api_key = "test_api_key"
        config_endpoint = "/ssh-config"

        with patch("infraninja.inventory.jinn.config") as mock_config:
            mock_config.ssh_config_endpoint = config_endpoint

            # Test base URL with trailing slash
            fetch_ssh_config(api_key, "https://api.example.com/")
            mock_get.assert_called_with(
                "https://api.example.com/ssh-config",
                headers={"Authentication": api_key},
                params={"bastionless": True},
                timeout=10,
            )

            # Test base URL without trailing slash
            fetch_ssh_config(api_key, "https://api.example.com")
            mock_get.assert_called_with(
                "https://api.example.com/ssh-config",
                headers={"Authentication": api_key},
                params={"bastionless": True},
                timeout=10,
            )

    @patch("infraninja.inventory.jinn.requests.get")
    def test_fetch_ssh_config_error_handling(self, mock_get):
        """Test fetch_ssh_config handles various error conditions properly."""
        errors = [
            requests.exceptions.ConnectTimeout("Connection timed out"),
            requests.exceptions.ReadTimeout("Read timed out"),
            requests.exceptions.ConnectionError("Connection refused"),
            requests.exceptions.HTTPError("404 Client Error"),
            ValueError("Invalid response"),
        ]

        for error in errors:
            # Setup mock to raise the current error
            mock_get.side_effect = error

            # Test error handling
            with pytest.raises(RuntimeError) as excinfo:
                fetch_ssh_config("api_key", "https://api.example.com")

            # Verify error message
            assert "Failed to fetch SSH config" in str(excinfo.value)
            assert str(error) in str(excinfo.value)

    @patch("infraninja.inventory.jinn.requests.get")
    def test_api_response_structure_handling(self, mock_get):
        """Test that API response structure is correctly validated."""
        # Setup mock to return valid JSON but with unexpected structure
        mock_response = Mock()
        mock_response.json.return_value = {"unexpected": "structure"}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        with patch("infraninja.inventory.jinn.logger") as mock_logger:
            with patch("infraninja.inventory.jinn.config") as mock_config:
                mock_config.inventory_endpoint = "/inventory"

                # Execute
                servers, project = fetch_servers("api_key", "https://api.example.com")

                # Verify
                assert servers == []
                assert project == "default"

    @patch("infraninja.inventory.jinn.requests.get")
    def test_json_decode_error_handling(self, mock_get):
        """Test handling of malformed JSON responses."""
        # Setup mock to raise JSONDecodeError
        mock_response = Mock()
        mock_response.json.side_effect = json.JSONDecodeError("Malformed JSON", "", 0)
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        with patch("infraninja.inventory.jinn.logger") as mock_logger:
            with patch("infraninja.inventory.jinn.config") as mock_config:
                mock_config.inventory_endpoint = "/inventory"

                # Execute
                servers, project = fetch_servers("api_key", "https://api.example.com")

                # Verify
                assert servers == []
                assert project == "default"
                mock_logger.error.assert_called_once()
