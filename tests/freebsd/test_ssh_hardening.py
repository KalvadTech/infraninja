from unittest.mock import MagicMock, patch

import pytest

from infraninja.security.freebsd.ssh_hardening import SSHHardener


def test_freebsd_ssh_hardener_default_config():
    """
    Test SSHHardener with default SSH configuration.
    """
    with patch("pyinfra.context.state", MagicMock(config=MagicMock())), patch(
        "pyinfra.context.host", MagicMock()
    ), patch("infraninja.security.freebsd.ssh_hardening.host") as mock_host, patch(
        "infraninja.security.freebsd.ssh_hardening.server"
    ) as mock_server, patch(
        "infraninja.security.freebsd.ssh_hardening.service"
    ) as mock_service:
        # Configure mock_host.get_fact to return empty results (options don't exist)
        mock_host.get_fact.return_value = []

        # Configure server.shell to indicate changes were made
        shell_result = MagicMock()
        shell_result.changed = True
        mock_server.shell.return_value = shell_result

        # Create SSH hardener with default config
        hardener = SSHHardener()

        # Mock the deploy decorator
        with patch("pyinfra.api.deploy", lambda *args, **kwargs: lambda func: func):
            hardener.deploy()

        # Verify server.shell was called for each default config option
        expected_options = [
            "PermitRootLogin",
            "PasswordAuthentication",
            "X11Forwarding",
        ]
        assert mock_server.shell.call_count == len(expected_options)

        # Verify the service was restarted since config changed
        mock_service.service.assert_called_once_with(
            name="Restart SSH service",
            srvname="sshd",
            srvstate="restarted",
            _ignore_errors=True,
        )

        # Verify host.noop was called to indicate service restart
        mock_host.noop.assert_called_with(
            "SSH configuration updated and service restarted."
        )


def test_freebsd_ssh_hardener_custom_config():
    """
    Test SSHHardener with custom SSH configuration.
    """
    custom_config = {
        "PermitRootLogin": "no",
        "PasswordAuthentication": "no",
        "X11Forwarding": "no",
        "PermitEmptyPasswords": "no",
        "MaxAuthTries": "3",
        "Protocol": "2",
    }

    with patch("pyinfra.context.state", MagicMock(config=MagicMock())), patch(
        "pyinfra.context.host", MagicMock()
    ), patch("infraninja.security.freebsd.ssh_hardening.host") as mock_host, patch(
        "infraninja.security.freebsd.ssh_hardening.server"
    ) as mock_server, patch(
        "infraninja.security.freebsd.ssh_hardening.service"
    ) as mock_service:
        # Configure mock_host.get_fact to return empty results (options don't exist)
        mock_host.get_fact.return_value = []

        # Configure server.shell to indicate changes were made
        shell_result = MagicMock()
        shell_result.changed = True
        mock_server.shell.return_value = shell_result

        # Create SSH hardener with custom config
        hardener = SSHHardener(ssh_config=custom_config)

        # Mock the deploy decorator
        with patch("pyinfra.api.deploy", lambda *args, **kwargs: lambda func: func):
            hardener.deploy()

        # Verify server.shell was called for each custom config option
        assert mock_server.shell.call_count == len(custom_config)

        # Verify each option was appended correctly
        shell_calls = [
            call[1]["commands"][0] for call in mock_server.shell.call_args_list
        ]
        for option, value in custom_config.items():
            expected_command = f"echo '{option} {value}' >> /etc/ssh/sshd_config"
            assert expected_command in shell_calls

        # Verify the service was restarted
        mock_service.service.assert_called_once()


