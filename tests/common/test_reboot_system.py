import pytest
from unittest.mock import patch, MagicMock

from infraninja.security.common.reboot_system import (
    reboot_system,
    check_reboot_required,
)


@pytest.mark.parametrize(
    "stdout, expected_result",
    [
        (["reboot_required"], True),
        (["no_reboot_required"], False),
        (["something_else"], False),
        ([], False),
    ],
)
def test_check_reboot_required(stdout, expected_result):
    """
    Test check_reboot_required function with different command outputs.
    """
    # Create mocks
    with patch("pyinfra.context.state", MagicMock(config=MagicMock())), patch(
        "pyinfra.context.host", MagicMock()
    ), patch("infraninja.security.common.reboot_system.host") as mock_host:
        # Configure host.get_fact to return the test stdout
        mock_host.get_fact.return_value = stdout

        # Call the function and check results
        result = check_reboot_required(mock_host)
        assert result == expected_result, (
            f"Expected {expected_result} for stdout: {stdout}"
        )


@pytest.mark.parametrize(
    "need_reboot, force_reboot, skip_reboot_check, reboot_required, should_reboot",
    [
        # Explicit reboot settings
        (True, False, False, False, True),  # need_reboot=True should always reboot
        (False, False, False, True, False),  # need_reboot=False should never reboot
        # Force reboot overrides
        (
            False,
            True,
            False,
            False,
            True,
        ),  # force_reboot=True should override need_reboot=False
        (
            None,
            True,
            False,
            False,
            True,
        ),  # force_reboot=True should override need_reboot=None
        # Auto-detection (need_reboot=None)
        (None, False, False, True, True),  # auto-detect: reboot required
        (None, False, False, False, False),  # auto-detect: no reboot required
        # Skip reboot check
        (
            True,
            False,
            True,
            False,
            True,
        ),  # skip_reboot_check=True: use need_reboot value
        (
            False,
            False,
            True,
            True,
            False,
        ),  # skip_reboot_check=True: use need_reboot value
        (
            None,
            False,
            True,
            True,
            False,
        ),  # skip_reboot_check=True with need_reboot=None: no reboot
    ],
)
def test_reboot_system(
    need_reboot, force_reboot, skip_reboot_check, reboot_required, should_reboot
):
    """
    Test reboot_system under various conditions.
    """
    # Create mocks
    with patch("pyinfra.context.state", MagicMock(config=MagicMock())), patch(
        "pyinfra.context.host", MagicMock()
    ), patch(
        "infraninja.security.common.reboot_system.check_reboot_required"
    ) as mock_check_reboot, patch(
        "infraninja.security.common.reboot_system.server"
    ) as mock_server:
        # Configure check_reboot_required to return the test value
        mock_check_reboot.return_value = reboot_required

        # Mock the deploy decorator to run the function directly
        with patch(
            "pyinfra.api.deploy.deploy", lambda *args, **kwargs: lambda func: func
        ):
            # Call the reboot_system function
            reboot_system(
                need_reboot=need_reboot,
                force_reboot=force_reboot,
                skip_reboot_check=skip_reboot_check,
            )

        # Check if server.reboot was called (or not) as expected
        if should_reboot:
            mock_server.reboot.assert_called_once()
        else:
            mock_server.reboot.assert_not_called()


def test_check_reboot_required_command_content():
    """
    Test that the check_reboot_required function passes the correct shell command.
    This test ensures the command checks for the appropriate reboot indicators.
    """
    # Create mocks
    with patch("pyinfra.context.state", MagicMock(config=MagicMock())), patch(
        "pyinfra.context.host", MagicMock()
    ), patch("infraninja.security.common.reboot_system.host") as mock_host:
        # Configure host.get_fact to capture the command
        def capture_command(fact_class, command, **kwargs):
            if fact_class.__name__ == "Command":
                # Store the command for inspection
                capture_command.last_command = command
                return ["no_reboot_required"]
            return None

        capture_command.last_command = None
        mock_host.get_fact.side_effect = capture_command

        # Call the function
        check_reboot_required(mock_host)

        # Verify the command contains checks for appropriate reboot indicators
        command = capture_command.last_command
        assert "/var/run/reboot-required" in command, (
            "Command should check for reboot-required file"
        )
        assert "uname -r" in command, "Command should check for kernel version"
        assert "Alpine" in command, "Command should handle Alpine Linux"
        assert "pacman" in command, "Command should handle Arch Linux"
        assert "dnf" in command, "Command should handle Fedora/RHEL"
        assert "apt" in command, "Command should handle Debian/Ubuntu"
