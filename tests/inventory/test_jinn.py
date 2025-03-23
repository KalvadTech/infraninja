#!/usr/bin/env python3
# tests/inventory/test_jinn.py

import unittest
from unittest.mock import patch, Mock, MagicMock
import pytest
import requests
import sys
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from infraninja.inventory.jinn import fetch_ssh_config

class TestFetchSSHConfig(unittest.TestCase):
    """Test suite for the fetch_ssh_config function."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.api_auth_key = "test_api_key"
        self.base_api_url = "https://api.example.com"
        self.config_endpoint = "/ssh-config"  # This assumes this endpoint is used in NinjaConfig
        
        # Create a mock for the config object with the required attribute
        self.config_patcher = patch('infraninja.inventory.jinn.config')
        self.mock_config = self.config_patcher.start()
        self.mock_config.ssh_config_endpoint = self.config_endpoint

    def tearDown(self):
        """Clean up test fixtures after each test method."""
        self.config_patcher.stop()

    @patch('infraninja.inventory.jinn.requests.get')
    def test_successful_fetch(self, mock_get):
        """Test fetch_ssh_config with a successful API response."""
        # Arrange
        expected_ssh_config = "Host example\n  HostName example.com"
        mock_response = Mock()
        mock_response.text = expected_ssh_config
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        # Act
        result = fetch_ssh_config(self.api_auth_key, self.base_api_url)
        
        # Assert
        mock_get.assert_called_once_with(
            f"{self.base_api_url}{self.config_endpoint}",
            headers={"Authentication": self.api_auth_key},
            params={"bastionless": True},
            timeout=10
        )
        self.assertEqual(result, expected_ssh_config)

    @patch('infraninja.inventory.jinn.requests.get')
    def test_bastionless_parameter(self, mock_get):
        """Test fetch_ssh_config with bastionless=False parameter."""
        # Arrange
        expected_ssh_config = "Host bastion\n  HostName bastion.example.com"
        mock_response = Mock()
        mock_response.text = expected_ssh_config
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        # Act
        result = fetch_ssh_config(self.api_auth_key, self.base_api_url, bastionless=False)
        
        # Assert
        mock_get.assert_called_once_with(
            f"{self.base_api_url}{self.config_endpoint}",
            headers={"Authentication": self.api_auth_key},
            params={"bastionless": False},
            timeout=10
        )
        self.assertEqual(result, expected_ssh_config)

    @patch('infraninja.inventory.jinn.requests.get')
    def test_http_error(self, mock_get):
        """Test fetch_ssh_config when the API returns an HTTP error."""
        # Arrange
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.HTTPError("404 Client Error")
        mock_get.return_value = mock_response
        
        # Act & Assert
        with self.assertRaises(RuntimeError) as context:
            fetch_ssh_config(self.api_auth_key, self.base_api_url)
        
        self.assertIn("Failed to fetch SSH config", str(context.exception))

    @patch('infraninja.inventory.jinn.requests.get')
    def test_timeout_error(self, mock_get):
        """Test fetch_ssh_config when the API request times out."""
        # Arrange
        mock_get.side_effect = requests.Timeout("Request timed out")
        
        # Act & Assert
        with self.assertRaises(RuntimeError) as context:
            fetch_ssh_config(self.api_auth_key, self.base_api_url)
        
        self.assertIn("Failed to fetch SSH config", str(context.exception))

    @patch('infraninja.inventory.jinn.requests.get')
    def test_connection_error(self, mock_get):
        """Test fetch_ssh_config when there is a connection error."""
        # Arrange
        mock_get.side_effect = requests.ConnectionError("Connection refused")
        
        # Act & Assert
        with self.assertRaises(RuntimeError) as context:
            fetch_ssh_config(self.api_auth_key, self.base_api_url)
        
        self.assertIn("Failed to fetch SSH config", str(context.exception))

    @patch('infraninja.inventory.jinn.requests.get')
    def test_url_trailing_slash_handling(self, mock_get):
        """Test that the function correctly handles URLs with and without trailing slashes."""
        # Arrange
        expected_ssh_config = "Host example\n  HostName example.com"
        mock_response = Mock()
        mock_response.text = expected_ssh_config
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        # Test URL with trailing slash
        base_url_with_slash = "https://api.example.com/"
        
        # Act
        result = fetch_ssh_config(self.api_auth_key, base_url_with_slash)
        
        # Assert
        mock_get.assert_called_with(
            f"https://api.example.com{self.config_endpoint}",
            headers={"Authentication": self.api_auth_key},
            params={"bastionless": True},
            timeout=10
        )
        self.assertEqual(result, expected_ssh_config)


# Run tests with pytest when this file is executed directly
if __name__ == "__main__":
    pytest.main(["-xvs", __file__])