def test_freebsd_ssh_hardener_existing_config_correct():
    """
    Test SSHHardener when existing config already has correct values.
    """
    with patch("pyinfra.context.state", MagicMock(config=MagicMock())), patch(
        "pyinfra.context.host", MagicMock()
    ), patch("infraninja.security.freebsd.ssh_hardening.host") as mock_host, patch(
        "infraninja.security.freebsd.ssh_hardening.server"
    ) as mock_server, patch(
        "infraninja.security.freebsd.ssh_hardening.files"
    ) as mock_files, patch(
        "infraninja.security.freebsd.ssh_hardening.service"
    ) as mock_service:
        # Configure mock_host.get_fact to return existing correct config
        def get_fact_side_effect(fact_class, **kwargs):
            pattern = kwargs.get("pattern", "")
            if "PermitRootLogin" in pattern:
                return ["PermitRootLogin prohibit-password"]
            elif "PasswordAuthentication" in pattern:
                return ["PasswordAuthentication no"]
            elif "X11Forwarding" in pattern:
                return ["X11Forwarding no"]
            return []

        mock_host.get_fact.side_effect = get_fact_side_effect

        # Create SSH hardener with default config
        hardener = SSHHardener()

        # Mock the deploy decorator
        with patch("pyinfra.api.deploy", lambda *args, **kwargs: lambda func: func):
            hardener.deploy()

        # Verify no changes were made (no server.shell or files.replace calls)
        assert mock_server.shell.call_count == 0
        assert mock_files.replace.call_count == 0

        # Verify the service was NOT restarted since no changes were made
        assert mock_service.service.call_count == 0


def test_freebsd_ssh_hardener_existing_config_incorrect():
    """
    Test SSHHardener when existing config has incorrect values that need updating.
    """
    with patch("pyinfra.context.state", MagicMock(config=MagicMock())), patch(
        "pyinfra.context.host", MagicMock()
    ), patch("infraninja.security.freebsd.ssh_hardening.host") as mock_host, patch(
        "infraninja.security.freebsd.ssh_hardening.files"
    ) as mock_files, patch(
        "infraninja.security.freebsd.ssh_hardening.service"
    ) as mock_service:
        # Configure mock_host.get_fact to return existing incorrect config
        def get_fact_side_effect(fact_class, **kwargs):
            pattern = kwargs.get("pattern", "")
            if "PermitRootLogin" in pattern:
                return ["PermitRootLogin yes"]  # Incorrect value
            elif "PasswordAuthentication" in pattern:
                return ["PasswordAuthentication yes"]  # Incorrect value
            elif "X11Forwarding" in pattern:
                return ["X11Forwarding yes"]  # Incorrect value
            return []

        mock_host.get_fact.side_effect = get_fact_side_effect

        # Configure files.replace to indicate changes were made
        replace_result = MagicMock()
        replace_result.changed = True
        mock_files.replace.return_value = replace_result

        # Create SSH hardener with default config
        hardener = SSHHardener()

        # Mock the deploy decorator
        with patch("pyinfra.api.deploy", lambda *args, **kwargs: lambda func: func):
            hardener.deploy()

        # Verify files.replace was called for each incorrect option
        expected_options = [
            "PermitRootLogin",
            "PasswordAuthentication",
            "X11Forwarding",
        ]
        assert mock_files.replace.call_count == len(expected_options)

        # Verify the service was restarted since config changed
        mock_service.service.assert_called_once_with(
            name="Restart SSH service",
            srvname="sshd",
            srvstate="restarted",
            _ignore_errors=True,
        )


