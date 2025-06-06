from pyinfra.context import host
from pyinfra.api.deploy import deploy
from pyinfra.facts.server import LinuxDistribution, Which
from pyinfra.operations.freebsd import pkg
from pyinfra.operations import (
    apk,
    apt,
    dnf,
    pacman,
    yum,
    zypper,
    xbps,
)


@deploy("Common System Updates")
def system_update():
    """
    Update and upgrade packages across various Linux distributions.

    Supported distributions:
    - Debian, Ubuntu, Mint, and other Debian-based distros (using apt)
    - Alpine (using apk)
    - RHEL, CentOS, Fedora, Rocky Linux, AlmaLinux (using yum or dnf)
    - Arch Linux, Manjaro, EndeavourOS (using pacman)
    - openSUSE (using zypper)
    - FreeBSD (using pkg)
    - Void Linux (using xbps)
    """
    # Get detailed distribution information
    distro = host.get_fact(LinuxDistribution)
    distro_name = distro.get("name", "")
    distro_id = distro.get("release_meta", {}).get("ID", "").lower()
    id_like = distro.get("release_meta", {}).get("ID_LIKE", "").lower()

    # Normalize distro names
    distro_name = distro_name.lower() if distro_name else ""

    # Debian-based distributions (Ubuntu, Debian, Mint, etc.)
    if any(d in distro_name for d in ["ubuntu", "debian", "mint", "linuxmint"]) or any(
        d in id_like for d in ["debian", "ubuntu"]
    ):
        apt.update(name=f"Update {distro_name} package lists")
        apt.upgrade(name=f"Upgrade {distro_name} packages")

    # Alpine Linux
    elif "alpine" in distro_name:
        apk.update(name="Update Alpine package lists")
        apk.upgrade(name="Upgrade Alpine packages")

    # RedHat family - newer versions use DNF, older use YUM
    elif (
        any(d in distro_name for d in ["fedora", "rhel", "centos", "rocky", "alma"])
        or "rhel" in id_like
    ):
        # Try to determine if system has dnf or needs to use yum
        if host.get_fact(Which, command="dnf"):  # Use the Which class
            dnf.update(name=f"Update {distro_name} packages")
        else:
            yum.update(name=f"Update {distro_name} packages")

    # Arch Linux and derivatives
    elif (
        any(d in distro_name for d in ["arch", "manjaro", "endeavouros"])
        or "arch" in id_like
    ):
        # TODO: check if theres an aur helper, use that instead, if not use pacman

        pacman.update(name=f"Update {distro_name} package database")
        pacman.upgrade(name=f"Upgrade {distro_name} packages")

    # openSUSE
    elif any(d in distro_name for d in ["opensuse", "suse"]):
        zypper.update(name=f"Update {distro_name} packages")

    # FreeBSD
    elif "freebsd" in distro_name:
        pkg.update(name="Update FreeBSD package database")
        pkg.upgrade(name="Upgrade FreeBSD packages")

    # Void Linux
    elif "void" in distro_name:
        xbps.update(name="Update Void Linux package database")
        xbps.upgrade(name="Upgrade Void Linux packages")

    # Unsupported OS
    else:
        raise ValueError(f"Unsupported OS: {distro_name} (ID: {distro_id})")
