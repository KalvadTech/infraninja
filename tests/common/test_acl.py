# filepath: /home/xoity/Desktop/work/infraninja/tests/common/test_acl.py
from unittest.mock import patch, MagicMock, call

from infraninja.security.common.acl import acl_setup


def test_acl_setup_setfacl_exists():
    """
    Test ACL setup when setfacl command exists.
    """
    # Setup mocks for all the functions we need
    with patch("pyinfra.context.state", MagicMock(config=MagicMock())), patch(
        "pyinfra.context.host", MagicMock()
    ), patch("infraninja.security.common.acl.host") as mock_host, patch(
        "infraninja.security.common.acl.server"
    ) as mock_server:
        # Mock setfacl exists check to return True
        setfacl_check = MagicMock()
        setfacl_check.return_value = True
        mock_server.shell.side_effect = [setfacl_check]

        # Mock server.shell for setfacl operations to return success
        mock_server.shell.return_value = True

        # Mock File fact to return that all paths exist
        mock_host.get_fact.return_value = {}  # Any non-None value to indicate file exists
        mock_host.noop = MagicMock()

        # Mock the decorator to run the actual function without the decorator
        with patch(
            "pyinfra.api.deploy.deploy", lambda *args, **kwargs: lambda func: func
        ):
            # Call the acl_setup function
            result = acl_setup()

        # Verify the result is True
        assert result is True

        # Verify setfacl check was called
        assert mock_server.shell.call_args_list[0] == call(
            name="Check if setfacl exists",
            commands=["command -v setfacl"],
            _ignore_errors=True,
        )

        # Verify calls to set ACLs
        # The first call was to check if setfacl exists
        # Each path in ACL_PATHS should have a corresponding setfacl call
        acl_calls = mock_server.shell.call_args_list[1:]
        assert len(acl_calls) > 0  # Ensure we have at least one ACL call

        # Example verification for a specific path
        etc_ssh_call_found = False
        for call_args in acl_calls:
            if "/etc/ssh/sshd_config" in call_args[1]["commands"][0]:
                etc_ssh_call_found = True
                break
        assert etc_ssh_call_found, "Expected to find call for /etc/ssh/sshd_config"


def test_acl_setup_setfacl_missing():
    """
    Test ACL setup when setfacl command is not available.
    """
    # Setup mocks for all the functions we need
    with patch("pyinfra.context.state", MagicMock(config=MagicMock())), patch(
        "pyinfra.context.host", MagicMock()
    ), patch("infraninja.security.common.acl.host") as mock_host, patch(
        "infraninja.security.common.acl.server"
    ) as mock_server:
        # Mock setfacl exists check to return False
        mock_server.shell.return_value = False

        # Mock host.noop for skipping ACL setup
        mock_host.noop = MagicMock()

        # Mock the decorator
        with patch(
            "pyinfra.api.deploy.deploy", lambda *args, **kwargs: lambda func: func
        ):
            # Call the acl_setup function
            result = acl_setup()

        # Verify function returns early
        assert result is None

        # Verify that host.noop was called to skip ACL setup
        mock_host.noop.assert_called_once_with(
            "Skip ACL setup - setfacl not available and could not be installed"
        )

        # There should be at most 2 calls to server.shell:
        # 1. Check if setfacl exists
        # 2. Try to verify setfacl exists after installation attempt
        assert mock_server.shell.call_count <= 2


def test_acl_setup_missing_paths():
    """
    Test ACL setup with some paths missing.
    """
    # Setup mocks for all the functions we need
    with patch("pyinfra.context.state", MagicMock(config=MagicMock())), patch(
        "pyinfra.context.host", MagicMock()
    ), patch("infraninja.security.common.acl.host") as mock_host, patch(
        "infraninja.security.common.acl.server"
    ) as mock_server:
        # Mock setfacl exists check to return True
        setfacl_check = MagicMock()
        setfacl_check.return_value = True
        mock_server.shell.side_effect = [setfacl_check] + [
            True
        ] * 50  # Allow multiple shell calls

        # Define paths that exist and don't exist
        def get_fact_side_effect(_fact, **kwargs):
            path = kwargs.get("path")
            if path in ["/etc/fail2ban", "/etc/ssh/sshd_config"]:
                return {}  # Path exists
            return None  # Path does not exist

        mock_host.get_fact.side_effect = get_fact_side_effect
        mock_host.noop = MagicMock()

        # Mock the decorator
        with patch(
            "pyinfra.api.deploy.deploy", lambda *args, **kwargs: lambda func: func
        ):
            # Call the acl_setup function
            result = acl_setup()

        # Verify the result is True
        assert result is True

        # Verify host.noop was called for skipping non-existent paths
        assert mock_host.noop.call_count > 0

        # Verify setfacl was only called for existing paths
        setfacl_calls = 0
        for call_args in mock_server.shell.call_args_list[
            1:
        ]:  # Skip the first check call
            if "setfacl" in call_args[1]["commands"][0]:
                setfacl_calls += 1
                # Make sure it's for an existing path
                assert any(
                    path in call_args[1]["commands"][0]
                    for path in ["/etc/fail2ban", "/etc/ssh/sshd_config"]
                )

        # We should have at least one setfacl call for each existing path
        assert setfacl_calls >= 2


def test_acl_setup_with_exceptions():
    """
    Test ACL setup when setfacl operations throw exceptions.
    """
    # Setup mocks for all the functions we need
    with patch("pyinfra.context.state", MagicMock(config=MagicMock())), patch(
        "pyinfra.context.host", MagicMock()
    ), patch("infraninja.security.common.acl.host") as mock_host, patch(
        "infraninja.security.common.acl.server"
    ) as mock_server:
        # Mock setfacl exists check to return True
        setfacl_check = MagicMock()
        setfacl_check.return_value = True

        # Make other server.shell calls raise an exception
        def shell_side_effect(*args, **kwargs):
            if "Check if setfacl exists" in kwargs.get("name", ""):
                return True
            raise Exception("setfacl error")

        mock_server.shell.side_effect = shell_side_effect

        # Mock File fact to return that all paths exist
        mock_host.get_fact.return_value = {}  # Any non-None value
        mock_host.noop = MagicMock()

        # Mock the decorator
        with patch(
            "pyinfra.api.deploy.deploy", lambda *args, **kwargs: lambda func: func
        ):
            # Call the acl_setup function
            result = acl_setup()

        # Verify the result is True (function continues despite exceptions)
        assert result is True

        # Verify host.noop was called for each exception
        assert mock_host.noop.call_count > 0
        for call_args in mock_host.noop.call_args_list:
            assert "Failed to set ACL for" in call_args[0][0]
