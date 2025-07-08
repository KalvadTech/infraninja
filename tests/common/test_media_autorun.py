from unittest.mock import MagicMock, patch

import pytest

from infraninja.security.common.media_autorun import media_autorun

# Test cases for different distribution types
DISTRO_TEST_CASES = [
    {
        "name": "ubuntu",
        "distro_info": {"name": "Ubuntu"},
        "has_udevadm": True,
        "is_freebsd": False,
    },
    {
        "name": "alpine",
        "distro_info": {"name": "Alpine Linux"},
        "has_udevadm": True,
        "is_freebsd": False,
    },
    {
        "name": "freebsd",
        "distro_info": {"name": "FreeBSD"},
        "has_udevadm": False,
        "is_freebsd": True,
    },
    {
        "name": "centos_without_udevadm",
        "distro_info": {"name": "CentOS Linux"},
        "has_udevadm": False,
        "is_freebsd": False,
    },
]


@pytest.mark.parametrize("test_case", DISTRO_TEST_CASES)
def test_media_autorun(test_case):
    """
    Test media_autorun function across different distributions.
    """

    # Configure mock behavior based on the distribution being tested
    def which_side_effect(fact, command, **kwargs):
        if fact.__name__ == "Which" and command == "udevadm":
            return test_case["has_udevadm"]
        return False

    # Setup mocks for all the functions we need
    with patch("pyinfra.context.state", MagicMock(config=MagicMock())), patch(
        "pyinfra.context.host", MagicMock()
    ), patch("infraninja.security.common.media_autorun.host") as mock_host, patch(
        "infraninja.security.common.media_autorun.files"
    ) as mock_files, patch(
        "infraninja.security.common.media_autorun.server"
    ) as mock_server:
        # Setup host.get_fact to return appropriate values
        mock_host.get_fact.side_effect = lambda fact, **kwargs: (
            test_case["distro_info"]
            if fact.__name__ == "LinuxDistribution"
            else which_side_effect(fact, **kwargs)
        )

        # Patch the deploy decorator to make it a no-op and call the function
        with patch("pyinfra.api.deploy", lambda *args, **kwargs: lambda func: func):
            # This calls the function directly without decoration
            media_autorun()

        # Verify server.service was called to disable autofs
        assert mock_server.service.called, "server.service was not called"
        assert mock_server.service.call_args[1]["service"] == "autofs"
        assert mock_server.service.call_args[1]["running"] is False
        assert mock_server.service.call_args[1]["enabled"] is False

        # Verify udev directory and rules were handled correctly based on the distro
        if not test_case["is_freebsd"]:
            # Check that udev directory was created
            assert mock_files.directory.called
            udev_dir_called = False
            for call in mock_files.directory.call_args_list:
                if call[1]["path"] == "/etc/udev/rules.d":
                    udev_dir_called = True
                    assert call[1]["present"] is True
            assert udev_dir_called, "Directory /etc/udev/rules.d was not created"

            # Check that udev rule was added
            assert mock_files.line.called
            udev_rule_called = False
            for call in mock_files.line.call_args_list:
                if (
                    call[1]["path"] == "/etc/udev/rules.d/85-no-automount.rules"
                    and 'ENV{UDISKS_AUTO}="0"' in call[1]["line"]
                ):
                    udev_rule_called = True
                    assert call[1]["present"] is True
            assert udev_rule_called, "Udev rule was not added"

            # Check if udevadm reload was called when available
            if test_case["has_udevadm"]:
                udev_reload_called = False
                for call in mock_server.shell.call_args_list:
                    if "udevadm control --reload-rules" in call[1]["commands"][0]:
                        udev_reload_called = True
                assert udev_reload_called, "Udevadm reload was not called"
            else:
                # Check that a noop was called when udevadm is not available
                mock_host.noop.assert_called_with(
                    f"Skipping udevadm reload as it's not available on {test_case['distro_info']['name'].lower()}"
                )

        # Verify mount point directory was created
        usb_dir_called = False
        for call in mock_files.directory.call_args_list:
            if call[1]["path"] == "/mnt/usb":
                usb_dir_called = True
                assert call[1]["present"] is True
        assert usb_dir_called, "Directory /mnt/usb was not created"

        # Verify fstab entry was added
        fstab_called = False
        for call in mock_files.line.call_args_list:
            if (
                call[1]["path"] == "/etc/fstab"
                and "/dev/sda1 /mnt/usb" in call[1]["line"]
            ):
                fstab_called = True
                assert call[1]["present"] is True
        assert fstab_called, "Fstab entry was not added"

        # Verify mount command was run
        mount_called = False
        for call in mock_server.shell.call_args_list:
            if "mount -a || true" in call[1]["commands"][0]:
                mount_called = True
        assert mount_called, "Mount command was not called"
