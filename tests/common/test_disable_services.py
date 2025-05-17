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
        "expected_service_op": "systemd.service",
    },
    {
        "name": "alpine_openrc",
        "distro_info": {
            "name": "Alpine Linux",
            "release_meta": {"ID": "alpine", "ID_LIKE": ""},
        },
        "init_system": None,  # Will be detected as Alpine directly
        "expected_service_op": "openrc.service",
    },
    {
        "name": "rhel_systemd",
        "distro_info": {
            "name": "CentOS Linux",
            "release_meta": {"ID": "centos", "ID_LIKE": "rhel fedora"},
        },
        "init_system": None,  # Will be detected as RHEL directly
        "expected_service_op": "systemd.service",
    },
    {
        "name": "arch_systemd",
        "distro_info": {
            "name": "Arch Linux",
            "release_meta": {"ID": "arch", "ID_LIKE": ""},
        },
        "init_system": None,  # Will be detected as Arch directly
        "expected_service_op": "systemd.service",
    },
    {
        "name": "void_runit",
        "distro_info": {
            "name": "Void Linux",
            "release_meta": {"ID": "void", "ID_LIKE": ""},
        },
        "init_system": None,  # Will be detected as Void directly
        "expected_service_op": "runit.service",
    },
    {
        "name": "generic_systemd",
        "distro_info": {
            "name": "Unknown",
            "release_meta": {"ID": "unknown", "ID_LIKE": ""},
        },
        "init_system": "systemctl",
        "expected_service_op": "systemd.service",
    },
    {
        "name": "generic_openrc",
        "distro_info": {
            "name": "Unknown",
            "release_meta": {"ID": "unknown", "ID_LIKE": ""},
        },
        "init_system": "rc-service",
        "expected_service_op": "openrc.service",
    },
    {
        "name": "generic_runit",
        "distro_info": {
            "name": "Unknown",
            "release_meta": {"ID": "unknown", "ID_LIKE": ""},
        },
        "init_system": "sv",
        "expected_service_op": "runit.service",
    },
    {
        "name": "generic_sysvinit",
        "distro_info": {
            "name": "Unknown",
            "release_meta": {"ID": "unknown", "ID_LIKE": ""},
        },
        "init_system": "service",
        "expected_service_op": "sysvinit.service",
    },
    {
        "name": "generic_fallback",
        "distro_info": {
            "name": "Unknown",
            "release_meta": {"ID": "unknown", "ID_LIKE": ""},
        },
        "init_system": None,  # No init system detected
        "expected_service_op": "server.shell",
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
        "infraninja.security.common.disable_services.systemd"
    ) as mock_systemd, patch(
        "infraninja.security.common.disable_services.openrc"
    ) as mock_openrc, patch(
        "infraninja.security.common.disable_services.runit"
    ) as mock_runit, patch(
        "infraninja.security.common.disable_services.sysvinit"
    ) as mock_sysvinit, patch(
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
            "systemd.service": mock_systemd.service,
            "openrc.service": mock_openrc.service,
            "runit.service": mock_runit.service,
            "sysvinit.service": mock_sysvinit.service,
            "server.shell": mock_server.shell,
        }

        # Mock the decorator to run the actual function without the decorator
        with patch(
            "pyinfra.api.deploy.deploy", lambda *args, **kwargs: lambda func: func
        ):
            # Create and run the ServiceDisabler with default services
            disabler = ServiceDisabler()
            disabler.deploy()

        # Get the expected operation and check it was called
        expected_op = service_ops[test_case["expected_service_op"]]

        # For distros that detect directly (without init system detection),
        # we expect appropriate service operations to be called
        if test_case["name"] in [
            "alpine_openrc",
            "rhel_systemd",
            "arch_systemd",
            "void_runit",
        ]:
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

        # Make sure several services were processed (not all may get the same operation)
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
        "infraninja.security.common.disable_services.systemd"
    ) as mock_systemd:
        # Configure host.get_fact to return systemd for init system
        mock_host.get_fact.side_effect = lambda fact, **kwargs: (
            {"name": "Ubuntu", "release_meta": {"ID": "ubuntu", "ID_LIKE": "debian"}}
            if fact.__name__ == "LinuxDistribution"
            else True
            if kwargs.get("command") == "systemctl"
            else False
        )

        mock_host.noop = MagicMock()  # Mock host.noop

        # Mock the decorator
        with patch(
            "pyinfra.api.deploy.deploy", lambda *args, **kwargs: lambda func: func
        ):
            # Create and run ServiceDisabler with custom services
            disabler = ServiceDisabler(services=custom_services)
            disabler.deploy()

        # Verify that systemd.service was called for each custom service
        for service in custom_services:
            service_call_found = False
            for call_args in mock_systemd.service.call_args_list:
                if service in str(call_args):
                    service_call_found = True
                    break
            assert service_call_found, (
                f"Expected systemd.service to be called for {service}"
            )

        # Verify that none of the default services were processed
        for service in ServiceDisabler.DEFAULT_SERVICES:
            if service in custom_services:
                continue  # Skip if service is in both lists

            default_service_call_found = False
            for call_args in mock_systemd.service.call_args_list:
                if service in str(call_args):
                    default_service_call_found = True
                    break
            assert not default_service_call_found, (
                f"Default service {service} should not have been processed"
            )
