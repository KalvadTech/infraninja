"""
This file contains pytest fixtures that can be shared across all test files.
Fixtures defined here are automatically available to all test files.
"""

import pytest
import os
import sys

# Add the project root directory to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


@pytest.fixture
def sample_config():
    """
    A fixture that provides a sample configuration for testing.
    """
    return {
        "host": "example.com",
        "port": 22,
        "username": "test_user",
        "password": "test_password",
    }


@pytest.fixture
def temp_directory(tmp_path):
    """
    A fixture that provides a temporary directory for testing file operations.
    """
    return tmp_path
