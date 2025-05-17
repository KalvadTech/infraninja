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
        "infraninja.security.common.common_install.apt"
    ) as mock_apt, patch(
        "infraninja.security.common.common_install.apk"
    ) as mock_apk, patch(
        "infraninja.security.common.common_install.dnf"
    ) as mock_dnf, patch(
        "infraninja.security.common.common_install.yum"
    ) as mock_yum, patch(
        "infraninja.security.common.common_install.pacman"
    ) as mock_pacman, patch(
        "infraninja.security.common.common_install.zypper"
    ) as mock_zypper, patch(
        "infraninja.security.common.common_install.xbps"
    ) as mock_xbps, patch("infraninja.security.common.common_install.pkg") as mock_pkg:
        # Configure host.get_fact to return the distro info
        mock_host.get_fact.side_effect = lambda fact, **kwargs: (
            test_case["distro_info"]
            if fact.__name__ == "LinuxDistribution"
            else test_case.get("which_returns", False)
            if fact.__name__ == "Which"
            else None
        )

        mock_host.noop = MagicMock()  # Mock host.noop

        # Store all mocks for later verification
        mocks = {
            "apt.update": mock_apt.update,
            "apt.packages": mock_apt.packages,
            "apk.update": mock_apk.update,
            "apk.packages": mock_apk.packages,
            "dnf.packages": mock_dnf.packages,
            "yum.packages": mock_yum.packages,
            "pacman.update": mock_pacman.update,
            "pacman.packages": mock_pacman.packages,
            "zypper.packages": mock_zypper.packages,
            "xbps.packages": mock_xbps.packages,
            "pkg.packages": mock_pkg.packages,
        }

        # Mock the decorator to run the actual function without the decorator
        with patch(
            "pyinfra.api.deploy.deploy", lambda *args, **kwargs: lambda func: func
        ):
            # Create and run the CommonPackageInstaller
            installer = CommonPackageInstaller()
            result = installer.deploy()

        # Verify the function returned True if successful
        assert result is True

        # Verify the expected operations were called
        for operation in test_case["expected_operations"]:
            assert mocks[operation].called, (
                f"Expected {operation} to be called for {test_case['name']}"
            )

            # If it's a packages operation, verify it was called with appropriate packages
            if operation.endswith(".packages"):
                args, kwargs = mocks[operation].call_args
                assert "packages" in kwargs, (
                    f"Expected 'packages' in kwargs for {operation}"
                )
                assert len(kwargs["packages"]) > 0, (
                    f"Expected non-empty package list for {operation}"
                )

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
        "infraninja.security.common.common_install.apt"
    ) as mock_apt:
        # Configure host.get_fact to return Debian
        mock_host.get_fact.return_value = {
            "name": "Debian GNU/Linux",
            "release_meta": {"ID": "debian", "ID_LIKE": ""},
        }

        mock_host.noop = MagicMock()  # Mock host.noop

        # Mock the decorator
        with patch(
            "pyinfra.api.deploy.deploy", lambda *args, **kwargs: lambda func: func
        ):
            # Create and run the CommonPackageInstaller with custom packages
            installer = CommonPackageInstaller(packages=custom_packages)
            result = installer.deploy()

        # Verify the function returned True
        assert result is True

        # Verify apt.packages was called with the custom package
        args, kwargs = mock_apt.packages.call_args
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
