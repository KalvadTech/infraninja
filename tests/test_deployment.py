"""
Tests for deployment operations and service management.
"""

import pytest
from unittest.mock import patch, MagicMock
import warnings

# Import with warning suppression for pyinfra deprecation warnings
with warnings.catch_warnings():
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    from pyinfra.api import State, Config
    from infraninja.netdata import deploy_netdata


@pytest.fixture
def mock_state():
    """
    Creates a mock pyinfra state for testing.
    """
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=ResourceWarning)
        config = Config()
        state = State(config)
        return state


@pytest.fixture
def mock_files():
    """
    Mock for pyinfra files operations.
    """
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=DeprecationWarning)
        with patch("infraninja.netdata.files") as mock:
            yield mock


@pytest.fixture
def mock_server():
    """
    Mock for pyinfra server operations.
    """
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=DeprecationWarning)
        with patch("infraninja.netdata.server") as mock:
            yield mock


def test_installation_script_download(mock_state, mock_files):
    """Test that the installation script is downloaded correctly"""
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=ResourceWarning)
        deploy_netdata(mock_state)

    mock_files.download.assert_called_once_with(
        name="Download the installation script",
        src="https://my-netdata.io/kickstart.sh",
        dest="~/kickstart.sh",
        mode="+x",
    )


def test_netdata_installation(mock_state, mock_server):
    """Test that Netdata is installed correctly"""
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=ResourceWarning)
        deploy_netdata(mock_state)

    mock_server.shell.assert_called_once_with(
        name="Install Netdata",
        commands=["~/kickstart.sh --dont-wait"],
    )


def test_cleanup_after_installation(mock_state, mock_files):
    """Test that installation script is cleaned up after installation"""
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=ResourceWarning)
        deploy_netdata(mock_state)

    mock_files.file.assert_called_with(
        name="Cleanup installation script",
        path="~/kickstart.sh",
        present=False,
    )


def test_config_template_deployment(mock_state, mock_files):
    """Test that the configuration template is deployed correctly"""
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=ResourceWarning)
        deploy_netdata(mock_state)

    mock_files.template.assert_called_once()
    call_kwargs = mock_files.template.call_args[1]
    assert call_kwargs["dest"] == "/etc/netdata/netdata.conf", (
        "Wrong config destination"
    )
    assert call_kwargs["user"] == "root", "Wrong config file owner"
    assert call_kwargs["group"] == "root", "Wrong config file group"
    assert call_kwargs["mode"] == "644", "Wrong config file permissions"


@pytest.mark.parametrize("config_changed", [True, False])
def test_service_restart_condition(mock_state, mock_server, config_changed):
    """Test that service restart happens only when config changes"""
    # Mock the template result
    mock_result = MagicMock()
    mock_result.changed = config_changed

    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=ResourceWarning)
        with patch("infraninja.netdata.files.template", return_value=mock_result):
            deploy_netdata(mock_state)

            mock_server.service.assert_called_once_with(
                name="Restart Netdata",
                service="netdata",
                running=True,
                restarted=True,
                enabled=True,
                _if=config_changed,
            )
