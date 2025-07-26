from pyinfra.api.deploy import deploy
from pyinfra.context import host
from pyinfra.facts.files import File
from pyinfra.facts.server import LinuxDistribution
from pyinfra.operations import server


@deploy("Set ACL")
def acl_setup():
    """
    Set up Access Control Lists (ACL) for security-critical files and directories.

    Configures ACL permissions for security tools configuration files,
    log files, and system directories. Automatically installs ACL utilities
    if not present and handles OS-specific package managers.

    .. code:: python

        from infraninja.security.common.acl import acl_setup
        acl_setup()

    :returns: True if ACL setup completed successfully
    :rtype: bool
    :raises NotImplementedError: If called on FreeBSD systems
    """
    # Get OS information
    distro = host.get_fact(LinuxDistribution)
    os_name = str(distro.get("name", "")).lower() if distro else ""

    # FreeBSD implementation moved to dedicated module
    if "freebsd" in os_name:
        raise NotImplementedError(
            "FreeBSD ACL setup is not implemented in this module. "
            "Please use the dedicated FreeBSD ACL module instead."
        )
    # Check if setfacl is available on Linux systems
    if not server.shell(
        name="Check if setfacl exists",
        commands=["command -v setfacl"],
        _ignore_errors=True,
    ):
        # Try to install ACL utilities on Linux
        if os_name in ["ubuntu", "debian"]:
            server.shell(
                name="Install ACL utilities",
                commands=["apt-get update && apt-get install -y acl"],
                _ignore_errors=True,
            )
        elif os_name in ["centos", "rhel", "fedora"]:
            server.shell(
                name="Install ACL utilities",
                commands=["yum install -y acl"],
                _ignore_errors=True,
            )
        elif os_name == "alpine":
            server.shell(
                name="Install ACL utilities",
                commands=["apk add acl"],
                _ignore_errors=True,
            )

        # Check again if setfacl is now available
        if not server.shell(
            name="Verify setfacl exists after installation",
            commands=["command -v setfacl"],
            _ignore_errors=True,
        ):
            host.noop(
                "Skip ACL setup - setfacl not available and could not be installed"
            )
            return

    # Define the ACL paths and rules
    ACL_PATHS = {
        "/etc/fail2ban": "u:root:rwx",
        "/var/log/lynis-report.dat": "u:root:r",
        "/etc/audit/audit.rules": "g:root:rwx",
        "/etc/suricata/suricata.yaml": "u:root:rwx",
        "/var/log/suricata": "u:root:rwx",
        "/etc/iptables/rules.v4": "u:root:rwx",
        "/etc/ssh/sshd_config": "u:root:rw",
        "/etc/cron.d": "u:root:rwx",
        "/etc/rsyslog.conf": "u:root:rw",
        "/etc/modprobe.d": "u:root:rwx",
        "/etc/udev/rules.d": "u:root:rwx",
        "/etc/fstab": "u:root:rw",
    }

    for path, acl_rule in ACL_PATHS.items():
        # Check if path exists before attempting to set ACL
        if host.get_fact(File, path=path) is None:
            host.noop(f"Skip ACL for {path} - path does not exist")
            continue

        # Attempt to set the ACL
        try:
            # Linux systems
            server.shell(
                name=f"Set ACL for {path}",
                commands=[f"setfacl -m {acl_rule} {path}"],
                _ignore_errors=True,
            )
        except Exception as e:
            host.noop(f"Failed to set ACL for {path} - {str(e)}")

    return True
