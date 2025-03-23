#!/usr/bin/env python3
# tests/conftest.py

import pytest
import sys
from pathlib import Path

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