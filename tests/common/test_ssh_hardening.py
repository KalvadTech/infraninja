from unittest.mock import MagicMock, patch

import pytest

from infraninja.security.common.ssh_hardening import SSHHardener

# Test cases for different init systems
INIT_SYSTEM_TEST_CASES = [
    {
        "name": "systemd",
        "init_system": "systemctl",
        "distro_info": {"name": "Fedora Linux"},
        "expected_service": "sshd",
    },
    {
        "name": "systemd_debian",
        "init_system": "systemctl",
        "distro_info": {"name": "Ubuntu"},
        "expected_service": "sshd",
    },
    {
        "name": "openrc",
        "init_system": "rc-service",
        "distro_info": {"name": "Alpine Linux"},
        "expected_service": "sshd",
    },
    {
        "name": "runit",
        "init_system": "sv",
        "distro_info": {"name": "Void Linux"},
        "expected_service": "sshd",
    },
    {
        "name": "sysvinit",
        "init_system": "service",
        "distro_info": {"name": "Slackware"},
        "expected_service": "sshd",
    },
    {
        "name": "fallback",
        "init_system": None,
        "distro_info": {"name": "Unknown"},
        "expected_service": "sshd",
    },
]


@pytest.mark.parametrize("test_case", INIT_SYSTEM_TEST_CASES)
def test_ssh_hardener_init_systems(test_case):
    """
    Test SSHHardener handling of different init systems.
    """

    # Configure mock behavior based on which init system is being tested
    def which_side_effect(fact, command, **kwargs):
        return (
            command == test_case["init_system"]
            if test_case["init_system"] is not None
            else False
        )

    # Create a mock for FindInFile fact to simulate existing config
    mock_find_in_file = MagicMock(return_value=["#PermitRootLogin yes"])

    # Setup mocks for all the functions we need
    with patch("pyinfra.context.state", MagicMock(config=MagicMock())), patch(
        "pyinfra.context.host", MagicMock()
    ), patch("infraninja.security.common.ssh_hardening.host") as mock_host, patch(
        "infraninja.security.common.ssh_hardening.files"
    ) as mock_files, patch(
        "infraninja.security.common.ssh_hardening.server"
    ) as mock_server:
        # Setup host.get_fact to return appropriate values
        mock_host.get_fact.side_effect = lambda fact, **kwargs: (
            test_case["distro_info"]
            if fact.__name__ == "LinuxDistribution"
            else which_side_effect(fact, **kwargs)
            if fact.__name__ == "Which"
            else mock_find_in_file()
        )

        # Configure files.replace to indicate a change
        replace_result = MagicMock()
        replace_result.changed = True
        mock_files.replace.return_value = replace_result

        # Create the hardener instance
        hardener = SSHHardener()

        # Patch the deploy decorator to make it a no-op and call the method
        with patch("pyinfra.api.deploy", lambda *args, **kwargs: lambda func: func):
            # This calls the function directly without decoration
            hardener.deploy()

        # Verify the server.service was called with the correct service name
        expected_service = test_case["expected_service"]
        assert mock_server.service.called
        assert mock_server.service.call_args[1]["service"] == expected_service
        assert mock_server.service.call_args[1]["running"] is True
        assert mock_server.service.call_args[1]["restarted"] is True


def test_ssh_hardener_custom_config():
    """
    Test SSHHardener with custom SSH configuration.
    """
    custom_config = {
        "PermitRootLogin": "no",
        "PasswordAuthentication": "no",
        "X11Forwarding": "no",
        "PermitEmptyPasswords": "no",
        "MaxAuthTries": "3",
    }

    # Create mocks for the functions we need
    with patch("pyinfra.context.state", MagicMock(config=MagicMock())), patch(
        "pyinfra.context.host", MagicMock()
    ), patch("infraninja.security.common.ssh_hardening.host") as mock_host, patch(
        "infraninja.security.common.ssh_hardening.files"
    ) as mock_files, patch(
        "infraninja.security.common.ssh_hardening.server"
    ) as mock_server:
        # Setup host.get_fact for distribution and init system
        mock_host.get_fact.side_effect = lambda fact, **kwargs: (
            {"name": "Ubuntu"}
            if fact.__name__ == "LinuxDistribution"
            else True
            if fact.__name__ == "Which" and kwargs.get("command") == "systemctl"
            else []  # Empty list for FindInFile to force append
        )

        # Mock server.shell to simulate .changed attribute
        shell_result = MagicMock()
        shell_result.changed = True
        mock_server.shell.return_value = shell_result

        # Create the hardener with custom config
        hardener = SSHHardener(ssh_config=custom_config)

        # Patch the deploy decorator to make it a no-op and call the method
        with patch("pyinfra.api.deploy", lambda *args, **kwargs: lambda func: func):
            # This calls the function directly without decoration
            hardener.deploy()

        # Verify all custom config options were set using server.shell (append)
        assert mock_server.shell.call_count == len(custom_config)


def test_ssh_hardener_no_changes():
    """
    Test SSHHardener when no config changes are needed.
    """
    # Create mocks for the functions we need
    with patch("pyinfra.context.state", MagicMock(config=MagicMock())), patch(
        "pyinfra.context.host", MagicMock()
    ), patch("infraninja.security.common.ssh_hardening.host") as mock_host, patch(
        "infraninja.security.common.ssh_hardening.files"
    ) as mock_files, patch(
        "infraninja.security.common.ssh_hardening.server"
    ) as mock_server:
        # Setup host.get_fact for existing options matching what we want
        def get_fact_side_effect(fact, **kwargs):
            if fact.__name__ == "LinuxDistribution":
                return {"name": "Ubuntu"}
            elif fact.__name__ == "Which" and kwargs.get("command") == "systemctl":
                return True
            elif fact.__name__ == "FindInFile":
                # Return the existing config lines that match what we want (so no changes needed)
                pattern = kwargs.get("pattern", "")
                # Extract the option name from the regex pattern
                if "PermitRootLogin" in pattern:
                    return ["PermitRootLogin prohibit-password"]
                elif "PasswordAuthentication" in pattern:
                    return ["PasswordAuthentication no"]
                elif "X11Forwarding" in pattern:
                    return ["X11Forwarding no"]
                return []
            return []

        mock_host.get_fact.side_effect = get_fact_side_effect

        # Configure files.replace to indicate no changes
        replace_result = MagicMock()
        replace_result.changed = False
        mock_files.replace.return_value = replace_result

        # Create the hardener instance
        hardener = SSHHardener()

        # Patch the deploy decorator to make it a no-op and call the method
        with patch("pyinfra.api.deploy", lambda *args, **kwargs: lambda func: func):
            # This calls the function directly without decoration
            hardener.deploy()

        # Since all options are already set correctly, files.replace should not be called
        assert mock_files.replace.call_count == 0
        # Verify service restart wasn't attempted
        assert not mock_server.service.called
