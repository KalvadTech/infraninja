import pytest
from unittest.mock import patch, MagicMock

from infraninja.security.common.common_install import CommonPackageInstaller

# Test cases for different distributions
DISTRO_TEST_CASES = [
    {
        "name": "debian",
        "distro_info": {
            "name": "Debian GNU/Linux",
            "release_meta": {"ID": "debian", "ID_LIKE": ""},
        },
        "expected_distro_family": "debian",
        "expected_operations": ["apt.update", "apt.packages"],
    },
    {
        "name": "ubuntu",
        "distro_info": {
            "name": "Ubuntu",
            "release_meta": {"ID": "ubuntu", "ID_LIKE": "debian"},
        },
        "expected_distro_family": "debian",
        "expected_operations": ["apt.update", "apt.packages"],
    },
    {
        "name": "alpine",
        "distro_info": {
            "name": "Alpine Linux",
            "release_meta": {"ID": "alpine", "ID_LIKE": ""},
        },
        "expected_distro_family": "alpine",
        "expected_operations": ["apk.update", "apk.packages"],
    },
    {
        "name": "fedora_dnf",
        "distro_info": {
            "name": "Fedora Linux",
            "release_meta": {"ID": "fedora", "ID_LIKE": ""},
        },
        "which_returns": True,
        "expected_distro_family": "rhel",
        "expected_operations": ["dnf.packages"],
    },
    {
        "name": "centos_yum",
        "distro_info": {
            "name": "CentOS Linux",
            "release_meta": {"ID": "centos", "ID_LIKE": "rhel fedora"},
        },
        "which_returns": False,
        "expected_distro_family": "rhel",
        "expected_operations": ["yum.packages"],
    },
    {
        "name": "arch",
        "distro_info": {
            "name": "Arch Linux",
            "release_meta": {"ID": "arch", "ID_LIKE": ""},
        },
        "expected_distro_family": "arch",
        "expected_operations": ["pacman.update", "pacman.packages"],
    },
    {
        "name": "opensuse",
        "distro_info": {
            "name": "openSUSE Leap",
            "release_meta": {"ID": "opensuse-leap", "ID_LIKE": "suse"},
        },
        "expected_distro_family": "suse",
        "expected_operations": ["zypper.packages"],
    },
    {
        "name": "void",
        "distro_info": {
            "name": "Void Linux",
            "release_meta": {"ID": "void", "ID_LIKE": ""},
        },
        "expected_distro_family": "void",
        "expected_operations": ["xbps.packages"],
    },
    {
        "name": "freebsd",
        "distro_info": {
            "name": "FreeBSD",
            "release_meta": {"ID": "freebsd", "ID_LIKE": ""},
        },
        "expected_distro_family": "freebsd",
        "expected_operations": ["pkg.packages"],
    },
]


@pytest.mark.parametrize("test_case", DISTRO_TEST_CASES)
def test_common_package_installer(test_case):
    """
    Test CommonPackageInstaller across different distributions.
    """
    # Create mocks
    with patch("pyinfra.context.state", MagicMock(config=MagicMock())), patch(
        "pyinfra.context.host", MagicMock()
    ), patch("infraninja.security.common.common_install.host") as mock_host, patch(
        "infraninja.security.common.common_install.server"
    ) as mock_server:
        # Configure host.get_fact to return the distro info
        mock_host.get_fact.side_effect = lambda fact, **kwargs: (
            test_case["distro_info"]
            if fact.__name__ == "LinuxDistribution"
            else test_case.get("which_returns", False)
            if fact.__name__ == "Which"
            else None
        )

        mock_host.noop = MagicMock()  # Mock host.noop

        # Create the CommonPackageInstaller instance
        installer = CommonPackageInstaller()

        # Patch the deploy decorator to make it a no-op and call the method
        with patch("pyinfra.api.deploy", lambda *args, **kwargs: lambda func: func):
            # This calls the function directly without decoration
            result = installer.deploy()

        # Verify the function returned True if successful
        assert result is True

        # Verify server.packages was called
        assert mock_server.packages.called

        # Get the arguments passed to server.packages
        args, kwargs = mock_server.packages.call_args

        # Verify the packages kwarg exists
        assert "packages" in kwargs, "Expected 'packages' in kwargs"
        assert len(kwargs["packages"]) > 0, "Expected non-empty package list"

        # Check if the expected packages for the distro family are included
        distro_family = test_case["expected_distro_family"]
        for (
            package_type,
            distro_packages,
        ) in CommonPackageInstaller.DEFAULT_PACKAGES.items():
            if distro_family in distro_packages:
                for package in distro_packages[distro_family]:
                    assert package in kwargs["packages"], (
                        f"Expected package {package} for {distro_family}"
                    )


def test_common_package_installer_custom_packages():
    """
    Test CommonPackageInstaller with custom package definitions.
    """
    # Define custom packages
    custom_packages = {
        "custom-tool": {
            "debian": ["custom-deb-pkg"],
            "alpine": ["custom-alpine-pkg"],
            "rhel": ["custom-rhel-pkg"],
            "arch": ["custom-arch-pkg"],
            "suse": ["custom-suse-pkg"],
            "void": ["custom-void-pkg"],
            "freebsd": ["custom-freebsd-pkg"],
        }
    }

    # Setup mocks
    with patch("pyinfra.context.state", MagicMock(config=MagicMock())), patch(
        "pyinfra.context.host", MagicMock()
    ), patch("infraninja.security.common.common_install.host") as mock_host, patch(
        "infraninja.security.common.common_install.server"
    ) as mock_server:
        # Configure host.get_fact to return Debian
        mock_host.get_fact.return_value = {
            "name": "Debian GNU/Linux",
            "release_meta": {"ID": "debian", "ID_LIKE": ""},
        }

        mock_host.noop = MagicMock()  # Mock host.noop

        # Create the CommonPackageInstaller instance with custom packages
        installer = CommonPackageInstaller(packages=custom_packages)

        # Patch the deploy decorator to make it a no-op and call the method
        with patch("pyinfra.api.deploy", lambda *args, **kwargs: lambda func: func):
            # This calls the function directly without decoration
            result = installer.deploy()

        # Verify the function returned True
        assert result is True

        # Verify server.packages was called with the custom package
        args, kwargs = mock_server.packages.call_args
        assert "custom-deb-pkg" in kwargs["packages"], (
            "Expected custom package to be installed"
        )

        # Verify default packages are not included
        for (
            package_type,
            distro_packages,
        ) in CommonPackageInstaller.DEFAULT_PACKAGES.items():
            if "debian" in distro_packages:
                for package in distro_packages["debian"]:
                    assert package not in kwargs["packages"], (
                        f"Did not expect default package {package}"
                    )


def test_common_package_installer_unsupported_os():
    """
    Test CommonPackageInstaller raises an error for unsupported OS.
    """
    # Setup mocks
    with patch("pyinfra.context.state", MagicMock(config=MagicMock())), patch(
        "pyinfra.context.host", MagicMock()
    ), patch("infraninja.security.common.common_install.host") as mock_host:
        # Configure host.get_fact to return an unsupported distro
        mock_host.get_fact.return_value = {
            "name": "Unsupported OS",
            "release_meta": {"ID": "unknown", "ID_LIKE": ""},
        }

        mock_host.noop = MagicMock()  # Mock host.noop

        # Mock the decorator
        with patch(
            "pyinfra.api.deploy.deploy", lambda *args, **kwargs: lambda func: func
        ):
            # Verify that deploy raises ValueError for unsupported OS
            with pytest.raises(ValueError, match="Unsupported OS"):
                installer = CommonPackageInstaller()
                installer.deploy()
