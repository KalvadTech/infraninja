from unittest.mock import MagicMock, patch

import pytest

from infraninja.security.freebsd.disable_services import FreeBSDServiceDisabler


def test_freebsd_service_disabler_default_services():
    """
    Test FreeBSDServiceDisabler with default services list.
    """
    with patch("pyinfra.context.state", MagicMock(config=MagicMock())), patch(
        "pyinfra.context.host", MagicMock()
    ), patch("infraninja.security.freebsd.disable_services.host") as mock_host, patch(
        "infraninja.security.freebsd.disable_services.service"
    ) as mock_service:
        # Create service disabler with default services
        disabler = FreeBSDServiceDisabler()

        # Mock the deploy decorator to make it a no-op
        with patch(
            "pyinfra.api.deploy.deploy", lambda *args, **kwargs: lambda func: func
        ):
            result = disabler.deploy()

        # Verify the method returns True
        assert result is True

        # Verify host.noop was called with the main message
        mock_host.noop.assert_any_call("Disabling services on FreeBSD")

        # Verify service.service was called for each default service
        expected_services = [
            "avahi_daemon",
            "cupsd",
            "bluetooth",
            "rpcbind",
            "vsftpd",
            "telnetd",
            "sendmail",
        ]

        assert mock_service.service.call_count == len(expected_services)

        # Check that each service was called with correct parameters
        service_calls = [call[1] for call in mock_service.service.call_args_list]
        called_services = [call["srvname"] for call in service_calls]

        for service_name in expected_services:
            assert service_name in called_services

        # Verify all services were called with "stopped" state and ignore_errors=True
        for call in service_calls:
            assert call["srvstate"] == "stopped"
            assert call["_ignore_errors"] is True

        # Verify host.noop was called for each service
        noop_calls = [call[0][0] for call in mock_host.noop.call_args_list]
        for service_name in expected_services:
            expected_message = f"Disabled service: {service_name} on FreeBSD"
            assert expected_message in noop_calls


def test_freebsd_service_disabler_custom_services():
    """
    Test FreeBSDServiceDisabler with custom services list.
    """
    custom_services = ["apache24", "mysql-server", "redis"]

    with patch("pyinfra.context.state", MagicMock(config=MagicMock())), patch(
        "pyinfra.context.host", MagicMock()
    ), patch("infraninja.security.freebsd.disable_services.host"), patch(
        "infraninja.security.freebsd.disable_services.service"
    ) as mock_service:
        # Create service disabler with custom services
        disabler = FreeBSDServiceDisabler(services=custom_services)

        # Mock the deploy decorator
        with patch(
            "pyinfra.api.deploy.deploy", lambda *args, **kwargs: lambda func: func
        ):
            result = disabler.deploy()

        # Verify the method returns True
        assert result is True

        # Verify service.service was called for each custom service
        assert mock_service.service.call_count == len(custom_services)

        # Check that each custom service was called with correct parameters
        service_calls = [call[1] for call in mock_service.service.call_args_list]
        called_services = [call["srvname"] for call in service_calls]

        for service_name in custom_services:
            assert service_name in called_services

        # Verify all services were called with "stopped" state and ignore_errors=True
        for call in service_calls:
            assert call["srvstate"] == "stopped"
            assert call["_ignore_errors"] is True


def test_freebsd_service_disabler_empty_services():
    """
    Test FreeBSDServiceDisabler with empty services list.
    """
    with patch("pyinfra.context.state", MagicMock(config=MagicMock())), patch(
        "pyinfra.context.host", MagicMock()
    ), patch("infraninja.security.freebsd.disable_services.host") as mock_host, patch(
        "infraninja.security.freebsd.disable_services.service"
    ) as mock_service:
        # Mock host.noop to avoid parameter issues
        mock_host.noop = MagicMock()

        # Create service disabler with empty services list
        disabler = FreeBSDServiceDisabler(services=[])

        # Mock the deploy decorator
        with patch(
            "pyinfra.api.deploy.deploy", lambda *args, **kwargs: lambda func: func
        ):
            result = disabler.deploy()

        # Verify the method returns True
        assert result is True

        # Verify host.noop was called with the main message
        mock_host.noop.assert_any_call("Disabling services on FreeBSD")

        # Verify no service operations were called since list is empty
        assert mock_service.service.call_count == 0


def test_freebsd_service_disabler_none_services_uses_default():
    """
    Test FreeBSDServiceDisabler with None services (should use default).
    """
    with patch("pyinfra.context.state", MagicMock(config=MagicMock())), patch(
        "pyinfra.context.host", MagicMock()
    ), patch("infraninja.security.freebsd.disable_services.host"), patch(
        "infraninja.security.freebsd.disable_services.service"
    ) as mock_service:
        # Create service disabler with None services (should use default)
        disabler = FreeBSDServiceDisabler(services=None)

        # Mock the deploy decorator
        with patch(
            "pyinfra.api.deploy.deploy", lambda *args, **kwargs: lambda func: func
        ):
            result = disabler.deploy()

        # Verify the method returns True
        assert result is True

        # Verify service.service was called for each default service
        expected_default_count = len(FreeBSDServiceDisabler.DEFAULT_SERVICES)
        assert mock_service.service.call_count == expected_default_count


