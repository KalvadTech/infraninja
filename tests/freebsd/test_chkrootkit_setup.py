#!/usr/bin/env python3
# tests/freebsd/test_chkrootkit_setup.py

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from infraninja.security.freebsd.chkrootkit_setup import chkrootkit_setup


class TestFreeBSDChkrootkitSetup(unittest.TestCase):
    """Test cases for the FreeBSD chkrootkit setup function."""

    def test_chkrootkit_setup_success(self):
        """
        Test chkrootkit_setup function with successful execution on FreeBSD.
        """
        with patch("pyinfra.context.state", MagicMock(config=MagicMock())), patch(
            "pyinfra.context.host", MagicMock()
        ), patch(
            "infraninja.security.freebsd.chkrootkit_setup.host"
        ) as mock_host, patch(
            "infraninja.security.freebsd.chkrootkit_setup.files"
        ) as mock_files, patch(
            "infraninja.security.freebsd.chkrootkit_setup.crontab"
        ) as mock_crontab, patch(
            "infraninja.security.freebsd.chkrootkit_setup.service"
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
                # Run the chkrootkit_setup function
                result = chkrootkit_setup()

            # Verify scan script template was uploaded
            mock_files.template.assert_any_call(
                name="Upload FreeBSD chkrootkit scan script",
                src=str(
                    Path(__file__).parent.parent.parent
                    / "infraninja"
                    / "security"
                    / "templates"
                    / "freebsd"
                    / "chkrootkit_scan_script.j2"
                ),
                dest="/usr/local/bin/run_chkrootkit_scan",
                mode="755",
                user="root",
                group="wheel",
            )

            # Verify log directory was created
            mock_files.directory.assert_any_call(
                name="Create chkrootkit log directory",
                path="/var/log/chkrootkit",
                present=True,
                mode="755",
                user="root",
                group="wheel",
            )

            # Verify newsyslog configuration
            mock_files.template.assert_any_call(
                name="Upload chkrootkit newsyslog configuration",
                src=str(
                    Path(__file__).parent.parent.parent
                    / "infraninja"
                    / "security"
                    / "templates"
                    / "freebsd"
                    / "chkrootkit_newsyslog.conf.j2"
                ),
                dest="/etc/newsyslog.conf.d/chkrootkit.conf",
                create_remote_dir=True,
            )

            # Verify cron job was added using crontab operation
            mock_crontab.crontab.assert_any_call(
                name="Add chkrootkit weekly cron job",
                command="/usr/local/bin/run_chkrootkit_scan",
                user="root",
                day_of_week="0",
                hour="2",
                minute="0",
            )

            # Verify cron was enabled in rc.conf
            mock_files.line.assert_any_call(
                name="Enable cron in rc.conf",
                path="/etc/rc.conf",
                line='cron_enable="YES"',
                present=True,
            )

            # Verify cron service restart using FreeBSD service operation
            mock_service.service.assert_any_call(
                name="Restart cron service",
                srvname="cron",
                srvstate="restarted",
            )

            # Verify initial log file creation
            mock_files.file.assert_any_call(
                name="Create initial chkrootkit log file",
                path="/var/log/chkrootkit/chkrootkit.log",
                present=True,
                mode="644",
                user="root",
                group="wheel",
            )

            # Verify result
            assert result is True

    def test_chkrootkit_setup_non_freebsd(self):
        """
        Test chkrootkit_setup function raises error on non-FreeBSD systems.
        """
        with patch("pyinfra.context.state", MagicMock(config=MagicMock())), patch(
            "pyinfra.context.host", MagicMock()
        ), patch("infraninja.security.freebsd.chkrootkit_setup.host") as mock_host:
            # Configure host.get_fact to return a non-FreeBSD distro
            mock_host.get_fact.return_value = {
                "name": "Ubuntu",
                "release_meta": {"ID": "ubuntu"},
            }

            # Mock the decorator
            with patch(
                "pyinfra.api.deploy.deploy", lambda *args, **kwargs: lambda func: func
            ):
                # Verify chkrootkit_setup raises ValueError for non-FreeBSD OS
                with self.assertRaises(ValueError) as context:
                    chkrootkit_setup()

                self.assertIn(
                    "This deployment is designed for FreeBSD systems only",
                    str(context.exception),
                )


if __name__ == "__main__":
    unittest.main()
