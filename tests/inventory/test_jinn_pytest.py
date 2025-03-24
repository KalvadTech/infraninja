#!/usr/bin/env python3
# tests/inventory/test_jinn_pytest.py

import pytest
from unittest.mock import patch, Mock
import requests
import sys
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from infraninja.inventory.jinn import fetch_ssh_config

# Test data
API_AUTH_KEY = "test_api_key"
BASE_API_URL = "https://api.example.com"
CONFIG_ENDPOINT = "/ssh-config"


@pytest.fixture
def mock_config():
    """Mock the config object."""
    with patch("infraninja.inventory.jinn.config") as mock:
        mock.ssh_config_endpoint = CONFIG_ENDPOINT
        yield mock


class TestFetchSSHConfigPytest:
    """Test suite for the fetch_ssh_config function using pytest style."""

    def test_successful_fetch(self, mock_config, monkeypatch):
        """Test fetch_ssh_config with a successful API response."""
        # Mock requests.get
        mock_response = Mock()
        mock_response.text = "Host example\n  HostName example.com"
        mock_response.raise_for_status = Mock()

        mock_get = Mock(return_value=mock_response)
        monkeypatch.setattr(requests, "get", mock_get)

        # Call the function
        result = fetch_ssh_config(API_AUTH_KEY, BASE_API_URL)

        # Verify
        mock_get.assert_called_once_with(
            f"{BASE_API_URL}{CONFIG_ENDPOINT}",
            headers={"Authentication": API_AUTH_KEY},
            params={"bastionless": True},
            timeout=10,
        )
        assert result == "Host example\n  HostName example.com"

    def test_http_error(self, mock_config, monkeypatch):
        """Test fetch_ssh_config when the API returns an HTTP error."""
        # Mock requests.get to raise an exception
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.HTTPError(
            "404 Client Error"
        )

        mock_get = Mock(return_value=mock_response)
        monkeypatch.setattr(requests, "get", mock_get)

        # Call the function and check exception
        with pytest.raises(RuntimeError) as excinfo:
            fetch_ssh_config(API_AUTH_KEY, BASE_API_URL)

        assert "Failed to fetch SSH config" in str(excinfo.value)

    def test_timeout_error(self, mock_config, monkeypatch):
        """Test fetch_ssh_config when the API request times out."""
        # Mock requests.get to raise a Timeout exception
        mock_get = Mock(side_effect=requests.Timeout("Request timed out"))
        monkeypatch.setattr(requests, "get", mock_get)

        # Call the function and check exception
        with pytest.raises(RuntimeError) as excinfo:
            fetch_ssh_config(API_AUTH_KEY, BASE_API_URL)

        assert "Failed to fetch SSH config" in str(excinfo.value)

    # Example of using the shared fixture from conftest.py
    def test_with_conftest_fixture(self, mock_config, mock_api_response, monkeypatch):
        """Test fetch_ssh_config using the shared fixture from conftest.py."""
        # Mock requests.get to return our fixture
        mock_get = Mock(return_value=mock_api_response)
        monkeypatch.setattr(requests, "get", mock_get)

        # Call the function
        result = fetch_ssh_config(API_AUTH_KEY, BASE_API_URL)

        # Verify
        assert "Host example" in result
        assert "HostName example.com" in result
        assert "User testuser" in result
