from pyinfra.api.deploy import deploy
from pyinfra.context import host
from pyinfra.facts.server import LinuxDistribution
from pyinfra.operations.freebsd import freebsd_update, pkg


@deploy("FreeBSD System Updates")
def system_update():
    """
    Update and upgrade packages on FreeBSD systems.

    This function handles:
    - FreeBSD base system updates using freebsd-update
    - Package updates using pkg
    - Cleaning package cache
    """
    # Get distribution information to confirm we're on FreeBSD
    distro = host.get_fact(LinuxDistribution)
    distro_name = (distro.get("name", "") or "").lower() if distro else ""

    # FreeBSD base system updates
    if "freebsd" in distro_name or not distro_name:
        # Update package repository catalogs
        pkg.update(name="Update FreeBSD package catalogs")

        # Upgrade all installed packages
        pkg.upgrade(name="Upgrade FreeBSD packages")

        # Clean package cache to free up space
        pkg.clean(all_pkg=True, name="Clean FreeBSD package cache")

        # Remove orphaned packages
        pkg.autoremove(name="Remove orphaned packages")

        # Update FreeBSD base system
        # very buggy, it throws an error and stops pyinfra when no updates found
        freebsd_update.update(name="Update FreeBSD base system")

    else:
        raise ValueError(
            f"This deployment is designed for FreeBSD systems only. Detected: {distro_name}"
        )


@deploy("FreeBSD Package Updates Only")
def package_update():
    """
    Update only packages on FreeBSD systems (skip base system updates).

    This is useful when you only want to update packages without
    updating the FreeBSD base system.
    """
    distro = host.get_fact(LinuxDistribution)
    distro_name = (distro.get("name", "") or "").lower() if distro else ""
    if "freebsd" in distro_name or not distro_name:
        # Update package repository catalogs
        pkg.update(name="Update FreeBSD package catalogs")

        # Upgrade all installed packages
        pkg.upgrade(name="Upgrade FreeBSD packages")

        # Clean package cache to free up space
        pkg.clean(all_pkg=True, name="Clean FreeBSD package cache")

        # Remove orphaned packages
        pkg.autoremove(name="Remove orphaned packages")
    else:
        raise ValueError(
            f"This deployment is designed for FreeBSD systems only. Detected: {distro_name}"
        )
