from unittest.mock import patch

import pytest

from infraninja.security.freebsd.install_tools import FreeBSDSecurityInstaller


def test_freebsd_security_installer_class():
    """
    Test FreeBSDSecurityInstaller class structure and defaults.
    """
    # Test that the class can be instantiated
    installer = FreeBSDSecurityInstaller()

    # Verify it has the expected default packages
    assert hasattr(installer, "packages")
    assert isinstance(installer.packages, dict)

    # Verify it has the expected methods
    assert hasattr(installer, "deploy")
    assert hasattr(installer, "_verify_freebsd")
    assert hasattr(installer, "_configure_tool")

    # Check some expected security tools in defaults
    assert "fail2ban" in installer.packages
    assert "clamav" in installer.packages
    assert "suricata" in installer.packages

    # Verify package lists are correct
    assert isinstance(installer.packages["fail2ban"], list)
    assert "security/py-fail2ban" in installer.packages["fail2ban"]


def test_freebsd_security_installer_custom_packages():
    """
    Test FreeBSDSecurityInstaller with custom packages.
    """
    custom_packages = {
        "custom_tool": ["custom-package"],
        "fail2ban": ["custom-fail2ban"],
    }

    installer = FreeBSDSecurityInstaller(packages=custom_packages)

    # Verify custom packages are used
    assert installer.packages == custom_packages
    assert "custom_tool" in installer.packages
    assert installer.packages["fail2ban"] == ["custom-fail2ban"]


def test_freebsd_security_installer_verify_freebsd():
    """
    Test _verify_freebsd method with FreeBSD and non-FreeBSD systems.
    """
    with patch("infraninja.security.freebsd.install_tools.host") as mock_host:
        # Test with FreeBSD
        mock_host.get_fact.return_value = {
            "name": "FreeBSD",
            "release_meta": {"ID": "freebsd"},
        }

        result = FreeBSDSecurityInstaller._verify_freebsd()
        assert result is True

        # Test with non-FreeBSD
        mock_host.get_fact.return_value = {
            "name": "Ubuntu",
            "release_meta": {"ID": "ubuntu"},
        }

        with pytest.raises(ValueError) as exc_info:
            FreeBSDSecurityInstaller._verify_freebsd()

        assert "This deployment is designed for FreeBSD systems only" in str(
            exc_info.value
        )


def test_freebsd_security_installer_deploy_structure():
    """
    Test that deploy method can be called and has proper structure.
    """
    installer = FreeBSDSecurityInstaller()

    # Verify deploy method exists and is callable
    assert hasattr(installer, "deploy")
    assert callable(installer.deploy)

    # Verify it's decorated with @deploy
    assert hasattr(installer.deploy, "__wrapped__") or hasattr(
        installer.deploy, "_pyinfra_op"
    )


def test_freebsd_security_installer_configure_tool():
    """
    Test _configure_tool method structure.
    """
    installer = FreeBSDSecurityInstaller()

    # Verify method exists
    assert hasattr(installer, "_configure_tool")
    assert callable(installer._configure_tool)

    # The method should accept a tool name parameter
    # We can't easily test the actual pyinfra operations without mocking extensively,
    # but we can verify the method structure
