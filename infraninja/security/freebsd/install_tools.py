from pyinfra.api.deploy import deploy
from pyinfra.context import host
from pyinfra.facts.server import LinuxDistribution
from pyinfra.operations import files, server
from pyinfra.operations.freebsd import service


class FreeBSDSecurityInstaller:
    """
    Installs and configures security tools on FreeBSD systems.
    Similar to CommonPackageInstaller, this is a class-based approach for extensibility.

    Usage:
        from infraninja.security.freebsd.install_tools import FreeBSDSecurityInstaller
        FreeBSDSecurityInstaller().deploy()

        You may define your own packages by passing a dictionary to the constructor:
        custom_packages = {
            'fail2ban': ['py39-fail2ban'],
            'clamav': ['clamav'],
        }
        FreeBSDSecurityInstaller(packages=custom_packages).deploy()
    """

    # Default security packages for FreeBSD
    DEFAULT_PACKAGES = {
        "fail2ban": ["security/py-fail2ban"],  # Correct FreeBSD package name
        "clamav": ["security/clamav"],
        "suricata": ["security/suricata"],
        "sudo": ["security/sudo"],
        "ca_root_nss": ["security/ca_root_nss"],
        "lynis": ["security/lynis"],
        "rkhunter": ["security/rkhunter"],
        "chkrootkit": ["security/chkrootkit"],
        # Note: Some packages may not be available or have different names
        # "ossec": ["security/ossec-hids"],  # May not be available
        # "portaudit": [],  # Deprecated, replaced by pkg audit
    }

    def __init__(self, packages=None):
        """
        Initialize with custom packages or use defaults.

        Args:
            packages (dict, optional): Custom packages dictionary. Defaults to None.
        """
        self.packages = packages or self.DEFAULT_PACKAGES.copy()

    @staticmethod
    def _verify_freebsd():
        """
        Verify that the system is running FreeBSD.

        Returns:
            bool: True if FreeBSD, raises ValueError otherwise
        """
        distro = host.get_fact(LinuxDistribution)
        distro_name = (distro.get("name", "") or "").lower() if distro else ""

        if "freebsd" not in distro_name and distro_name:
            raise ValueError(
                f"This deployment is designed for FreeBSD systems only. Detected: {distro_name}"
            )
        return True

    def _configure_tool(self, tool_name):
        """
        Configure specific security tools after installation.

        Args:
            tool_name (str): Name of the tool to configure
        """
        if tool_name == "fail2ban":
            # Enable and start fail2ban
            files.line(
                name="Enable fail2ban in rc.conf",
                path="/etc/rc.conf",
                line='fail2ban_enable="YES"',
                present=True,
            )
            service.service(
                name="Start fail2ban service",
                srvname="fail2ban",
                srvstate="started",
            )

        elif tool_name == "clamav":
            # Update virus definitions
            server.shell(
                name="Update ClamAV virus definitions",
                commands=["freshclam"],
            )
            # Enable and start ClamAV daemon
            files.line(
                name="Enable ClamAV in rc.conf",
                path="/etc/rc.conf",
                line='clamav_clamd_enable="YES"',
                present=True,
            )
            files.line(
                name="Enable ClamAV freshclam in rc.conf",
                path="/etc/rc.conf",
                line='clamav_freshclam_enable="YES"',
                present=True,
            )
            service.service(
                name="Start ClamAV service",
                srvname="clamav-clamd",
                srvstate="started",
            )
            service.service(
                name="Start ClamAV freshclam service",
                srvname="clamav-freshclam",
                srvstate="started",
            )

        elif tool_name == "suricata":
            # Enable and start Suricata
            files.line(
                name="Enable Suricata in rc.conf",
                path="/etc/rc.conf",
                line='suricata_enable="YES"',
                present=True,
            )
            service.service(
                name="Start Suricata service",
                srvname="suricata",
                srvstate="started",
            )

    @deploy("Install FreeBSD Security Tools")
    def deploy(self):
        """
        Install and configure security tools on FreeBSD systems.

        Returns:
            bool: True if successful
        """
        # Verify we're on FreeBSD
        self._verify_freebsd()

        host.noop("Installing FreeBSD security tools")

        # Collect all packages to install
        packages_to_install = []
        for tool_name, packages in self.packages.items():
            host.noop(f"Adding {tool_name} packages: {', '.join(packages)}")
            packages_to_install.extend(packages)

        if not packages_to_install:
            host.noop("No packages to install")
            return False

        # Use server.packages which automatically uses FreeBSD pkg
        server.packages(
            name="Install FreeBSD security packages",
            packages=packages_to_install,
            present=True,
        )

        # Configure each tool that was installed
        for tool_name in self.packages.keys():
            self._configure_tool(tool_name)

        return True
