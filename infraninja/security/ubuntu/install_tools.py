from pyinfra import host
from pyinfra.api import deploy
from pyinfra.facts.apt import AptSources
from pyinfra.operations import apt

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
            "packages": ["auditd"],
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
        "acl": {
            "install": True,
            "packages": ["acl"],
        },
        "cron": {
            "install": True,
            "packages": ["cron"],
        },
        "iptables": {
            "install": True,
            "packages": ["iptables", "iptables-persistent", "netfilter-persistent"],
        },
        "named": {
            "install": True,
            "packages": ["bind9"],
        },
        "nftables": {
            "install": True,
            "packages": ["nftables"],
        },
        "ntp": {
            "install": True,
            "packages": ["ntp"],
        },
    }
}


@deploy("Install Security Tools", data_defaults=DEFAULTS)
def install_security_tools():
    # Loop over each tool in the host data
    for _, tool_data in host.data.security_tools.items():
        # Check if the tool is set to install
        if tool_data["install"]:
            for package in tool_data["packages"]:
                installed_packages = host.get_fact(AptSources)

                # Check if package is installed
                if package not in installed_packages:
                    # Install the specified package
                    apt.packages(
                        name=f"Install {package}",
                        packages=[package],
                    )
                else:
                    pass
