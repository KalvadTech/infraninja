import pytest
from unittest.mock import patch, MagicMock, call

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
        "expected_service": "ssh",
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
        "infraninja.security.common.ssh_hardening.systemd"
    ) as mock_systemd, patch(
        "infraninja.security.common.ssh_hardening.openrc"
    ) as mock_openrc, patch(
        "infraninja.security.common.ssh_hardening.runit"
    ) as mock_runit, patch(
        "infraninja.security.common.ssh_hardening.sysvinit"
    ) as mock_sysvinit, patch(
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

        # Mock the decorator to run the actual function without the decorator
        with patch(
            "pyinfra.api.deploy.deploy", lambda *args, **kwargs: lambda func: func
        ):
            # Create and run SSHHardener
            hardener = SSHHardener()
            hardener.deploy()

        # Verify the correct service operation was called based on init system
        expected_service = test_case["expected_service"]

        if test_case["init_system"] == "systemctl":
            assert mock_systemd.daemon_reload.called
            assert mock_systemd.service.called
            assert mock_systemd.service.call_args == call(
                name="Restart SSH",
                service=expected_service,
                running=True,
                restarted=True,
            )
        elif test_case["init_system"] == "rc-service":
            assert mock_openrc.service.called
            assert mock_openrc.service.call_args == call(
                name="Restart SSH",
                service=expected_service,
                running=True,
                restarted=True,
            )
        elif test_case["init_system"] == "sv":
            assert mock_runit.service.called
            assert mock_runit.service.call_args == call(
                service=expected_service,
                running=True,
                restarted=True,
            )
        elif test_case["init_system"] == "service":
            assert mock_sysvinit.service.called
            assert mock_sysvinit.service.call_args == call(
                name="Restart SSH with SysV init",
                service=expected_service,
                running=True,
                restarted=True,
            )
        elif test_case["init_system"] is None:
            assert mock_server.shell.called
            assert expected_service in mock_server.shell.call_args[1]["commands"][0]


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
    ) as mock_files, patch("infraninja.security.common.ssh_hardening.systemd"):
        # Setup host.get_fact for distribution and init system
        mock_host.get_fact.side_effect = lambda fact, **kwargs: (
            {"name": "Ubuntu"}
            if fact.__name__ == "LinuxDistribution"
            else True
            if fact.__name__ == "Which" and kwargs.get("command") == "systemctl"
            else []  # Empty list for FindInFile to force using line()
        )

        # Mock the decorator
        with patch(
            "pyinfra.api.deploy.deploy", lambda *args, **kwargs: lambda func: func
        ):
            # Create and run SSHHardener with custom config
            hardener = SSHHardener(ssh_config=custom_config)
            hardener.deploy()

        # Verify all custom config options were set
        assert mock_files.line.call_count == len(custom_config)
        for option, value in custom_config.items():
            # Check that files.line was called for each option
            found = False
            for call_args in mock_files.line.call_args_list:
                if call_args[1]["line"] == f"{option} {value}":
                    found = True
                    break
            assert found, f"Expected to find call for option: {option}"


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
        "infraninja.security.common.ssh_hardening.systemd"
    ) as mock_systemd:
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

        # Mock the decorator
        with patch(
            "pyinfra.api.deploy.deploy", lambda *args, **kwargs: lambda func: func
        ):
            # Create and run SSHHardener
            hardener = SSHHardener()
            hardener.deploy()

        # Verify that we checked the config
        assert mock_files.replace.call_count == 3  # One for each default option

        # Verify service restart wasn't attempted
        assert not mock_systemd.service.called
