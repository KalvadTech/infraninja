from pyinfra.api.deploy import deploy
from pyinfra.context import host
from pyinfra.facts.files import File
from pyinfra.facts.server import LinuxDistribution
from pyinfra.operations import server


@deploy("FreeBSD ACL Setup")
def acl_setup():
    """
    Set up Access Control Lists (ACL) for security-critical files and directories on FreeBSD.

    Configures POSIX.1e ACL permissions for security tools configuration files,
    log files, and system directories on FreeBSD systems. Automatically enables
    ACL support on UFS filesystems and handles FreeBSD-specific ACL syntax.

    .. code:: python

        from infraninja.security.freebsd.acl import acl_setup
        acl_setup()

    :returns: True if ACL setup completed successfully
    :rtype: bool
    :raises ValueError: If called on non-FreeBSD systems

    .. note::
        FreeBSD ACLs require UFS filesystem with ACL support enabled.

    .. warning::
        ACL modifications may affect system security. Ensure you understand
        the implications before running in production environments.
    """
    # Verify this is FreeBSD
    distro = host.get_fact(LinuxDistribution)
    distro_name = str(distro.get("name", "")).lower() if distro else ""
    if distro_name != "freebsd":
        raise ValueError("This deployment is designed for FreeBSD systems only")

    # Check if setfacl is available on FreeBSD
    setfacl_check = server.shell(
        name="Check if setfacl exists",
        commands=["command -v setfacl"],
        _ignore_errors=True,
    )

    if not setfacl_check:
        host.noop("setfacl not available on this FreeBSD system")
        return False

    # Check if ACLs are enabled on root filesystem
    acl_mount_check = server.shell(
        name="Check if root filesystem is mounted with ACLs",
        commands=["mount | grep 'on / ' | grep -q acls"],
        _ignore_errors=True,
    )

    if not acl_mount_check:
        # Try to enable ACLs with tunefs (requires clean filesystem)
        tunefs_result = server.shell(
            name="Try to enable ACL support on root filesystem",
            commands=["tunefs -a enable /"],
            _ignore_errors=True,
        )

        if not tunefs_result:
            host.noop(
                "ACL support cannot be enabled. Root filesystem may need fsck or "
                "may not support ACLs. Consider running 'fsck /' when unmounted "
                "or rebuilding kernel with UFS_ACL option."
            )
            return False

    # Enable ACLs in fstab for future mounts (if not already present)
    fstab_check_result = server.shell(
        name="Check if root filesystem has acls option in fstab",
        commands=["grep -q 'acls' /etc/fstab"],
        _ignore_errors=True,
    )

    if not fstab_check_result:
        host.noop(
            "ACL support not found in /etc/fstab. Consider adding 'acls' option "
            "to root filesystem entry and remounting for ACL support."
        )

    # Define FreeBSD-specific ACL paths and rules
    # FreeBSD uses different ACL syntax than Linux
    ACL_PATHS = {
        "/usr/local/etc/fail2ban": "user:root:rwx",
        "/var/log/security": "user:root:rwx",
        "/etc/audit": "user:root:rwx",
        "/usr/local/etc/suricata": "user:root:rwx",
        "/var/log/suricata": "user:root:rwx",
        "/etc/pf.conf": "user:root:rw-",
        "/etc/ssh/sshd_config": "user:root:rw-",
        "/etc/crontab": "user:root:rw-",
        "/etc/syslog.conf": "user:root:rw-",
        "/etc/fstab": "user:root:rw-",
        "/etc/rc.conf": "user:root:rw-",
        "/boot/loader.conf": "user:root:rw-",
        "/etc/newsyslog.conf": "user:root:rw-",
    }

    successful_acls = 0
    for path, acl_rule in ACL_PATHS.items():
        # Check if path exists before attempting to set ACL
        if host.get_fact(File, path=path) is None:
            host.noop(f"Skip ACL for {path} - path does not exist")
            continue

        # Attempt to set the ACL using FreeBSD syntax
        result = server.shell(
            name=f"Set ACL for {path}",
            commands=[f"setfacl -m {acl_rule} {path}"],
            _ignore_errors=True,
        )

        if result:
            successful_acls += 1
        else:
            host.noop(
                f"Failed to set ACL for {path} - ACLs may not be enabled on filesystem"
            )

    # Set ACLs for common FreeBSD log directories
    log_directories = [
        "/var/log",
        "/var/audit",
        "/var/log/security",
        "/usr/local/var/log",
    ]

    for log_dir in log_directories:
        if host.get_fact(File, path=log_dir):
            result = server.shell(
                name=f"Set ACL for log directory {log_dir}",
                commands=[f"setfacl -m user:root:rwx {log_dir}"],
                _ignore_errors=True,
            )
            if result:
                successful_acls += 1
            else:
                host.noop(
                    f"Failed to set ACL for {log_dir} - ACLs may not be enabled on filesystem"
                )

    # Set default ACLs on directories to ensure inheritance
    default_acl_dirs = [
        "/var/log",
        "/var/audit",
        "/usr/local/etc",
    ]

    for dir_path in default_acl_dirs:
        if host.get_fact(File, path=dir_path):
            server.shell(
                name=f"Set default ACL for {dir_path}",
                commands=[f"setfacl -d -m user:root:rwx {dir_path}"],
                _ignore_errors=True,
            )

    # Verify ACL functionality
    server.shell(
        name="Test ACL functionality",
        commands=["getfacl /etc/ssh/sshd_config 2>/dev/null | grep -q 'user:root'"],
        _ignore_errors=True,
    )

    return False
