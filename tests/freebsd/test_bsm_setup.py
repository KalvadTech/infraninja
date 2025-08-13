#!/usr/bin/env python3
# tests/freebsd/test_bsm_setup.py

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from infraninja.security.freebsd.bsm_setup import bsm_setup


class TestBSMSetup(unittest.TestCase):
    """Test cases for the BSM setup function."""

    def test_bsm_setup_success(self):
        """
        Test bsm_setup function with successful execution on FreeBSD.
        """
        with patch("pyinfra.context.state", MagicMock(config=MagicMock())), patch(
            "pyinfra.context.host", MagicMock()
        ), patch("infraninja.security.freebsd.bsm_setup.host") as mock_host, patch(
            "infraninja.security.freebsd.bsm_setup.files"
        ) as mock_files, patch(
            "infraninja.security.freebsd.bsm_setup.server"
        ) as mock_server, patch(
            "infraninja.security.freebsd.bsm_setup.service"
        ) as mock_service:
            # Configure host.get_fact to return FreeBSD distro info
            mock_host.get_fact.return_value = {
                "name": "FreeBSD",
                "release_meta": {"ID": "freebsd"},
            }

            # Mock the decorator
            with patch(
                "pyinfra.api.deploy.deploy", lambda *args, **kwargs: lambda func: func
            ):
                # Run the bsm_setup function
                result = bsm_setup()

            # Verify audit directory was created
            mock_files.directory.assert_any_call(
                name="Create audit directory",
                path="/var/audit",
                present=True,
                mode="750",
                user="root",
                group="wheel",
            )

            # Verify audit_control template was uploaded
            mock_files.template.assert_any_call(
                name="Upload BSM audit_control configuration",
                src=str(
                    Path(__file__).parent.parent.parent
                    / "infraninja"
                    / "security"
                    / "templates"
                    / "freebsd"
                    / "audit_control.j2"
                ),
                dest="/etc/security/audit_control",
                backup=True,
                create_remote_dir=True,
            )

            # Verify audit_user template was uploaded
            mock_files.template.assert_any_call(
                name="Upload BSM audit_user configuration",
                src=str(
                    Path(__file__).parent.parent.parent
                    / "infraninja"
                    / "security"
                    / "templates"
                    / "freebsd"
                    / "audit_user.j2"
                ),
                dest="/etc/security/audit_user",
                backup=True,
                create_remote_dir=True,
            )

            # Verify newsyslog configuration
            mock_files.template.assert_any_call(
                name="Upload BSM newsyslog configuration",
                src=str(
                    Path(__file__).parent.parent.parent
                    / "infraninja"
                    / "security"
                    / "templates"
                    / "freebsd"
                    / "bsm_newsyslog.conf.j2"
                ),
                dest="/etc/newsyslog.conf.d/bsm.conf",
                create_remote_dir=True,
            )

            # Verify auditd was enabled in rc.conf
            mock_files.line.assert_any_call(
                name="Enable auditd in rc.conf",
                path="/etc/rc.conf",
                line='auditd_enable="YES"',
                present=True,
            )

            # Verify audit flags were set in rc.conf
            mock_files.line.assert_any_call(
                name="Set audit flags in rc.conf",
                path="/etc/rc.conf",
                line='audit_flags="lo,aa"',
                present=True,
            )

            # Verify service was started
            mock_service.service.assert_any_call(
                srvname="auditd",
                srvstate="started",
            )

            # Verify service was restarted
            mock_service.service.assert_any_call(
                srvname="auditd",
                srvstate="restarted",
            )

            # Verify audit configuration refresh
            mock_server.shell.assert_any_call(
                name="Refresh audit configuration",
                commands=["audit -s 2>/dev/null || audit -i 2>/dev/null || true"],
                _ignore_errors=True,
            )

            # Verify result
            assert result is True

    def test_bsm_setup_non_freebsd(self):
        """
        Test bsm_setup function raises error on non-FreeBSD systems.
        """
        with patch("pyinfra.context.state", MagicMock(config=MagicMock())), patch(
            "pyinfra.context.host", MagicMock()
        ), patch("infraninja.security.freebsd.bsm_setup.host") as mock_host:
            # Configure host.get_fact to return a non-FreeBSD distro
            mock_host.get_fact.return_value = {
                "name": "Ubuntu",
                "release_meta": {"ID": "ubuntu"},
            }

            # Mock the decorator
            with patch(
                "pyinfra.api.deploy.deploy", lambda *args, **kwargs: lambda func: func
            ):
                # Verify bsm_setup raises ValueError for non-FreeBSD OS
                with self.assertRaises(ValueError) as context:
                    bsm_setup()

                self.assertIn(
                    "This deployment is designed for FreeBSD systems only",
                    str(context.exception),
                )

    def test_bsm_setup_no_distro_info(self):
        """
        Test bsm_setup function with no distribution information.
        """
        with patch("pyinfra.context.state", MagicMock(config=MagicMock())), patch(
            "pyinfra.context.host", MagicMock()
        ), patch("infraninja.security.freebsd.bsm_setup.host") as mock_host:
            # Configure host.get_fact to return None
            mock_host.get_fact.return_value = None

            # Mock the decorator
            with patch(
                "pyinfra.api.deploy.deploy", lambda *args, **kwargs: lambda func: func
            ):
                # Verify bsm_setup raises ValueError when no distro info
                with self.assertRaises(ValueError) as context:
                    bsm_setup()

                self.assertIn(
                    "This deployment is designed for FreeBSD systems only",
                    str(context.exception),
                )


if __name__ == "__main__":
    unittest.main()
