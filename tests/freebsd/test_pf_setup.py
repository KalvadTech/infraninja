from unittest.mock import MagicMock, patch

import pytest

from infraninja.security.freebsd.pf_setup import pf_setup


def test_pf_setup_success():
    """
    Test pf_setup function with successful execution.
    """
    with patch("pyinfra.context.state", MagicMock(config=MagicMock())), patch(
        "pyinfra.context.host", MagicMock()
    ), patch("infraninja.security.freebsd.pf_setup.host") as mock_host, patch(
        "infraninja.security.freebsd.pf_setup.files"
    ), patch("infraninja.security.freebsd.pf_setup.server") as mock_server, patch(
        "infraninja.security.freebsd.pf_setup.service"
    ) as mock_service:
        # Configure host.get_fact to return FreeBSD distro info
        mock_host.get_fact.side_effect = lambda fact, **kwargs: (
            {"name": "FreeBSD", "release_meta": {"ID": "freebsd"}}
            if fact.__name__ == "LinuxDistribution"
            else "kldstat output"
        )

        # Mock the decorator
        with patch(
            "pyinfra.api.deploy.deploy", lambda *args, **kwargs: lambda func: func
        ):
            # Run the pf_setup function
            result = pf_setup()

        # Verify essential operations were called
        assert mock_server.shell.called
        assert mock_service.service.called

        # Verify result
        assert result is True


def test_pf_setup_non_freebsd():
    """
    Test pf_setup function raises error on non-FreeBSD systems.
    """
    with patch("pyinfra.context.state", MagicMock(config=MagicMock())), patch(
        "pyinfra.context.host", MagicMock()
    ), patch("infraninja.security.freebsd.pf_setup.host") as mock_host:
        # Configure host.get_fact to return a non-FreeBSD distro
        mock_host.get_fact.return_value = {
            "name": "Ubuntu",
            "release_meta": {"ID": "ubuntu"},
        }

        # Mock the decorator
        with patch(
            "pyinfra.api.deploy.deploy", lambda *args, **kwargs: lambda func: func
        ):
            # Verify pf_setup raises ValueError for non-FreeBSD OS
            with pytest.raises(ValueError) as exc_info:
                pf_setup()

            assert "This deployment is designed for FreeBSD systems only" in str(
                exc_info.value
            )


def test_pf_setup_module_not_loaded():
    """
    Test pf_setup function loads PF module when not loaded.
    """
    with patch("pyinfra.context.state", MagicMock(config=MagicMock())), patch(
        "pyinfra.context.host", MagicMock()
    ), patch("infraninja.security.freebsd.pf_setup.host") as mock_host, patch(
        "infraninja.security.freebsd.pf_setup.server"
    ) as mock_server, patch("infraninja.security.freebsd.pf_setup.files"), patch(
        "infraninja.security.freebsd.pf_setup.service"
    ):
        # Configure host.get_fact to return FreeBSD and PF not loaded
        mock_host.get_fact.side_effect = lambda fact, command=None, **kwargs: (
            {"name": "FreeBSD", "release_meta": {"ID": "freebsd"}}
            if fact.__name__ == "LinuxDistribution"
            else "not_loaded"
        )

        # Mock the decorator
        with patch(
            "pyinfra.api.deploy.deploy", lambda *args, **kwargs: lambda func: func
        ):
            # Run the pf_setup function
            pf_setup()

        # Verify kldload was called to load PF module
        mock_server.shell.assert_any_call(
            name="Load PF kernel module",
            commands="kldload pf",
        )
