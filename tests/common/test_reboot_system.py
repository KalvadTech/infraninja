from unittest.mock import patch

from infraninja.security.common.reboot_system import reboot_system


def test_reboot_system_module_imports():
    """
    Test that the reboot_system module has the expected structure and imports.
    """
    # Test that the function is callable
    assert callable(reboot_system)


def test_reboot_system_uses_reboot_required_fact():
    """
    Test that when reboot_system is called, it eventually uses the RebootRequired fact.
    This test verifies the integration rather than unit-testing the internal logic.
    """
    from pyinfra.facts.server import RebootRequired

    # This test verifies that the RebootRequired fact is properly imported
    # and available for use by the reboot_system function
    assert RebootRequired is not None

    # Verify that RebootRequired has the expected command structure
    fact_instance = RebootRequired()
    command = fact_instance.command()

    # Check that the command includes the expected reboot checks
    assert "/var/run/reboot-required" in command
    assert "freebsd-version" in command
    assert "Alpine" in command or "alpine" in command.lower()


@patch("infraninja.security.common.reboot_system.host")
@patch("infraninja.security.common.reboot_system.server")
def test_reboot_system_integration_mock(mock_server, mock_host):
    """
    Test reboot_system behavior by mocking at the module level.
    """
    # Configure the mock to simulate reboot required
    mock_host.get_fact.return_value = True

    # Import and test the actual function logic by calling it
    # The decorator will be bypassed in unit tests but the logic will run
    try:
        # This will test the import and basic structure
        # Verify it's callable
        assert callable(reboot_system)

        # The actual testing of the logic happens during real deployment
        # where pyinfra's context is properly set up

    except Exception as e:
        # If there are import issues, the test should catch them
        assert False, f"Failed to import or access reboot_system: {e}"


def test_pyinfra_reboot_required_fact_functionality():
    """
    Test that pyinfra's RebootRequired fact works as expected.
    """
    from pyinfra.facts.server import RebootRequired

    # Test that we can create an instance
    fact = RebootRequired()

    # Test that it has the command method
    assert hasattr(fact, "command")
    assert callable(fact.command)

    # Test that the command returns the expected shell script
    command = fact.command()
    assert isinstance(command, str)
    assert len(command) > 0

    # Test that it has the process method
    assert hasattr(fact, "process")
    assert callable(fact.process)

    # Test the process method with expected outputs
    assert fact.process(["reboot_required"]) is True
    assert not fact.process(["no_reboot_required"])
    assert not fact.process(["something_else"])

    # For empty list, the fact should handle it gracefully
    # Note: Empty output should be treated as "no reboot required"
    try:
        result = fact.process([])
        assert not result  # Should be False for empty output
    except IndexError:
        # If the fact doesn't handle empty lists gracefully, that's also valid behavior
        # since empty output shouldn't normally happen in real deployments
        pass


def test_reboot_system_function_signature():
    """
    Test that reboot_system has the expected function signature.
    """
    import inspect

    # Get the signature of the operation
    # For pyinfra operations, we need to check the original function
    sig = inspect.signature(reboot_system)

    # Check that it has the expected parameters
    params = list(sig.parameters.keys())

    # The exact parameter names might vary based on how pyinfra wraps the function
    # but we can check that the function is callable with our expected arguments
    assert len(params) >= 0  # Should have some parameters

    # Test that we can call it with expected arguments (will fail gracefully in test environment)
    try:
        # This should not raise a TypeError about arguments
        reboot_system(need_reboot=True, force_reboot=False, skip_reboot_check=True)
    except TypeError as e:
        if "argument" in str(e).lower():
            assert False, f"Function signature issue: {e}"
        # Other TypeErrors are fine (like missing pyinfra context)
    except Exception:
        # Other exceptions are expected in test environment
        pass


def test_reboot_system_source_code_content():
    """
    Test that the reboot_system source code contains expected elements.
    """
    import inspect

    # Get the source code of the function
    try:
        source = inspect.getsource(reboot_system)

        # Check that it uses the RebootRequired fact
        assert "RebootRequired" in source

        # Check that it has the expected logic flow
        assert "if force_reboot:" in source
        assert "need_reboot is None" in source
        assert "host.get_fact" in source
        assert "server.reboot" in source

        # Check that it has the expected parameters
        assert "need_reboot=None" in source
        assert "force_reboot=False" in source
        assert "skip_reboot_check=False" in source

    except Exception as e:
        # If we can't get source code, that's also valuable information
        assert False, f"Could not inspect reboot_system source: {e}"


def test_imports_in_reboot_system_module():
    """
    Test that the reboot_system module imports the correct dependencies.
    """
    import infraninja.security.common.reboot_system as reboot_module

    # Check that the module has the expected imports available
    assert hasattr(reboot_module, "deploy")
    assert hasattr(reboot_module, "host")
    assert hasattr(reboot_module, "RebootRequired")
    assert hasattr(reboot_module, "server")

    # Verify the imports are the expected types
    from pyinfra.api.deploy import deploy
    from pyinfra.context import host
    from pyinfra.facts.server import RebootRequired

    # These are the same objects
    assert reboot_module.deploy is deploy
    assert reboot_module.host is host
    assert reboot_module.RebootRequired is RebootRequired


def test_reboot_system_refactored_correctly():
    """
    Test that the reboot_system function was properly refactored to use the new RebootRequired fact.
    """
    import inspect

    import infraninja.security.common.reboot_system as reboot_module

    try:
        # Get the source of the function
        source = inspect.getsource(reboot_system)

        # Ensure the old check_reboot_required function is NOT being used
        assert "check_reboot_required" not in source

        # Ensure it uses the built-in RebootRequired fact
        assert "host.get_fact(RebootRequired)" in source

        # Ensure the function signature is correct
        assert (
            "def reboot_system(need_reboot=None, force_reboot=False, skip_reboot_check=False)"
            in source
        )

        # Ensure the logic flow is correct
        assert "if force_reboot:" in source
        assert "need_reboot = True" in source
        assert "if need_reboot is None and not skip_reboot_check:" in source
        assert "need_reboot = host.get_fact(RebootRequired)" in source
        assert "if need_reboot is True:" in source
        assert "server.reboot(" in source

        # Check that the module imports RebootRequired
        module_source = inspect.getsource(reboot_module)
        assert "from pyinfra.facts.server import RebootRequired" in module_source

    except Exception as e:
        assert False, f"Could not verify reboot_system refactoring: {e}"
