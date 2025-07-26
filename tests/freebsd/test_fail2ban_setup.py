from unittest.mock import MagicMock, patch

import pytest

from infraninja.security.freebsd.fail2ban_setup import fail2ban_setup


def test_fail2ban_setup_success():
    """
    Test fail2ban_setup function with successful execution.
    """
    with patch("pyinfra.context.state", MagicMock(config=MagicMock())), patch(
        "pyinfra.context.host", MagicMock()
    ), patch("infraninja.security.freebsd.fail2ban_setup.host") as mock_host, patch(
        "infraninja.security.freebsd.fail2ban_setup.files"
    ) as mock_files, patch(
        "infraninja.security.freebsd.fail2ban_setup.service"
    ) as mock_service:
        # Configure host.get_fact to return FreeBSD distro info
        mock_host.get_fact.return_value = {
            "name": "FreeBSD",
            "release_meta": {"ID": "freebsd"},
        }

        # Mock the decorator
        with patch(
            "pyinfra.api.deploy.deploy", lambda *args, **kwargs: lambda func: func
        ):
            # Run the fail2ban_setup function
            result = fail2ban_setup()

        # Verify configuration directory was created
        mock_files.directory.assert_any_call(
            name="Create fail2ban configuration directory",
            path="/usr/local/etc/fail2ban",
            present=True,
        )

        # Verify fail2ban was enabled in rc.conf
        mock_files.line.assert_any_call(
            name="Enable fail2ban in rc.conf",
            path="/etc/rc.conf",
            line='fail2ban_enable="YES"',
            present=True,
        )

        # Verify service was restarted
        mock_service.service.assert_called_once_with(
            name="Restart fail2ban service",
            srvname="fail2ban",
            srvstate="restarted",
        )

        # Verify result
        assert result is True


def test_fail2ban_setup_non_freebsd():
    """
    Test fail2ban_setup function raises error on non-FreeBSD systems.
    """
    with patch("pyinfra.context.state", MagicMock(config=MagicMock())), patch(
        "pyinfra.context.host", MagicMock()
    ), patch("infraninja.security.freebsd.fail2ban_setup.host") as mock_host:
        # Configure host.get_fact to return a non-FreeBSD distro
        mock_host.get_fact.return_value = {
            "name": "Ubuntu",
            "release_meta": {"ID": "ubuntu"},
        }

        # Mock the decorator
        with patch(
            "pyinfra.api.deploy.deploy", lambda *args, **kwargs: lambda func: func
        ):
            # Verify fail2ban_setup raises ValueError for non-FreeBSD OS
            with pytest.raises(ValueError) as exc_info:
                fail2ban_setup()

            assert "This deployment is designed for FreeBSD systems only" in str(
                exc_info.value
            )


def test_fail2ban_pf_integration():
    """
    Test fail2ban_setup integrates with PF properly.
    """
    with patch("pyinfra.context.state", MagicMock(config=MagicMock())), patch(
        "pyinfra.context.host", MagicMock()
    ), patch("infraninja.security.freebsd.fail2ban_setup.host") as mock_host, patch(
        "infraninja.security.freebsd.fail2ban_setup.files"
    ) as mock_files, patch("infraninja.security.freebsd.fail2ban_setup.service"):
        # Configure host.get_fact to return FreeBSD distro info
        mock_host.get_fact.return_value = {
            "name": "FreeBSD",
            "release_meta": {"ID": "freebsd"},
        }

        # Mock the decorator
        with patch(
            "pyinfra.api.deploy.deploy", lambda *args, **kwargs: lambda func: func
        ):
            # Run the fail2ban_setup function
            fail2ban_setup()

        # Verify PF action template was used
        template_calls = [
            call
            for call in mock_files.template.call_args_list
            if "pf_action" in str(call)
        ]

        assert len(template_calls) > 0, "PF action template should have been used"

        # Verify jail.local template was used
        jail_template_calls = [
            call
            for call in mock_files.template.call_args_list
            if "jail.local" in str(call)
        ]

        assert len(jail_template_calls) > 0, "Jail.local template should have been used"
