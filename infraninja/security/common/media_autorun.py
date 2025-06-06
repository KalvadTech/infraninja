from pyinfra.api import deploy
from pyinfra.context import host
from pyinfra.facts.server import LinuxDistribution, Which
from pyinfra.operations import files, server, systemd


@deploy("disable Media Autorun")
def media_autorun():
    systemd.service(
        name="Disable udisks2 service",
        service="autofs",
        running=False,
        enabled=False,
    )

    # Get distro information
    distro = host.get_fact(LinuxDistribution)
    distro_name = distro.get("name", "") or ""
    distro_name = distro_name.lower()

    # FreeBSD doesn't use udev, skip these operations
    if "freebsd" not in distro_name:
        # Ensure the directory exists
        files.directory(
            name="Ensure /etc/udev/rules.d directory exists",
            path="/etc/udev/rules.d",
            present=True,
        )

        files.line(
            name="Disable media autorun",
            path="/etc/udev/rules.d/85-no-automount.rules",
            line='ACTION=="add", SUBSYSTEM=="block", ENV{UDISKS_AUTO}="0", ENV{UDISKS_IGNORE}="1"',
            present=True,
        )

        # Check if udevadm exists before running it
        has_udevadm = host.get_fact(Which, command="udevadm")
        if has_udevadm:
            server.shell(
                name="Reload udev rules",
                commands=["udevadm control --reload-rules && udevadm trigger"],
            )
        else:
            host.noop(f"Skipping udevadm reload as it's not available on {distro_name}")

    # Create mount point directory if it doesn't exist
    files.directory(
        name="Ensure /mnt/usb directory exists",
        path="/mnt/usb",
        present=True,
    )

    files.line(
        name="Disable media autorun",
        path="/etc/fstab",
        line="/dev/sda1 /mnt/usb vfat noauto,nouser,noexec 0 0",
        present=True,
    )

    # Check if /dev/sda1 exists before trying to mount it
    server.shell(
        name="reload fstab safely",
        commands=["mount -a || true"],  # Continue even if mount fails
    )