def test_freebsd_ssh_hardener_mixed_config_scenarios():
    """
    Test SSHHardener with mixed scenarios: some options exist and correct,
    some exist and incorrect, some don't exist.
    """
    with patch("pyinfra.context.state", MagicMock(config=MagicMock())), patch(
        "pyinfra.context.host", MagicMock()
    ), patch("infraninja.security.freebsd.ssh_hardening.host") as mock_host, patch(
        "infraninja.security.freebsd.ssh_hardening.files"
    ) as mock_files, patch(
        "infraninja.security.freebsd.ssh_hardening.server"
    ) as mock_server, patch(
        "infraninja.security.freebsd.ssh_hardening.service"
    ) as mock_service:
        # Configure mock_host.get_fact for mixed scenarios
        def get_fact_side_effect(fact_class, **kwargs):
            pattern = kwargs.get("pattern", "")
            if "PermitRootLogin" in pattern:
                return ["PermitRootLogin prohibit-password"]  # Correct
            elif "PasswordAuthentication" in pattern:
                return ["PasswordAuthentication yes"]  # Incorrect
            elif "X11Forwarding" in pattern:
                return []  # Doesn't exist
            return []

        mock_host.get_fact.side_effect = get_fact_side_effect

        # Configure mock returns
        replace_result = MagicMock()
        replace_result.changed = True
        mock_files.replace.return_value = replace_result

        shell_result = MagicMock()
        shell_result.changed = True
        mock_server.shell.return_value = shell_result

        # Create SSH hardener with default config
        hardener = SSHHardener()

        # Mock the deploy decorator
        with patch("pyinfra.api.deploy", lambda *args, **kwargs: lambda func: func):
            hardener.deploy()

        # Verify files.replace was called once (for PasswordAuthentication)
        assert mock_files.replace.call_count == 1

        # Verify server.shell was called once (for X11Forwarding)
        assert mock_server.shell.call_count == 1

        # Verify the service was restarted since some config changed
        mock_service.service.assert_called_once()


def test_freebsd_ssh_hardener_default_config_values():
    """
    Test that the default SSH configuration contains expected values.
    """
    expected_default_config = {
        "PermitRootLogin": "prohibit-password",
        "PasswordAuthentication": "no",
        "X11Forwarding": "no",
    }

    # Verify the default config matches expectations
    assert SSHHardener.DEFAULT_SSH_CONFIG == expected_default_config


def test_freebsd_ssh_hardener_config_independence():
    """
    Test that modifying config in one instance doesn't affect another.
    """
    # Create first instance and modify its config
    hardener1 = SSHHardener()
    original_config = hardener1.ssh_config.copy()
    hardener1.ssh_config["CustomOption"] = "test_value"

    # Create second instance
    hardener2 = SSHHardener()

    # Verify second instance has unmodified default config
    assert hardener2.ssh_config == original_config
    assert "CustomOption" not in hardener2.ssh_config


def test_freebsd_ssh_hardener_init_with_none():
    """
    Test SSHHardener initialization with None config (should use default).
    """
    hardener = SSHHardener(ssh_config=None)
    assert hardener.ssh_config == SSHHardener.DEFAULT_SSH_CONFIG.copy()


def test_freebsd_ssh_hardener_init_with_empty_dict():
    """
    Test SSHHardener initialization with empty dictionary.
    """
    hardener = SSHHardener(ssh_config={})
    assert hardener.ssh_config == {}


@pytest.mark.parametrize(
    "existing_line,desired_value,should_change",
    [
        ("PermitRootLogin yes", "prohibit-password", True),
        ("PermitRootLogin no", "prohibit-password", True),
        ("PermitRootLogin prohibit-password", "prohibit-password", False),
        ("#PermitRootLogin yes", "prohibit-password", True),
        ("  PermitRootLogin  yes  ", "prohibit-password", True),
        ("PasswordAuthentication yes", "no", True),
        ("PasswordAuthentication no", "no", False),
        ("X11Forwarding yes", "no", True),
        ("X11Forwarding no", "no", False),
    ],
)
def test_freebsd_ssh_hardener_config_line_comparison(
    existing_line, desired_value, should_change
):
    """
    Test SSH config line comparison logic with various existing line formats.
    """
    with patch("pyinfra.context.state", MagicMock(config=MagicMock())), patch(
        "pyinfra.context.host", MagicMock()
    ), patch("infraninja.security.freebsd.ssh_hardening.host") as mock_host, patch(
        "infraninja.security.freebsd.ssh_hardening.files"
    ) as mock_files, patch(
        "infraninja.security.freebsd.ssh_hardening.server"
    ) as mock_server, patch(
        "infraninja.security.freebsd.ssh_hardening.service"
    ) as mock_service:
        # Extract option name from desired_value parameter
        option_name = (
            "PermitRootLogin"
            if "PermitRootLogin" in existing_line
            else "PasswordAuthentication"
            if "PasswordAuthentication" in existing_line
            else "X11Forwarding"
        )

        # Configure mock_host.get_fact to return the test existing line
        mock_host.get_fact.return_value = [existing_line]

        # Configure mock returns
        replace_result = MagicMock()
        replace_result.changed = should_change
        mock_files.replace.return_value = replace_result

        # Create SSH hardener with single option
        custom_config = {option_name: desired_value}
        hardener = SSHHardener(ssh_config=custom_config)

        # Mock the deploy decorator
        with patch("pyinfra.api.deploy", lambda *args, **kwargs: lambda func: func):
            hardener.deploy()

        if should_change:
            # Should have called files.replace
            mock_files.replace.assert_called_once()
            # Should have restarted service
            mock_service.service.assert_called_once()
        else:
            # Should not have called files.replace
            assert mock_files.replace.call_count == 0
            # Should not have restarted service
            assert mock_service.service.call_count == 0


