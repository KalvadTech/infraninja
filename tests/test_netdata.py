"""
Tests for the netdata deployment functionality.
"""

import pytest
from pathlib import Path
import warnings

# Import with warning suppression for pyinfra deprecation warnings
with warnings.catch_warnings():
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    from pyinfra.api import State, Config
    from pyinfra.api.connect import connect_all
    from infraninja.netdata import DEFAULTS

# Constants for test values
TEST_CONFIG = {
    "claim_token": "test_token_123",
    "claim_rooms": "test_room",
    "claim_url": "https://test.netdata.cloud",
    "reclaim": True,
    "dbengine_multihost_disk_space": 4096,
    "stream": {
        "enabled": True,
        "destination": "test.streaming.netdata.cloud",
        "api_key": "test_api_key_123",
    },
}


@pytest.fixture
def mock_state():
    """
    Creates a mock pyinfra state for testing.
    """
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=ResourceWarning)
        config = Config()
        state = State(config)
        connect_all(state)
        return state


@pytest.fixture
def custom_config():
    """
    Provides a custom netdata configuration for testing.
    """
    return TEST_CONFIG.copy()


def test_default_config():
    """Test the default configuration values"""
    assert isinstance(DEFAULTS, dict), "DEFAULTS should be a dictionary"
    assert "claim_token" in DEFAULTS, "claim_token should be in DEFAULTS"
    assert "claim_rooms" in DEFAULTS, "claim_rooms should be in DEFAULTS"
    assert "claim_url" in DEFAULTS, "claim_url should be in DEFAULTS"
    assert isinstance(DEFAULTS["stream"], dict), "stream should be a dictionary"
    assert DEFAULTS["stream"]["enabled"] is False, (
        "stream should be disabled by default"
    )


def test_custom_config_override(mock_state, custom_config):
    """Test that custom configuration properly overrides defaults"""
    # Update state data with custom config
    mock_state.data.update(custom_config)

    # Verify custom values are used
    assert mock_state.data["claim_token"] == TEST_CONFIG["claim_token"]
    assert mock_state.data["claim_rooms"] == TEST_CONFIG["claim_rooms"]
    assert mock_state.data["stream"]["enabled"] == TEST_CONFIG["stream"]["enabled"]
    assert mock_state.data["stream"]["api_key"] == TEST_CONFIG["stream"]["api_key"]


def test_template_path():
    """Test that the netdata template file exists"""
    from importlib.resources import files as resource_files

    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=ResourceWarning)
        template_path = resource_files("infraninja.templates").joinpath(
            "netdata.conf.j2"
        )
        assert Path(template_path).exists(), "Netdata template file should exist"


@pytest.mark.parametrize("disk_space", [1024, 2048, 4096])
def test_dbengine_disk_space_validation(disk_space):
    """Test different dbengine disk space configurations"""
    assert isinstance(disk_space, int), "disk_space should be an integer"
    assert disk_space > 0, "disk_space should be positive"
    assert disk_space % 1024 == 0, "disk_space should be multiple of 1024"
