from pyinfra import config, host
from pyinfra.api import deploy
from pyinfra.operations import apk

config.SUDO = True

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
        "lynis": {
            "install": True,
            "packages": ["lynis"],
        },
        "chkrootkit": {
            "install": True,
            "packages": ["chkrootkit"],
        },
        "suricata": {
            "install": True,
            "packages": ["suricata"],
        },
        "unattended-upgrades": {
            "install": True,
            "packages": ["unattended-upgrades"],
        },
        "acl": {
            "install": True,
            "packages": ["acl"],
        },
        "cronie": {
            "install": True,
            "packages": ["cronie"],
        },
    }
}


@deploy("Install Security Tools", data_defaults=DEFAULTS)
def install_security_tools():
    # Loop over each tool in the host data
    for tool, tool_data in host.data.security_tools.items():
        # Check if the tool is set to install
        if tool_data["install"]:
            # Check if the primary package is already installed
            primary_package = tool_data["packages"][0]
            if not host.fact.apk.is_installed(primary_package):
                # Install the specified packages for this tool
                apk.packages(
                    name=f"Install {tool} and related packages",
                    packages=tool_data["packages"],
                )
            else:
                print(f"{primary_package} is already installed, skipping.")