def test_freebsd_ssh_hardener_service_restart_parameters():
    """
    Test that SSH service restart is called with correct parameters.
    """
    with patch("pyinfra.context.state", MagicMock(config=MagicMock())), patch(
        "pyinfra.context.host", MagicMock()
    ), patch("infraninja.security.freebsd.ssh_hardening.host") as mock_host, patch(
        "infraninja.security.freebsd.ssh_hardening.files"
    ) as mock_files, patch(
        "infraninja.security.freebsd.ssh_hardening.server"
    ) as mock_server, patch(
        "infraninja.security.freebsd.ssh_hardening.service"
    ) as mock_service:
        # Configure mocks to simulate config changes
        mock_host.get_fact.return_value = []  # Options don't exist

        shell_result = MagicMock()
        shell_result.changed = True
        mock_server.shell.return_value = shell_result

        # Create SSH hardener
        hardener = SSHHardener()

        # Mock the deploy decorator
        with patch("pyinfra.api.deploy", lambda *args, **kwargs: lambda func: func):
            hardener.deploy()

        # Verify service.service was called with exact parameters
        mock_service.service.assert_called_once_with(
            name="Restart SSH service",
            srvname="sshd",
            srvstate="restarted",
            _ignore_errors=True,
        )


def test_freebsd_ssh_hardener_no_changes_no_restart():
    """
    Test that SSH service is not restarted when no config changes are made.
    """
    with patch("pyinfra.context.state", MagicMock(config=MagicMock())), patch(
        "pyinfra.context.host", MagicMock()
    ), patch("infraninja.security.freebsd.ssh_hardening.host") as mock_host, patch(
        "infraninja.security.freebsd.ssh_hardening.files"
    ) as mock_files, patch(
        "infraninja.security.freebsd.ssh_hardening.server"
    ) as mock_server, patch(
        "infraninja.security.freebsd.ssh_hardening.service"
    ) as mock_service:
        # Configure mocks to simulate no changes needed
        def get_fact_side_effect(fact_class, **kwargs):
            pattern = kwargs.get("pattern", "")
            if "PermitRootLogin" in pattern:
                return ["PermitRootLogin prohibit-password"]
            elif "PasswordAuthentication" in pattern:
                return ["PasswordAuthentication no"]
            elif "X11Forwarding" in pattern:
                return ["X11Forwarding no"]
            return []

        mock_host.get_fact.side_effect = get_fact_side_effect

        # Create SSH hardener
        hardener = SSHHardener()

        # Mock the deploy decorator
        with patch("pyinfra.api.deploy", lambda *args, **kwargs: lambda func: func):
            hardener.deploy()

        # Verify service was not restarted
        assert mock_service.service.call_count == 0

        # Verify no configuration operations were performed
        assert mock_files.replace.call_count == 0
        assert mock_server.shell.call_count == 0


