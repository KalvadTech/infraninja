#!/usr/bin/env python3
# tests/freebsd/test_acl.py

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from infraninja.security.freebsd.acl import acl_setup


class TestFreeBSDACLSetup(unittest.TestCase):
    """Test cases for the FreeBSD ACL setup function."""

    def test_acl_setup_success(self):
        """
        Test acl_setup function with successful execution on FreeBSD.
        """
        with patch("pyinfra.context.state", MagicMock(config=MagicMock())), patch(
            "pyinfra.context.host", MagicMock()
        ), patch("infraninja.security.freebsd.acl.host") as mock_host, patch(
            "infraninja.security.freebsd.acl.server"
        ) as mock_server:
            # Configure host.get_fact to return FreeBSD distro info
            mock_host.get_fact.side_effect = (
                lambda fact_class, **kwargs: {
                    "name": "FreeBSD",
                    "release_meta": {"ID": "freebsd"},
                }
                if "LinuxDistribution" in str(fact_class)
                else "/fake/path"
            )

            # Mock setfacl availability
            mock_server.shell.return_value = True

            # Mock the decorator
            with patch(
                "pyinfra.api.deploy.deploy", lambda *args, **kwargs: lambda func: func
            ):
                # Run the acl_setup function
                result = acl_setup()

            # Verify setfacl availability was checked
            mock_server.shell.assert_any_call(
                name="Check if setfacl exists",
                commands=["command -v setfacl"],
                _ignore_errors=True,
            )

            # Verify ACL mount check
            mock_server.shell.assert_any_call(
                name="Check if root filesystem is mounted with ACLs",
                commands=["mount | grep 'on / ' | grep -q acls"],
                _ignore_errors=True,
            )

            # Verify result - the function currently always returns False
            assert result is False

    def test_acl_setup_non_freebsd(self):
        """
        Test acl_setup function raises error on non-FreeBSD systems.
        """
        with patch("pyinfra.context.state", MagicMock(config=MagicMock())), patch(
            "pyinfra.context.host", MagicMock()
        ), patch("infraninja.security.freebsd.acl.host") as mock_host:
            # Configure host.get_fact to return a non-FreeBSD distro
            mock_host.get_fact.return_value = {
                "name": "Ubuntu",
                "release_meta": {"ID": "ubuntu"},
            }

            # Mock the decorator
            with patch(
                "pyinfra.api.deploy.deploy", lambda *args, **kwargs: lambda func: func
            ):
                # Verify acl_setup raises ValueError for non-FreeBSD OS
                with self.assertRaises(ValueError) as context:
                    acl_setup()

                self.assertIn(
                    "This deployment is designed for FreeBSD systems only",
                    str(context.exception),
                )

    def test_acl_setup_no_setfacl(self):
        """
        Test acl_setup function when setfacl is not available.
        """
        with patch("pyinfra.context.state", MagicMock(config=MagicMock())), patch(
            "pyinfra.context.host", MagicMock()
        ), patch("infraninja.security.freebsd.acl.host") as mock_host, patch(
            "infraninja.security.freebsd.acl.server"
        ) as mock_server:
            # Configure host.get_fact to return FreeBSD distro info
            mock_host.get_fact.return_value = {
                "name": "FreeBSD",
                "release_meta": {"ID": "freebsd"},
            }

            # Mock setfacl not available
            mock_server.shell.return_value = False

            # Mock the decorator
            with patch(
                "pyinfra.api.deploy.deploy", lambda *args, **kwargs: lambda func: func
            ):
                # Run the acl_setup function
                result = acl_setup()

            # Verify setfacl availability was checked
            mock_server.shell.assert_called_with(
                name="Check if setfacl exists",
                commands=["command -v setfacl"],
                _ignore_errors=True,
            )

            # Verify noop was called for missing setfacl
            mock_host.noop.assert_called_with(
                "setfacl not available on this FreeBSD system"
            )

            # Verify result
            assert result is False

    def test_acl_setup_mount_check_fails(self):
        """
        Test acl_setup function when ACL mount check fails and tunefs fails.
        """
        with patch("pyinfra.context.state", MagicMock(config=MagicMock())), patch(
            "pyinfra.context.host", MagicMock()
        ), patch("infraninja.security.freebsd.acl.host") as mock_host, patch(
            "infraninja.security.freebsd.acl.server"
        ) as mock_server:
            # Configure host.get_fact to return FreeBSD distro info
            mock_host.get_fact.return_value = {
                "name": "FreeBSD",
                "release_meta": {"ID": "freebsd"},
            }

            # Mock shell commands - setfacl exists but mount check and tunefs fail
            def mock_shell(*args, **kwargs):
                name = kwargs.get("name", "")
                if "Check if setfacl exists" in name:
                    return True  # setfacl available
                elif "Check if root filesystem is mounted with ACLs" in name:
                    return False  # ACLs not mounted
                elif "Try to enable ACL support" in name:
                    return False  # tunefs fails
                return False

            mock_server.shell.side_effect = mock_shell

            # Mock the decorator
            with patch(
                "pyinfra.api.deploy.deploy", lambda *args, **kwargs: lambda func: func
            ):
                # Run the acl_setup function
                result = acl_setup()

            # Verify appropriate noop was called
            mock_host.noop.assert_any_call(
                "ACL support cannot be enabled. Root filesystem may need fsck or "
                "may not support ACLs. Consider running 'fsck /' when unmounted "
                "or rebuilding kernel with UFS_ACL option."
            )

            # Verify result
            assert result is False

    def test_acl_setup_file_not_found(self):
        """
        Test acl_setup function when some target files don't exist.
        """
        with patch("pyinfra.context.state", MagicMock(config=MagicMock())), patch(
            "pyinfra.context.host", MagicMock()
        ), patch("infraninja.security.freebsd.acl.host") as mock_host, patch(
            "infraninja.security.freebsd.acl.server"
        ) as mock_server:
            # Configure host.get_fact to return FreeBSD distro info and file existence
            def mock_get_fact(fact_class, **kwargs):
                if "LinuxDistribution" in str(fact_class):
                    return {"name": "FreeBSD", "release_meta": {"ID": "freebsd"}}
                elif "File" in str(fact_class):
                    # Return None for some files to simulate they don't exist
                    path = kwargs.get("path", "")
                    if "/usr/local/etc/fail2ban" in path:
                        return None  # File doesn't exist
                    return "/fake/path"  # File exists
                return None

            mock_host.get_fact.side_effect = mock_get_fact

            # Mock setfacl availability
            mock_server.shell.return_value = True

            # Mock the decorator
            with patch(
                "pyinfra.api.deploy.deploy", lambda *args, **kwargs: lambda func: func
            ):
                # Run the acl_setup function
                result = acl_setup()

            # Verify noop was called for missing files
            mock_host.noop.assert_any_call(
                "Skip ACL for /usr/local/etc/fail2ban - path does not exist"
            )

            # Verify result - the function currently always returns False
            assert result is False


if __name__ == "__main__":
    unittest.main()
