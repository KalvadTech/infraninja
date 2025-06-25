from unittest.mock import MagicMock, patch

import pytest

# Import the module containing system_update
from infraninja.security.common.update_packages import system_update

# Test cases for different Linux distributions
DISTRO_TEST_CASES = [
    # Debian-based systems
    {
        "name": "debian",
        "distro_info": {
            "name": "Debian GNU/Linux",
            "release_meta": {"ID": "debian", "ID_LIKE": ""},
        },
        "expected_operations": ["apt.update", "apt.upgrade"],
    },
    {
        "name": "ubuntu",
        "distro_info": {
            "name": "Ubuntu",
            "release_meta": {"ID": "ubuntu", "ID_LIKE": "debian"},
        },
        "expected_operations": ["apt.update", "apt.upgrade"],
    },
    {
        "name": "mint",
        "distro_info": {
            "name": "Linux Mint",
            "release_meta": {"ID": "linuxmint", "ID_LIKE": "ubuntu debian"},
        },
        "expected_operations": ["apt.update", "apt.upgrade"],
    },
    # Alpine
    {
        "name": "alpine",
        "distro_info": {
            "name": "Alpine Linux",
            "release_meta": {"ID": "alpine", "ID_LIKE": ""},
        },
        "expected_operations": ["apk.update", "apk.upgrade"],
    },
    # RHEL family with DNF
    {
        "name": "fedora_dnf",
        "distro_info": {
            "name": "Fedora Linux",
            "release_meta": {"ID": "fedora", "ID_LIKE": ""},
        },
        "which_returns": True,
        "expected_operations": ["dnf.update"],
    },
    # RHEL family with YUM
    {
        "name": "centos_yum",
        "distro_info": {
            "name": "CentOS Linux",
            "release_meta": {"ID": "centos", "ID_LIKE": "rhel fedora"},
        },
        "which_returns": False,
        "expected_operations": ["yum.update"],
    },
    # Arch Linux
    {
        "name": "arch",
        "distro_info": {
            "name": "Arch Linux",
            "release_meta": {"ID": "arch", "ID_LIKE": ""},
        },
        "expected_operations": ["pacman.update", "pacman.upgrade"],
    },
    # openSUSE
    {
        "name": "opensuse",
        "distro_info": {
            "name": "openSUSE Leap",
            "release_meta": {"ID": "opensuse-leap", "ID_LIKE": "suse"},
        },
        "expected_operations": ["zypper.update"],
    },
    # Void Linux
    {
        "name": "void",
        "distro_info": {
            "name": "Void Linux",
            "release_meta": {"ID": "void", "ID_LIKE": ""},
        },
        "expected_operations": ["xbps.update", "xbps.upgrade"],
    },
]


@pytest.mark.parametrize("test_case", DISTRO_TEST_CASES)
def test_system_update_for_distros(test_case):
    """
    Test system_update function with different distributions.
    Uses parametrization to test all supported distributions.
    """
    # Mock the pyinfra modules
    mocks = {}

    # We need to mock the state and config in pyinfra's context
    with patch("pyinfra.context.state", MagicMock(config=MagicMock())), patch(
        "pyinfra.context.host", MagicMock()
    ), patch("infraninja.security.common.update_packages.host") as mock_host, patch(
        "infraninja.security.common.update_packages.apt"
    ) as mock_apt, patch(
        "infraninja.security.common.update_packages.apk"
    ) as mock_apk, patch(
        "infraninja.security.common.update_packages.dnf"
    ) as mock_dnf, patch(
        "infraninja.security.common.update_packages.yum"
    ) as mock_yum, patch(
        "infraninja.security.common.update_packages.pacman"
    ) as mock_pacman, patch(
        "infraninja.security.common.update_packages.zypper"
    ) as mock_zypper, patch(
        "infraninja.security.common.update_packages.xbps"
    ) as mock_xbps:
        # Store all mocks for later verification
        mocks = {
            "apt.update": mock_apt.update,
            "apt.upgrade": mock_apt.upgrade,
            "apk.update": mock_apk.update,
            "apk.upgrade": mock_apk.upgrade,
            "dnf.update": mock_dnf.update,
            "yum.update": mock_yum.update,
            "pacman.update": mock_pacman.update,
            "pacman.upgrade": mock_pacman.upgrade,
            "zypper.update": mock_zypper.update,
            "xbps.update": mock_xbps.update,
            "xbps.upgrade": mock_xbps.upgrade,
        }

        # Configure host.get_fact to return the distro info
        mock_host.get_fact.side_effect = lambda fact, **kwargs: (
            test_case["distro_info"]
            if fact.__name__ == "LinuxDistribution"
            else test_case.get("which_returns", False)
        )

        # Mock the decorator itself to run the actual function without the decorator
        with patch(
            "pyinfra.api.deploy.deploy", lambda *args, **kwargs: lambda func: func
        ):
            # Run the system_update function
            system_update()

        # Verify the expected operations were called
        for operation in test_case["expected_operations"]:
            mock_operation = mocks[operation]
            assert mock_operation.called, (
                f"Expected {operation} to be called for {test_case['name']}"
            )

        # Verify other operations were not called
        for operation, mock_operation in mocks.items():
            if operation not in test_case["expected_operations"]:
                assert not mock_operation.called, (
                    f"{operation} should not have been called for {test_case['name']}"
                )


def test_system_update_unsupported_os():
    """
    Test system_update raises an error for unsupported OS.
    """
    # Mock pyinfra state and context
    with patch("pyinfra.context.state", MagicMock(config=MagicMock())), patch(
        "pyinfra.context.host", MagicMock()
    ), patch("infraninja.security.common.update_packages.host") as mock_host:
        # Configure host.get_fact to return an unsupported distro
        mock_host.get_fact.return_value = {
            "name": "Unsupported OS",
            "release_meta": {"ID": "unknown", "ID_LIKE": ""},
        }

        # Mock the decorator to run the actual function without the decorator
        with patch(
            "pyinfra.api.deploy.deploy", lambda *args, **kwargs: lambda func: func
        ):
            # Verify that system_update raises ValueError for unsupported OS
            with pytest.raises(ValueError, match="Unsupported OS"):
                system_update()