def test_freebsd_ssh_hardener_print_statements():
    """
    Test that print statements are called with correct messages.
    """
    with patch("pyinfra.context.state", MagicMock(config=MagicMock())), patch(
        "pyinfra.context.host", MagicMock()
    ), patch("infraninja.security.freebsd.ssh_hardening.host") as mock_host, patch(
        "infraninja.security.freebsd.ssh_hardening.files"
    ) as mock_files, patch(
        "infraninja.security.freebsd.ssh_hardening.server"
    ) as mock_server, patch(
        "infraninja.security.freebsd.ssh_hardening.service"
    ) as mock_service, patch("builtins.print") as mock_print:
        # Configure mocks for mixed scenarios
        def get_fact_side_effect(fact_class, **kwargs):
            pattern = kwargs.get("pattern", "")
            if "PermitRootLogin" in pattern:
                return ["PermitRootLogin yes"]  # Incorrect
            elif "PasswordAuthentication" in pattern:
                return ["PasswordAuthentication no"]  # Correct
            elif "X11Forwarding" in pattern:
                return []  # Doesn't exist
            return []

        mock_host.get_fact.side_effect = get_fact_side_effect

        replace_result = MagicMock()
        replace_result.changed = True
        mock_files.replace.return_value = replace_result

        shell_result = MagicMock()
        shell_result.changed = True
        mock_server.shell.return_value = shell_result

        # Create SSH hardener
        hardener = SSHHardener()

        # Mock the deploy decorator
        with patch("pyinfra.api.deploy", lambda *args, **kwargs: lambda func: func):
            hardener.deploy()

        # Verify print statements were called with appropriate messages
        print_calls = [call[0][0] for call in mock_print.call_args_list]

        # Should have checking messages for all options
        assert any("Checking for PermitRootLogin" in call for call in print_calls)
        assert any(
            "Checking for PasswordAuthentication" in call for call in print_calls
        )
        assert any("Checking for X11Forwarding" in call for call in print_calls)

        # Should have update message for PermitRootLogin
        assert any("Updated PermitRootLogin" in call for call in print_calls)

        # Should have correct value message for PasswordAuthentication
        assert any(
            "PasswordAuthentication already set to correct value" in call
            for call in print_calls
        )

        # Should have added new option message for X11Forwarding
        assert any("Added new option X11Forwarding" in call for call in print_calls)


def test_freebsd_ssh_hardener_file_operations_parameters():
    """
    Test that file operations are called with correct parameters.
    """
    with patch("pyinfra.context.state", MagicMock(config=MagicMock())), patch(
        "pyinfra.context.host", MagicMock()
    ), patch("infraninja.security.freebsd.ssh_hardening.host") as mock_host, patch(
        "infraninja.security.freebsd.ssh_hardening.files"
    ) as mock_files, patch(
        "infraninja.security.freebsd.ssh_hardening.server"
    ) as mock_server, patch(
        "infraninja.security.freebsd.ssh_hardening.service"
    ) as mock_service:
        # Configure mocks for replace scenario
        mock_host.get_fact.return_value = ["PermitRootLogin yes"]

        replace_result = MagicMock()
        replace_result.changed = True
        mock_files.replace.return_value = replace_result

        # Create SSH hardener with single option
        custom_config = {"PermitRootLogin": "no"}
        hardener = SSHHardener(ssh_config=custom_config)

        # Mock the deploy decorator
        with patch("pyinfra.api.deploy", lambda *args, **kwargs: lambda func: func):
            hardener.deploy()

        # Verify files.replace was called with correct parameters
        mock_files.replace.assert_called_once()
        call_kwargs = mock_files.replace.call_args[1]

        assert call_kwargs["name"] == "Configure SSH: PermitRootLogin (update value)"
        assert call_kwargs["path"] == "/etc/ssh/sshd_config"
        assert call_kwargs["text"] == "^PermitRootLogin yes$"
        assert call_kwargs["replace"] == "PermitRootLogin no"
        assert call_kwargs["_ignore_errors"] is True