def test_freebsd_service_disabler_service_call_parameters():
    """
    Test that service operations are called with correct parameters.
    """
    test_services = ["testservice1", "testservice2"]

    with patch("pyinfra.context.state", MagicMock(config=MagicMock())), patch(
        "pyinfra.context.host", MagicMock()
    ), patch("infraninja.security.freebsd.disable_services.host"), patch(
        "infraninja.security.freebsd.disable_services.service"
    ) as mock_service:
        # Create service disabler
        disabler = FreeBSDServiceDisabler(services=test_services)

        # Mock the deploy decorator
        with patch(
            "pyinfra.api.deploy.deploy", lambda *args, **kwargs: lambda func: func
        ):
            disabler.deploy()

        # Verify each service call has correct parameters
        service_calls = mock_service.service.call_args_list

        for i, service_name in enumerate(test_services):
            call_args, call_kwargs = service_calls[i]
            assert call_kwargs["srvname"] == service_name
            assert call_kwargs["srvstate"] == "stopped"
            assert call_kwargs["_ignore_errors"] is True


def test_freebsd_service_disabler_default_services_list():
    """
    Test that the default services list contains expected services.
    """
    expected_default_services = [
        "avahi_daemon",
        "cupsd",
        "bluetooth",
        "rpcbind",
        "vsftpd",
        "telnetd",
        "sendmail",
    ]

    # Verify the default services list matches expectations
    assert FreeBSDServiceDisabler.DEFAULT_SERVICES == expected_default_services


def test_freebsd_service_disabler_services_independence():
    """
    Test that modifying services in one instance doesn't affect another.
    """
    # Create first instance and modify its services
    disabler1 = FreeBSDServiceDisabler()
    original_services = disabler1.services.copy()
    disabler1.services.append("custom_service")

    # Create second instance
    disabler2 = FreeBSDServiceDisabler()

    # Verify second instance has unmodified default services
    assert disabler2.services == original_services
    assert "custom_service" not in disabler2.services


@pytest.mark.parametrize(
    "services_input,expected_count",
    [
        (None, 7),  # Default services count
        ([], 0),  # Empty list
        (["single_service"], 1),  # Single service
        (["service1", "service2", "service3"], 3),  # Multiple services
        (FreeBSDServiceDisabler.DEFAULT_SERVICES, 7),  # Explicit default list
    ],
)
def test_freebsd_service_disabler_service_count(services_input, expected_count):
    """
    Test FreeBSDServiceDisabler with various service list inputs.
    """
    with patch("pyinfra.context.state", MagicMock(config=MagicMock())), patch(
        "pyinfra.context.host", MagicMock()
    ), patch(
        "infraninja.security.freebsd.disable_services.service"
    ) as mock_service, patch(
        "infraninja.security.freebsd.disable_services.host"
    ) as mock_host:
        # Mock host.noop to avoid parameter issues
        mock_host.noop = MagicMock()

        # Create service disabler
        disabler = FreeBSDServiceDisabler(services=services_input)

        # Mock the deploy decorator
        with patch(
            "pyinfra.api.deploy.deploy", lambda *args, **kwargs: lambda func: func
        ):
            disabler.deploy()

        # Verify correct number of service calls
        assert mock_service.service.call_count == expected_count


def test_freebsd_service_disabler_deploy_decorator_usage():
    """
    Test that the deploy decorator is used correctly for each service.
    """
    test_services = ["test1", "test2"]

    with patch("pyinfra.context.state", MagicMock(config=MagicMock())), patch(
        "pyinfra.context.host", MagicMock()
    ), patch("infraninja.security.freebsd.disable_services.service"), patch(
        "infraninja.security.freebsd.disable_services.host"
    ) as mock_host:
        # Mock host.noop to avoid parameter issues
        mock_host.noop = MagicMock()

        # Track deploy decorator calls
        deploy_calls = []

        def mock_deploy(name):
            deploy_calls.append(name)
            return lambda func: func

        with patch("infraninja.security.freebsd.disable_services.deploy", mock_deploy):
            # Create service disabler
            disabler = FreeBSDServiceDisabler(services=test_services)

            # Call deploy
            disabler.deploy()

        # Verify deploy decorator was called for each service
        for service_name in test_services:
            expected_name = f"Disable unwanted/common service: {service_name}"
            assert expected_name in deploy_calls


def test_freebsd_service_disabler_host_noop_calls():
    """
    Test that host.noop is called with correct messages.
    """
    test_services = ["testservice"]

    with patch("pyinfra.context.state", MagicMock(config=MagicMock())), patch(
        "pyinfra.context.host", MagicMock()
    ), patch("infraninja.security.freebsd.disable_services.host") as mock_host, patch(
        "infraninja.security.freebsd.disable_services.service"
    ):
        # Mock host.noop to avoid parameter issues
        mock_host.noop = MagicMock()

        # Create service disabler
        disabler = FreeBSDServiceDisabler(services=test_services)

        # Mock the deploy decorator
        with patch(
            "pyinfra.api.deploy.deploy", lambda *args, **kwargs: lambda func: func
        ):
            disabler.deploy()

        # Verify host.noop calls
        noop_calls = [call[0][0] for call in mock_host.noop.call_args_list]

        # Should have main message and one per service
        assert "Disabling services on FreeBSD" in noop_calls
        assert "Disabled service: testservice on FreeBSD" in noop_calls
