#!/usr/bin/env python3
# tests/freebsd/test_lynis_setup.py

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from infraninja.security.freebsd.lynis_setup import lynis_setup


class TestFreeBSDLynisSetup(unittest.TestCase):
    """Test cases for the FreeBSD Lynis setup function."""

    def test_lynis_setup_success(self):
        """
        Test lynis_setup function with successful execution on FreeBSD.
        """
        with patch("pyinfra.context.state", MagicMock(config=MagicMock())), patch(
            "pyinfra.context.host", MagicMock()
        ), patch("infraninja.security.freebsd.lynis_setup.host") as mock_host, patch(
            "infraninja.security.freebsd.lynis_setup.files"
        ) as mock_files, patch(
            "infraninja.security.freebsd.lynis_setup.crontab"
        ) as mock_crontab, patch(
            "infraninja.security.freebsd.lynis_setup.server"
        ) as mock_server, patch(
            "infraninja.security.freebsd.lynis_setup.service"
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
                # Run the lynis_setup function
                result = lynis_setup()

            # Verify configuration directory was created
            mock_files.directory.assert_any_call(
                name="Create Lynis configuration directory",
                path="/usr/local/etc/lynis",
                present=True,
                mode="755",
                user="root",
                group="wheel",
            )

            # Verify configuration template was uploaded
            mock_files.template.assert_any_call(
                name="Upload FreeBSD Lynis configuration",
                src=str(
                    Path(__file__).parent.parent.parent
                    / "infraninja"
                    / "security"
                    / "templates"
                    / "freebsd"
                    / "lynis.prf.j2"
                ),
                dest="/usr/local/etc/lynis/default.prf",
                backup=True,
                mode="644",
                user="root",
                group="wheel",
            )

            # Verify log directory was created
            mock_files.directory.assert_any_call(
                name="Create Lynis log directory",
                path="/var/log/lynis",
                present=True,
                mode="755",
                user="root",
                group="wheel",
            )

            # Verify reports directory was created
            mock_files.directory.assert_any_call(
                name="Create Lynis reports directory",
                path="/var/log/lynis/reports",
                present=True,
                mode="755",
                user="root",
                group="wheel",
            )

            # Verify audit script template was uploaded
            mock_files.template.assert_any_call(
                name="Upload FreeBSD Lynis audit script",
                src=str(
                    Path(__file__).parent.parent.parent
                    / "infraninja"
                    / "security"
                    / "templates"
                    / "freebsd"
                    / "lynis_audit_script.j2"
                ),
                dest="/usr/local/bin/run_lynis_audit",
                mode="755",
                user="root",
                group="wheel",
            )

            # Verify cron job was added
            mock_crontab.crontab.assert_any_call(
                name="Add Lynis weekly audit cron job",
                command="/usr/local/bin/run_lynis_audit",
                user="root",
                day_of_week="0",
                hour="4",
                minute="0",
            )

            # Verify cron service restart
            mock_service.service.assert_any_call(
                name="Restart cron service",
                srvname="cron",
                srvstate="restarted",
            )

            # Verify database update
            mock_server.shell.assert_any_call(
                name="Update Lynis database",
                commands=["/usr/local/bin/lynis update info"],
                _ignore_errors=True,
            )

            # Verify result
            assert result is True

    def test_lynis_setup_non_freebsd(self):
        """
        Test lynis_setup function raises error on non-FreeBSD systems.
        """
        with patch("pyinfra.context.state", MagicMock(config=MagicMock())), patch(
            "pyinfra.context.host", MagicMock()
        ), patch("infraninja.security.freebsd.lynis_setup.host") as mock_host:
            # Configure host.get_fact to return a non-FreeBSD distro
            mock_host.get_fact.return_value = {
                "name": "Ubuntu",
                "release_meta": {"ID": "ubuntu"},
            }

            # Mock the decorator
            with patch(
                "pyinfra.api.deploy.deploy", lambda *args, **kwargs: lambda func: func
            ):
                # Verify lynis_setup raises ValueError for non-FreeBSD OS
                with self.assertRaises(ValueError) as context:
                    lynis_setup()

                self.assertIn(
                    "This deployment is designed for FreeBSD systems only",
                    str(context.exception),
                )


if __name__ == "__main__":
    unittest.main()
