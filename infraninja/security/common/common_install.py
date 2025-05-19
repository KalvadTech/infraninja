from pyinfra.context import host
from pyinfra.api.deploy import deploy
from pyinfra.facts.server import LinuxDistribution
from pyinfra.operations import server


class CommonPackageInstaller:
    """
    Installs common packages across various Linux distributions.
    Similar to SSHHardener and ServiceDisabler, this is a class-based approach.

    Usage:
        from infraninja.security.common.common_install import CommonPackageInstaller
        CommonPackageInstaller().deploy()

        you may define your own packages by passing a dictionary to the constructor:
        custom_packages = {
            'generic_name': {
                'debian': ['debian_pkg1', 'debian_pkg2'],
                'alpine': ['alpine_pkg1'],
            }
        }

    """

    # Core common packages for security tools
    DEFAULT_PACKAGES = {
        # Format: 'generic_name': {'debian': ['debian_pkg1', 'debian_pkg2'], 'alpine': ['alpine_pkg1']}
        "acl": {
            "debian": ["acl"],
            "alpine": ["acl"],
            "rhel": ["acl"],
            "arch": ["acl"],
            "suse": ["acl"],
            "void": ["acl"],
            "freebsd": ["acl"],
        },
        "cron": {
            "debian": ["cron"],
            "alpine": ["cronie"],
            "rhel": ["cronie"],
            "arch": ["cronie"],
            "suse": ["cronie"],
            "void": ["cronie"],
            "freebsd": ["cron"],
        },
        "firewall": {
            "debian": [
                "nftables",
                "iptables",
                "iptables-persistent",
                "netfilter-persistent",
            ],
            "alpine": ["nftables", "iptables"],
            "rhel": ["nftables", "iptables", "iptables-services"],
            "arch": ["nftables", "iptables"],
            "suse": ["nftables", "iptables"],
            "void": ["nftables", "iptables"],
            "freebsd": ["ipfw", "pf"],
        },
        "ssh": {
            "debian": ["openssh-server", "openssh-client"],
            "alpine": ["openssh-server", "openssh-client"],
            "rhel": ["openssh-server", "openssh-clients"],
            "arch": ["openssh"],
            "suse": ["openssh"],
            "void": ["openssh"],
            "freebsd": ["openssh-portable"],
        },
        "audit": {
            "debian": ["auditd"],
            "alpine": ["audit"],
            "rhel": ["audit"],
            "arch": ["audit"],
            "suse": ["audit"],
            "void": ["audit"],
            "freebsd": ["audit"],
        },
        "logrotate": {
            "debian": ["logrotate"],
            "alpine": ["logrotate"],
            "rhel": ["logrotate"],
            "arch": ["logrotate"],
            "suse": ["logrotate"],
            "void": ["logrotate"],
            "freebsd": ["logrotate"],
        },
        "fail2ban": {
            "debian": ["fail2ban"],
            "alpine": ["fail2ban"],
            "rhel": ["fail2ban"],
            "arch": ["fail2ban"],
            "suse": ["fail2ban"],
            "void": ["fail2ban"],
            "freebsd": ["py39-fail2ban"],
        },
    }

    def __init__(self, packages=None):
        """
        Initialize with custom packages or use defaults.

        Args:
            packages (dict, optional): Custom packages dictionary. Defaults to None.
        """
        self.packages = packages or self.DEFAULT_PACKAGES.copy()

    @deploy("Install Common Security Packages")
    def deploy(self):
        """
        Install common security packages across different Linux distributions.

        Raises:
            OperationError: if no packages are defined for the detected distribution.
        """

        distro = host.get_fact(LinuxDistribution)
        distro_name = distro.get("name", "")
        if distro_name:
            distro_name = distro_name.lower()
        distro_id = distro.get("release_meta", {}).get("ID", "")
        if distro_id:
            distro_id = distro_id.lower()

        host.noop(f"Installing Packages on: {distro_name} (ID: {distro_id})")

        # Store all packages to install for this distro
        packages_to_install = []

        server.packages(
            name="Install common security packages",
            packages=packages_to_install,
            present=True,
        )

        return True
