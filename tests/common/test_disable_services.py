import pytest
from unittest.mock import patch, MagicMock

from infraninja.security.common.disable_services import ServiceDisabler

# Test cases for different init systems
INIT_SYSTEM_TEST_CASES = [
    {
        "name": "debian_systemd",
        "distro_info": {
            "name": "Ubuntu",
            "release_meta": {"ID": "ubuntu", "ID_LIKE": "debian"},
        },
        "init_system": "systemctl",
        "expected_service_op": "server.service",
    },
    {
        "name": "alpine_openrc",
        "distro_info": {
            "name": "Alpine Linux",
            "release_meta": {"ID": "alpine", "ID_LIKE": ""},
        },
        "init_system": None,  # Will be detected as Alpine directly
        "expected_service_op": "server.service",
    },
    {
        "name": "rhel_systemd",
        "distro_info": {
            "name": "CentOS Linux",
            "release_meta": {"ID": "centos", "ID_LIKE": "rhel fedora"},
        },
        "init_system": None,  # Will be detected as RHEL directly
        "expected_service_op": "server.service",
    },
    {
        "name": "arch_systemd",
        "distro_info": {
            "name": "Arch Linux",
            "release_meta": {"ID": "arch", "ID_LIKE": ""},
        },
        "init_system": None,  # Will be detected as Arch directly
        "expected_service_op": "server.service",
    },
    {
        "name": "void_runit",
        "distro_info": {
            "name": "Void Linux",
            "release_meta": {"ID": "void", "ID_LIKE": ""},
        },
        "init_system": None,  # Will be detected as Void directly
        "expected_service_op": "server.service",
    },
    {
        "name": "generic_systemd",
        "distro_info": {
            "name": "Unknown",
            "release_meta": {"ID": "unknown", "ID_LIKE": ""},
        },
        "init_system": "systemctl",
        "expected_service_op": "server.service",
    },
    {
        "name": "generic_openrc",
        "distro_info": {
            "name": "Unknown",
            "release_meta": {"ID": "unknown", "ID_LIKE": ""},
        },
        "init_system": "rc-service",
        "expected_service_op": "server.service",
    },
    {
        "name": "generic_runit",
        "distro_info": {
            "name": "Unknown",
            "release_meta": {"ID": "unknown", "ID_LIKE": ""},
        },
        "init_system": "sv",
        "expected_service_op": "server.service",
    },
    {
        "name": "generic_sysvinit",
        "distro_info": {
            "name": "Unknown",
            "release_meta": {"ID": "unknown", "ID_LIKE": ""},
        },
        "init_system": "service",
        "expected_service_op": "server.service",
    },
    {
        "name": "generic_fallback",
        "distro_info": {
            "name": "Unknown",
            "release_meta": {"ID": "unknown", "ID_LIKE": ""},
        },
        "init_system": None,  # No init system detected
        "expected_service_op": "server.service",
    },
]


@pytest.mark.parametrize("test_case", INIT_SYSTEM_TEST_CASES)
def test_service_disabler_init_systems(test_case):
    """
    Test ServiceDisabler across different init systems and distros.
    """

    # Configure init system detection
    def which_side_effect(fact, command=None, **kwargs):
        if command == test_case.get("init_system"):
            return True
        return False

    # Setup mocks for all the functions we need
    with patch("pyinfra.context.state", MagicMock(config=MagicMock())), patch(
        "pyinfra.context.host", MagicMock()
    ), patch("infraninja.security.common.disable_services.host") as mock_host, patch(
        "infraninja.security.common.disable_services.server"
    ) as mock_server:
        # Configure host.get_fact to return the distro info or which command status
        mock_host.get_fact.side_effect = lambda fact, **kwargs: (
            test_case["distro_info"]
            if fact.__name__ == "LinuxDistribution"
            else which_side_effect(fact, **kwargs)
        )

        mock_host.noop = MagicMock()  # Mock host.noop

        # Create a map of service operations to their mocks
        service_ops = {
            "server.service": mock_server.service,
        }

        # Create the service disabler instance
        disabler = ServiceDisabler()

        # Patch the deploy decorator to make it a no-op and call the method
        with patch("pyinfra.api.deploy", lambda *args, **kwargs: lambda func: func):
            # This calls the function directly without decoration
            disabler.deploy()

        # Get the expected operation and check it was called
        expected_op = service_ops[test_case["expected_service_op"]]

        # For all cases, verify that server.service was called
        assert expected_op.called, (
            f"Expected {test_case['expected_service_op']} to be called"
        )

        # For all test cases, verify that the appropriate service operation was called
        # for each of the default services
        call_count = 0
        for service in ServiceDisabler.DEFAULT_SERVICES:
            for call_args in expected_op.call_args_list:
                if service in str(call_args):
                    call_count += 1
                    break

        # Make sure several services were processed
        assert call_count > 0, (
            f"No services were processed with {test_case['expected_service_op']}"
        )


def test_service_disabler_custom_services():
    """
    Test ServiceDisabler with custom service list.
    """
    custom_services = ["custom-service1", "custom-service2", "custom-service3"]

    # Setup mocks
    with patch("pyinfra.context.state", MagicMock(config=MagicMock())), patch(
        "pyinfra.context.host", MagicMock()
    ), patch("infraninja.security.common.disable_services.host") as mock_host, patch(
        "infraninja.security.common.disable_services.server"
    ) as mock_server:
        # Configure host.get_fact to return systemd for init system
        mock_host.get_fact.side_effect = lambda fact, **kwargs: (
            {"name": "Ubuntu", "release_meta": {"ID": "ubuntu", "ID_LIKE": "debian"}}
            if fact.__name__ == "LinuxDistribution"
            else True
            if kwargs.get("command") == "systemctl"
            else False
        )

        mock_host.noop = MagicMock()  # Mock host.noop

        # Create the service disabler instance with custom services
        disabler = ServiceDisabler(services=custom_services)

        # Patch the deploy decorator to make it a no-op and call the method
        with patch("pyinfra.api.deploy", lambda *args, **kwargs: lambda func: func):
            # This calls the function directly without decoration
            disabler.deploy()

        # Verify that server.service was called for each custom service
        for service in custom_services:
            service_call_found = False
            for call_args in mock_server.service.call_args_list:
                if service in str(call_args):
                    service_call_found = True
                    break
            assert service_call_found, (
                f"Expected server.service to be called for {service}"
            )

        # Verify that none of the default services were processed
        for service in ServiceDisabler.DEFAULT_SERVICES:
            if service in custom_services:
                continue  # Skip if service is in both lists

            default_service_call_found = False
            for call_args in mock_server.service.call_args_list:
                if service in str(call_args):
                    default_service_call_found = True
                    break
            assert not default_service_call_found, (
                f"Default service {service} should not have been processed"
            )
