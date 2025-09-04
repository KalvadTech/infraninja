#!/usr/bin/env python3
# tests/freebsd/test_rkhunter_setup.py

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from infraninja.security.freebsd.rkhunter_setup import rkhunter_setup


class TestFreeBSDRkhunterSetup(unittest.TestCase):
    """Test cases for the FreeBSD rkhunter setup function."""

    def test_rkhunter_setup_success(self):
        """
        Test rkhunter_setup function with successful execution on FreeBSD.
        """
        with patch("pyinfra.context.state", MagicMock(config=MagicMock())), patch(
            "pyinfra.context.host", MagicMock()
        ), patch("infraninja.security.freebsd.rkhunter_setup.host") as mock_host, patch(
            "infraninja.security.freebsd.rkhunter_setup.files"
        ) as mock_files, patch(
            "infraninja.security.freebsd.rkhunter_setup.crontab"
        ) as mock_crontab, patch(
            "infraninja.security.freebsd.rkhunter_setup.server"
        ) as mock_server, patch(
            "infraninja.security.freebsd.rkhunter_setup.service"
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
                # Run the rkhunter_setup function
                result = rkhunter_setup()

            # Verify configuration directory was created
            mock_files.directory.assert_any_call(
                name="Create rkhunter configuration directory",
                path="/usr/local/etc/rkhunter",
                present=True,
                mode="755",
                user="root",
                group="wheel",
            )

            # Verify configuration template was uploaded
            mock_files.template.assert_any_call(
                name="Upload FreeBSD rkhunter configuration",
                src=str(
                    Path(__file__).parent.parent.parent
                    / "infraninja"
                    / "security"
                    / "templates"
                    / "freebsd"
                    / "rkhunter.conf.j2"
                ),
                dest="/usr/local/etc/rkhunter.conf",
                backup=True,
                mode="644",
                user="root",
                group="wheel",
            )

            # Verify log directory was created
            mock_files.directory.assert_any_call(
                name="Create rkhunter log directory",
                path="/var/log/rkhunter",
                present=True,
                mode="755",
                user="root",
                group="wheel",
            )

            # Verify secure temporary directory was created
            mock_files.directory.assert_any_call(
                name="Create rkhunter temporary directory",
                path="/var/tmp/rkhunter",
                present=True,
                mode="700",
                user="root",
                group="wheel",
            )

            # Verify database directory was created
            mock_files.directory.assert_any_call(
                name="Create rkhunter database directory",
                path="/var/lib/rkhunter/db",
                present=True,
                mode="755",
                user="root",
                group="wheel",
            )

            # Verify i18n directory was created
            mock_files.directory.assert_any_call(
                name="Create rkhunter i18n directory",
                path="/var/lib/rkhunter/db/i18n",
                present=True,
                mode="755",
                user="root",
                group="wheel",
            )

            # Verify scan script template was uploaded
            mock_files.template.assert_any_call(
                name="Upload FreeBSD rkhunter scan script",
                src=str(
                    Path(__file__).parent.parent.parent
                    / "infraninja"
                    / "security"
                    / "templates"
                    / "freebsd"
                    / "rkhunter_scan_script.j2"
                ),
                dest="/usr/local/bin/run_rkhunter_scan",
                mode="755",
                user="root",
                group="wheel",
            )

            # Verify cron job was added
            mock_crontab.crontab.assert_any_call(
                name="Add rkhunter daily cron job",
                command="/usr/local/bin/run_rkhunter_scan",
                user="root",
                hour="3",
                minute="0",
            )

            # Verify cron service restart
            mock_service.service.assert_any_call(
                name="Restart cron service",
                srvname="cron",
                srvstate="restarted",
            )

            # Verify database initialization
            mock_server.shell.assert_any_call(
                name="Initialize rkhunter database",
                commands=["/usr/local/bin/rkhunter --propupd"],
                _ignore_errors=True,
            )

            # Verify result
            assert result is True

    def test_rkhunter_setup_non_freebsd(self):
        """
        Test rkhunter_setup function raises error on non-FreeBSD systems.
        """
        with patch("pyinfra.context.state", MagicMock(config=MagicMock())), patch(
            "pyinfra.context.host", MagicMock()
        ), patch("infraninja.security.freebsd.rkhunter_setup.host") as mock_host:
            # Configure host.get_fact to return a non-FreeBSD distro
            mock_host.get_fact.return_value = {
                "name": "Ubuntu",
                "release_meta": {"ID": "ubuntu"},
            }

            # Mock the decorator
            with patch(
                "pyinfra.api.deploy.deploy", lambda *args, **kwargs: lambda func: func
            ):
                # Verify rkhunter_setup raises ValueError for non-FreeBSD OS
                with self.assertRaises(ValueError) as context:
                    rkhunter_setup()

                self.assertIn(
                    "This deployment is designed for FreeBSD systems only",
                    str(context.exception),
                )


if __name__ == "__main__":
    unittest.main()
