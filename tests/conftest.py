#!/usr/bin/env python3
# tests/conftest.py

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))


# You can add fixtures here that will be available to all test files
@pytest.fixture
def mock_ssh_config():
    """Return a sample SSH config for testing."""
    return """
Host example
    HostName example.com
    User testuser
    IdentityFile ~/.ssh/id_rsa
    Port 22
"""


@pytest.fixture
def mock_api_response(mock_ssh_config):
    """Return a mock API response with the SSH config."""

    class MockResponse:
        def __init__(self, text, status_code):
            self.text = text
            self.status_code = status_code

        def raise_for_status(self):
            if self.status_code >= 400:
                from requests.exceptions import HTTPError

                raise HTTPError(f"{self.status_code} Error")

    return MockResponse(mock_ssh_config, 200)


@pytest.fixture
def sample_server_data():
    """Return sample server data for testing."""
    return {
        "result": [
            {
                "hostname": "server1",
                "ssh_user": "admin",
                "is_active": True,
                "group": {
                    "name_en": "production",
                    "project": {"name_en": "test_project"},
                },
                "tags": ["web", "api"],
                "attributes": {"location": "eu-west", "role": "webserver"},
            },
            {
                "hostname": "server2",
                "ssh_user": "admin",
                "is_active": True,
                "group": {"name_en": "staging", "project": {"name_en": "test_project"}},
                "tags": ["db", "backup"],
                "attributes": {"location": "us-east", "role": "database"},
            },
            {
                "hostname": "server3",
                "ssh_user": "admin",
                "is_active": False,
                "group": {
                    "name_en": "production",
                    "project": {"name_en": "test_project"},
                },
                "tags": ["inactive"],
                "attributes": {"location": "us-west", "role": "deprecated"},
            },
        ]
    }


@pytest.fixture
def mock_config():
    """Return a mock NinjaConfig instance."""
    mock = Mock()
    mock.ssh_config_endpoint = "/ssh-config"
    mock.inventory_endpoint = "/inventory"
    mock.ssh_config_dir = "/home/user/.ssh/configs"
    mock.main_ssh_config = "/home/user/.ssh/config"
    mock.default_ssh_config_filename = "default_ssh_config"
    mock.ssh_key_path = "/home/user/.ssh/id_rsa"
    return mock


@pytest.fixture
def temp_ssh_dir(tmp_path):
    """Create a temporary .ssh directory with some mock key files."""
    ssh_dir = tmp_path / ".ssh"
    ssh_dir.mkdir()

    # Create mock SSH key files
    (ssh_dir / "id_rsa").write_text("mock private key")
    (ssh_dir / "id_rsa.pub").write_text("mock public key")
    (ssh_dir / "id_ed25519").write_text("mock ed25519 key")
    (ssh_dir / "config").write_text("# SSH config file")
    (ssh_dir / "known_hosts").write_text("known hosts content")

    return ssh_dir
