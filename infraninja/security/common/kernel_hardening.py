from pyinfra.api.deploy import deploy
from pyinfra.context import host
from pyinfra.facts.server import LinuxName
from pyinfra.operations import files, server


@deploy("Kernel Security Hardening")
def kernel_hardening():
    """
    Apply kernel security hardening configurations.

    Implements comprehensive kernel-level security hardening by configuring
    sysctl parameters for network security, memory protection, and system
    security. Creates persistent configuration that survives reboots.

    Security areas covered:
    - Network security (IP redirects, source routing, TCP cookies)
    - Memory protection (ASLR, minimum memory address)
    - Core dump restrictions
    - System security (SysRq, dmesg restrictions, kernel pointers)

    .. code:: python

        from infraninja.security.common.kernel_hardening import kernel_hardening
        kernel_hardening()

    :returns: True if kernel hardening completed successfully, False if some settings failed
    :rtype: bool
    """
    # Check if running on Linux
    linux_name = host.get_fact(LinuxName)

    if not linux_name:
        print("[ERROR] This script requires a Linux system")
        return False

    if linux_name.lower() == "freebsd":
        print("[Warning] This script is not compatible with FreeBSD, skipping.")
        return False

    # Verify sysctl is available
    if not server.shell(
        name="Check if sysctl exists",
        commands=["command -v sysctl"],
    ):
        print("[ERROR] sysctl command not found")
        return False

    # Create sysctl config directory if it doesn't exist
    files.directory(
        name="Ensure sysctl.d directory exists",
        path="/etc/sysctl.d",
        present=True,
    )

    # Kernel hardening configuration
    sysctl_config = {
        # Network Security
        "net.ipv4.conf.all.secure_redirects": "0",
        "net.ipv4.conf.default.secure_redirects": "0",
        "net.ipv4.conf.all.accept_source_route": "0",
        "net.ipv4.conf.default.accept_source_route": "0",
        "net.ipv4.conf.all.send_redirects": "0",
        "net.ipv4.conf.default.send_redirects": "0",
        "net.ipv4.icmp_echo_ignore_broadcasts": "1",
        "net.ipv4.tcp_syncookies": "1",
        "net.ipv4.tcp_max_syn_backlog": "2048",
        "net.ipv4.tcp_synack_retries": "2",
        "net.ipv4.tcp_syn_retries": "5",
        # Memory Protection
        "kernel.randomize_va_space": "2",
        "vm.mmap_min_addr": "65536",
        # Core Dumps
        "fs.suid_dumpable": "0",
        # System Security
        "kernel.sysrq": "0",
        "kernel.core_uses_pid": "1",
        "kernel.dmesg_restrict": "1",
        "kernel.kptr_restrict": "2",
    }

    # Apply sysctl settings with error handling
    failed_settings = []
    for key, value in sysctl_config.items():
        try:
            # Check if sysctl key exists
            if not server.shell(
                name=f"Check if {key} exists",
                commands=[f"test -f /proc/sys/{key.replace('.', '/')}"],
                _ignore_errors=True,
            ):
                host.noop(f"Skip {key} - parameter not supported")
                continue

            server.sysctl(
                name=f"Set {key} to {value}",
                key=key,
                value=value,
                persist=True,
                persist_file="/etc/sysctl.d/99-security.conf",
            )
        except Exception as e:
            failed_settings.append(key)
            host.noop(f"Failed to set {key}: {str(e)}")
            continue

    # Apply settings
    try:
        server.shell(
            name="Apply sysctl settings",
            commands=["sysctl -p /etc/sysctl.d/99-security.conf"],
            _ignore_errors=True,
        )
    except Exception as e:
        host.noop(f"Warning - Failed to apply sysctl settings: {str(e)}")

    if failed_settings:
        host.noop(
            f"Warning - Failed to set some kernel parameters: {', '.join(failed_settings)}"
        )
        return False

    host.noop("Success - Kernel hardening completed")
    return True
