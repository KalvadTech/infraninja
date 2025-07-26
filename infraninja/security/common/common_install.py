from pyinfra.api.deploy import deploy
from pyinfra.context import host
from pyinfra.facts.server import LinuxDistribution
from pyinfra.operations import server


class CommonPackageInstaller:
    """
    Installs common security packages across various Linux distributions.

    Provides a unified interface for installing essential security tools
    across different Linux distributions and package managers. Automatically
    detects the distribution family and uses appropriate package names.

    Supported distributions:
    - Debian-based (Ubuntu, Debian, Mint) - using apt
    - Alpine Linux - using apk
    - Red Hat family (RHEL, CentOS, Fedora, Rocky, Alma) - using yum/dnf
    - Arch Linux family (Arch, Manjaro, EndeavourOS) - using pacman
    - SUSE family (openSUSE) - using zypper
    - Void Linux - using xbps
    - FreeBSD - using pkg

    .. code:: python

        from infraninja.security.common.common_install import CommonPackageInstaller

        # Install default security packages
        CommonPackageInstaller().deploy()

        # Install custom package set
        custom_packages = {
            'security_tools': {
                'debian': ['custom-security-tool'],
                'alpine': ['custom-security-alpine'],
            }
        }
        CommonPackageInstaller(packages=custom_packages).deploy()

        # For openSUSE with additional repositories
        zypper_repos = [
            "https://download.opensuse.org/repositories/security/openSUSE_Tumbleweed/security.repo"
        ]
        CommonPackageInstaller(zypper_repos=zypper_repos).deploy()
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
        },
        "cron": {
            "debian": ["cron"],
            "alpine": ["cronie"],
            "rhel": ["cronie"],
            "arch": ["cronie"],
            "suse": ["cronie"],
            "void": ["cronie"],
        },
        "udev": {
            "debian": ["udev"],
            "alpine": ["udev", "eudev"],
            "rhel": ["systemd-udev"],
            "arch": ["udev"],
            "suse": ["udev"],
            "void": ["eudev"],
            "freebsd": ["devd"],
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
            "freebsd": ["security/py-fail2ban"],
        },
        "security_tools": {
            "debian": [
                "rkhunter",
                "chkrootkit",
                "lynis",
                "clamav",
                "clamav-daemon",
            ],
            "alpine": ["rkhunter", "chkrootkit", "lynis", "clamav"],
            "rhel": ["rkhunter", "chkrootkit", "lynis", "clamav"],
            "arch": ["rkhunter", "chkrootkit", "lynis", "clamav"],
            "suse": ["rkhunter", "chkrootkit", "lynis", "clamav"],
            "void": ["rkhunter", "chkrootkit", "lynis", "clamav"],
            "freebsd": ["rkhunter", "chkrootkit", "lynis", "clamav"],
        },
        "apparmor": {
            "debian": ["apparmor"],
            "alpine": ["apparmor"],
            "rhel": ["apparmor"],
            "arch": ["apparmor"],
            "suse": ["apparmor"],
            "void": ["apparmor"],
        },
    }

    def __init__(self, packages=None, zypper_repos=None):
        """
        Initialize with custom packages or use defaults.

        :param packages: Custom packages dictionary mapping generic names to distribution-specific package lists
        :type packages: dict, optional
        :param zypper_repos: List of zypper repository URLs to add before installing packages (SUSE/openSUSE only)
        :type zypper_repos: list, optional
        """
        self.packages = packages or self.DEFAULT_PACKAGES.copy()
        self.zypper_repos = zypper_repos or []

    @staticmethod
    def _get_distro_family():
        """
        Determine the Linux distribution family for package selection.

        Analyzes system information to classify the distribution into
        one of the supported families for appropriate package manager selection.

        :returns: The distribution family identifier
        :rtype: str
        :returns: None if distribution is not supported
        :rtype: None
        """
        # Get detailed distribution information
        distro = host.get_fact(LinuxDistribution)
        distro_name = distro.get("name", "")
        distro_id = distro.get("release_meta", {}).get("ID", "").lower()
        id_like = distro.get("release_meta", {}).get("ID_LIKE", "").lower()

        # Normalize distro names
        distro_name = distro_name.lower() if distro_name else ""

        # Determine the distribution family
        if any(
            dist in distro_name for dist in ["ubuntu", "debian", "mint", "linuxmint"]
        ) or any(dist in id_like for dist in ["debian", "ubuntu"]):
            return "debian"
        elif "alpine" in distro_name:
            return "alpine"
        elif (
            any(
                dist in distro_name
                for dist in ["fedora", "rhel", "centos", "rocky", "alma"]
            )
            or "rhel" in id_like
        ):
            return "rhel"
        elif (
            any(dist in distro_name for dist in ["arch", "manjaro", "endeavouros"])
            or "arch" in id_like
        ):
            return "arch"
        elif any(dist in distro_name for dist in ["opensuse", "suse"]):
            return "suse"
        elif "void" in distro_name:
            return "void"
        elif "freebsd" in distro_name:
            return "freebsd"
        else:
            host.noop(f"Warning: Unsupported OS: {distro_name} (ID: {distro_id})")
            return None

    def _setup_zypper_repos(self):
        """
        Add zypper repositories if specified and on SUSE/openSUSE system.

        Configures additional package repositories for SUSE/openSUSE systems
        to provide access to security packages that may not be in default repos.

        :returns: None
        :rtype: None
        """
        if not self.zypper_repos:
            return

        host.noop(f"Adding {len(self.zypper_repos)} zypper repositories")

        for repo_url in self.zypper_repos:
            server.shell(
                name=f"Add zypper repository: {repo_url}",
                commands=[f"zypper --gpg-auto-import-keys addrepo {repo_url}"],
            )

        # Refresh repositories after adding them
        server.shell(
            name="Refresh zypper repositories with auto-accept keys",
            commands=["zypper --gpg-auto-import-keys refresh"],
        )

    @deploy("Install Common Security Packages")
    def deploy(self):
        """
        Install common security packages across different Linux distributions.

        Executes the package installation process by detecting the distribution
        family, setting up any additional repositories if needed, and installing
        the appropriate packages using the system's package manager.

        :returns: True if packages were installed successfully, False if no packages to install
        :rtype: bool
        :raises ValueError: If the operating system is not supported
        """
        distro_family = self._get_distro_family()
        if not distro_family:
            raise ValueError(
                f"Unsupported OS: {host.get_fact(LinuxDistribution).get('name', 'Unknown')}"
            )

        host.noop(f"Installing common security packages for {distro_family} family")

        # Add zypper repositories if on SUSE/openSUSE
        if distro_family == "suse" and self.zypper_repos:
            self._setup_zypper_repos()

        # Store all packages to install for this distro
        packages_to_install = []

        # Collect all packages for this distro family
        for package_type, distro_packages in self.packages.items():
            if distro_family in distro_packages:
                pkg_list = distro_packages[distro_family]
                host.noop(f"Adding {package_type} packages: {', '.join(pkg_list)}")
                packages_to_install.extend(pkg_list)

        if not packages_to_install:
            host.noop("No packages to install for this distribution")
            return False

        # Use the server.packages operation which automatically detects and uses
        # the appropriate package manager for the current distribution
        if distro_family == "suse":
            # Need to handle zypper repositories differently
            # First refresh repositories
            server.shell(
                name="Refresh zypper repositories with auto-import keys",
                commands=["zypper --gpg-auto-import-keys refresh"],
            )
            # Then install packages
            server.packages(
                name="Install common security packages",
                packages=packages_to_install,
                present=True,
            )
        else:
            server.packages(
                name="Install common security packages",
                packages=packages_to_install,
                present=True,
            )

        return True
