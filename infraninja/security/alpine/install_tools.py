import contextlib

from pyinfra import host
from pyinfra.api import deploy
from pyinfra.facts.apk import ApkPackages
from pyinfra.facts.server import LinuxDistribution, LinuxName
from pyinfra.operations import apk, server

# Define defaults for each security tool and related packages
DEFAULTS = {
    "security_tools": {
        "fail2ban": {
            "install": True,
            "packages": ["fail2ban"],
        },
        "apparmor-utils": {
            "install": True,
            "packages": ["apparmor-utils"],
        },
        "auditd": {
            "install": True,
            "packages": ["audit"],
        },
        "clamav": {
            "install": True,
            "packages": ["clamav", "clamav-daemon"],
        },
        "suricata": {
            "install": True,
            "packages": ["suricata"],
        },
        "acl": {
            "install": True,
            "packages": ["acl"],
        },
        "cronie": {
            "install": True,
            "packages": ["cronie"],
        },
        "nftables": {
            "install": True,
            "packages": ["nftables"],
        },
    }
}


@deploy("Install Security Tools", data_defaults=DEFAULTS)
def install_security_tools():
    # Check OS and package manager
    linux_name = host.get_fact(LinuxName)
    linux_dist = host.get_fact(LinuxDistribution)

    is_alpine = any("alpine" in str(name).lower() for name in [linux_name, linux_dist])

    if not is_alpine:
        return False

    # Verify APK is available
    if not server.shell(
        name="Check if APK exists",
        commands=["command -v apk"],
    ):
        return False

    # Get current package state
    installed_packages = []
    with contextlib.suppress(Exception):
        installed_packages = host.get_fact(ApkPackages)

    # Loop over each tool in the host data
    for _, tool_data in host.data.security_tools.items():
        if not tool_data["install"]:
            continue

        for package in tool_data["packages"]:
            if package in installed_packages:
                continue

            # Attempt to install the package
            apk.packages(
                packages=[package],
                present=True,
            )

    return True
