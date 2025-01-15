from pyinfra import host
from pyinfra.api import deploy
from pyinfra.facts.server import LinuxName, LinuxDistribution
from pyinfra.operations import server, files


@deploy("Kernel Security Hardening")
def kernel_hardening():
    # Check if running on Linux
    linux_name = host.get_fact(LinuxName)
    linux_dist = host.get_fact(LinuxDistribution)
    
    if not linux_name:
        print("[ERROR] This script requires a Linux system")
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
        "net.ipv4.conf.all.accept_redirects": "0",
        "net.ipv4.conf.default.accept_redirects": "0",
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
        "kernel.exec-shield": "1",
        # Core Dumps
        "fs.suid_dumpable": "0",
        # System Security
        "kernel.sysrq": "0",
        "kernel.core_uses_pid": "1",
        "kernel.dmesg_restrict": "1",
        "kernel.kptr_restrict": "2",
        "kernel.yama.ptrace_scope": "1",
    }

    # Apply sysctl settings with error handling
    failed_settings = []
    for key, value in sysctl_config.items():
        try:
            server.sysctl(
                name=f"Set {key} to {value}",
                key=key,
                value=value,
                persist=True,
                persist_file="/etc/sysctl.d/99-security.conf",
                    )
        except Exception as e:
            failed_settings.append(key)
            print(f"[WARNING] Failed to set {key}: {str(e)}")

    # Apply settings based on distribution
    
    try:
        server.sysctl(
            name=f"Apply sysctl settings for {linux_dist}",
            persist_file="/etc/sysctl.d/99-security.conf",
            apply=True,
            )
    except Exception as e:
        print(f"[WARNING] Failed to apply sysctl settings: {str(e)}")
        return False

    if failed_settings:
        print(f"[WARNING] Failed to set some kernel parameters: {', '.join(failed_settings)}")
        return False

    print("[SUCCESS] Kernel hardening completed")
    return True
