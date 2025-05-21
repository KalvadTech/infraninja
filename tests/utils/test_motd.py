import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

# Import the module to test
from infraninja.utils.motd import motd


class TestMOTD:
    """Tests for the MOTD utility."""

    @pytest.fixture
    def mock_host(self):
        """Fixture to mock pyinfra host."""
        with patch("infraninja.utils.motd.host") as mock_host:
            # Setup hostname fact
            mock_host.get_fact.side_effect = lambda fact, *args, **kwargs: (
                "test-server"
                if fact.__name__ == "Hostname"
                else "Jan 01 12:34:56 2025"
                if fact.__name__ == "Command"
                else None
            )
            yield mock_host

    @pytest.fixture
    def mock_files_op(self):
        """Fixture to mock pyinfra files operations."""
        with patch("infraninja.utils.motd.files") as mock_files:
            yield mock_files

    @pytest.fixture
    def mock_pyinfra_context(self):
        """Fixture to mock pyinfra context."""
        # Create State mock with config attribute
        state_mock = MagicMock()
        state_mock.config = MagicMock()
        host_mock = MagicMock()

        with patch("pyinfra.context.state", state_mock), patch(
            "pyinfra.context.host", host_mock
        ):
            yield

    @pytest.fixture
    def mock_deploy_decorator(self):
        """Fixture to mock the deploy decorator."""

        def mock_deploy(*args, **kwargs):
            def decorator(func):
                def wrapper(*fargs, **fkwargs):
                    return func(*fargs, **fkwargs)

                return wrapper

            return decorator

        with patch("infraninja.utils.motd.deploy", mock_deploy):
            yield

    @pytest.fixture
    def mock_template_path(self):
        """Fixture to mock finding the template path."""
        mock_path = MagicMock(spec=Path)
        mock_path_instance = MagicMock(spec=Path)
        mock_path.joinpath.return_value = mock_path_instance
        mock_path_instance.__str__.return_value = "/mock/path/to/templates/motd.j2"

        with patch("infraninja.utils.motd.resource_files", return_value=mock_path):
            yield mock_path

    @staticmethod
    def test_motd_creation(
        mock_host,
        mock_files_op,
        mock_deploy_decorator,
        mock_template_path,
        mock_pyinfra_context,
    ):
        """Test the MOTD creation function."""
        # Call the function
        motd()

        # Verify hostname fact was retrieved
        mock_host.get_fact.assert_any_call(
            pytest.importorskip("pyinfra.facts.server").Hostname
        )

        # Verify last login command fact was retrieved
        command_fact = pytest.importorskip("pyinfra.facts.server").Command
        last_access_cmd = (
            "last -n 1 | grep -v 'reboot' | head -n 1 | awk '{print $4,$5,$6,$7}'"
        )
        mock_host.get_fact.assert_any_call(command_fact, last_access_cmd)

        # Verify template was fetched using importlib.resources
        mock_template_path.joinpath.assert_called_once_with("motd.j2")

        # Verify files.template was called with correct arguments
        mock_files_op.template.assert_called_once_with(
            name="Deploy MOTD file",
            src="/mock/path/to/templates/motd.j2",
            dest="/etc/motd",
            hostname="test-server",
            last_login="Jan 01 12:34:56 2025",
        )

    @staticmethod
    def test_motd_without_last_login(
        mock_host,
        mock_files_op,
        mock_deploy_decorator,
        mock_template_path,
        mock_pyinfra_context,
    ):
        """Test MOTD creation when there's no last login info."""
        # Modify mock_host to return None for Command fact
        mock_host.get_fact.side_effect = lambda fact, *args, **kwargs: (
            "test-server" if fact.__name__ == "Hostname" else None
        )

        # Call the function
        motd()

        # Verify template was called with correct arguments including None for last_login
        mock_files_op.template.assert_called_once_with(
            name="Deploy MOTD file",
            src="/mock/path/to/templates/motd.j2",
            dest="/etc/motd",
            hostname="test-server",
            last_login=None,
        )

    @staticmethod
    def test_motd_error_handling(
        mock_host,
        mock_files_op,
        mock_deploy_decorator,
        mock_template_path,
        mock_pyinfra_context,
    ):
        """Test error handling in MOTD creation."""
        # Setup mock to raise an exception
        mock_files_op.template.side_effect = Exception("Template error")

        with pytest.raises(Exception, match="Template error"):
            motd()
