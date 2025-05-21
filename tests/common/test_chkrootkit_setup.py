from unittest.mock import patch, MagicMock
import pytest
from pathlib import Path

from infraninja.security.common.chkrootkit_setup import chkrootkit_setup


class TestChkrootkitSetup:
    """Tests for the chkrootkit_setup function."""

    @pytest.fixture
    def mock_files(self):
        """Fixture to mock pyinfra files operations."""
        with patch("infraninja.security.common.chkrootkit_setup.files") as mock_files:
            yield mock_files

    @pytest.fixture
    def mock_server(self):
        """Fixture to mock pyinfra server operations."""
        with patch(
            "infraninja.security.common.chkrootkit_setup.crontab"
        ) as mock_server:
            yield mock_server

    @pytest.fixture
    def mock_resource_files(self):
        """Fixture to mock importlib.resources files function."""
        mock_path = MagicMock(spec=Path)
        mock_script_path = MagicMock(spec=Path)
        mock_logrotate_path = MagicMock(spec=Path)

        # Configure mock path for the template directory
        mock_path.joinpath.side_effect = (
            lambda path: mock_script_path
            if path == "chkrootkit_scan_script.j2"
            else mock_logrotate_path
        )

        # Set string representations for the paths
        mock_script_path.__str__.return_value = (
            "/mock/path/to/templates/ubuntu/chkrootkit_scan_script.j2"
        )
        mock_logrotate_path.__str__.return_value = (
            "/mock/path/to/templates/ubuntu/chkrootkit_logrotate.j2"
        )

        with patch(
            "infraninja.security.common.chkrootkit_setup.resource_files",
            return_value=mock_path,
        ):
            yield mock_path

    @pytest.fixture
    def mock_pyinfra_context(self):
        """Fixture to mock pyinfra context."""
        with patch("pyinfra.context.state", MagicMock(config=MagicMock())), patch(
            "pyinfra.context.host", MagicMock()
        ):
            yield

    @pytest.fixture
    def mock_deploy_decorator(self):
        """Fixture to mock the deploy decorator."""
        with patch(
            "infraninja.security.common.chkrootkit_setup.deploy",
            lambda *args, **kwargs: lambda func: func,
        ):
            yield

    @staticmethod
    def test_chkrootkit_setup(
        mock_files,
        mock_server,
        mock_resource_files,
        mock_pyinfra_context,
        mock_deploy_decorator,
    ):
        """Test chkrootkit_setup function executes all expected operations."""
        # Call the function
        chkrootkit_setup()

        # Verify resource_files was called with the right template directory
        mock_resource_files.joinpath.assert_any_call("chkrootkit_scan_script.j2")
        mock_resource_files.joinpath.assert_any_call("chkrootkit_logrotate.j2")

        # Verify the scan script template was uploaded
        mock_files.template.assert_any_call(
            name="Upload chkrootkit scan script",
            src="/mock/path/to/templates/ubuntu/chkrootkit_scan_script.j2",
            dest="/usr/local/bin/run_chkrootkit_scan",
            mode="755",
        )

        # Verify the cron job was added
        mock_server.crontab.assert_called_once_with(
            name="Add chkrootkit cron job for weekly scans",
            command="/usr/local/bin/run_chkrootkit_scan",
            user="root",
            day_of_week="0",
            hour="2",
            minute="0",
        )

        # Verify the log directory was created
        mock_files.directory.assert_called_once_with(
            name="Create chkrootkit log directory",
            path="/var/log/chkrootkit",
            present=True,
        )

        # Verify the logrotate config was uploaded
        mock_files.template.assert_any_call(
            name="Upload chkrootkit logrotate configuration",
            src="/mock/path/to/templates/ubuntu/chkrootkit_logrotate.j2",
            dest="/etc/logrotate.d/chkrootkit",
        )

    @staticmethod
    def test_files_template_order(
        mock_files,
        mock_server,
        mock_resource_files,
        mock_pyinfra_context,
        mock_deploy_decorator,
    ):
        """Test that files.template is called in the expected order."""
        # Call the function
        chkrootkit_setup()

        # Verify files.template call order
        expected_calls = [
            {
                "name": "Upload chkrootkit scan script",
                "src": "/mock/path/to/templates/ubuntu/chkrootkit_scan_script.j2",
                "dest": "/usr/local/bin/run_chkrootkit_scan",
                "mode": "755",
            },
            {
                "name": "Upload chkrootkit logrotate configuration",
                "src": "/mock/path/to/templates/ubuntu/chkrootkit_logrotate.j2",
                "dest": "/etc/logrotate.d/chkrootkit",
            },
        ]

        # Check that files.template was called exactly twice
        assert mock_files.template.call_count == 2

        # Extract the actual calls
        actual_calls = [call.kwargs for call in mock_files.template.call_args_list]

        # Check that the actual calls match the expected calls
        for expected, actual in zip(expected_calls, actual_calls):
            for key, value in expected.items():
                assert actual[key] == value

    @staticmethod
    def test_correct_template_paths_used(
        mock_files,
        mock_server,
        mock_resource_files,
        mock_pyinfra_context,
        mock_deploy_decorator,
    ):
        """Test that the correct template paths are used."""
        # Call the function
        chkrootkit_setup()

        # Get the template paths that were used
        script_path_call = None
        logrotate_path_call = None

        for call in mock_files.template.call_args_list:
            if call.kwargs["name"] == "Upload chkrootkit scan script":
                script_path_call = call.kwargs["src"]
            elif call.kwargs["name"] == "Upload chkrootkit logrotate configuration":
                logrotate_path_call = call.kwargs["src"]

        # Check that we got both template paths
        assert script_path_call is not None, "Script template path not found in calls"
        assert logrotate_path_call is not None, (
            "Logrotate template path not found in calls"
        )

        # Check that the script path resolves to expected template (mocked)
        assert (
            script_path_call
            == "/mock/path/to/templates/ubuntu/chkrootkit_scan_script.j2"
        )

        # Check that the logrotate path resolves to expected template (mocked)
        assert (
            logrotate_path_call
            == "/mock/path/to/templates/ubuntu/chkrootkit_logrotate.j2"
        )
