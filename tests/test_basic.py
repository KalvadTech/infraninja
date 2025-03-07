"""
Basic tests for the infraninja package.
"""

from infraninja import __version__


def test_version():
    """Test that version string is present"""
    assert isinstance(__version__, str)
    assert len(__version__) > 0


def test_sample_config_fixture(sample_config):
    """Test the sample_config fixture"""
    assert isinstance(sample_config, dict)
    assert "host" in sample_config
    assert "port" in sample_config
    assert sample_config["port"] == 22


def test_temp_directory(temp_directory):
    """Test the temp_directory fixture"""
    assert temp_directory.exists()
    assert temp_directory.is_dir()

    # Example of using the temp directory
    test_file = temp_directory / "test.txt"
    test_file.write_text("Hello, World!")
    assert test_file.read_text() == "Hello, World!"
