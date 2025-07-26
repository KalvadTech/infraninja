from pyinfra.api.deploy import deploy
from pyinfra.context import host
from pyinfra.facts.server import Command
from pyinfra.operations import server


def check_reboot_required(host):
    """
    Check if a system reboot is required by examining various indicators.

    Examines multiple system-specific indicators to determine if a reboot
    is needed after system updates or configuration changes.

    On Linux systems:
    - Checks for /var/run/reboot-required and /var/run/reboot-required.pkgs
    - On Alpine Linux, compares installed kernel with running kernel
    - On Arch Linux systems, checks for pending package updates
    - On Fedora/RHEL systems, uses dnf needs-restarting

    On FreeBSD systems:
    - Compares running FreeBSD version with installed version

    :param host: PyInfra host object for executing commands
    :type host: pyinfra.context.Host
    :returns: True if reboot is required, False otherwise
    :rtype: bool
    """
    # Shell command to check if reboot is required
    command = """
    # Get OS type
    OS_TYPE=$(uname -s)

    if [ "$OS_TYPE" = "Linux" ]; then
        # Check if it's Alpine Linux
        if [ -f /etc/alpine-release ]; then
            RUNNING_KERNEL=$(uname -r)
            INSTALLED_KERNEL=$(ls -1 /lib/modules | sort -V | tail -n1)
            if [ "$RUNNING_KERNEL" != "$INSTALLED_KERNEL" ]; then
                echo "reboot_required"
                exit 0
            fi
        fi

        # Check for standard Linux reboot required files
        if [ -f /var/run/reboot-required ] || [ -f /var/run/reboot-required.pkgs ] || [ -f /var/run/reboot-needed ]; then
            echo "reboot_required"
            exit 0
        fi

        # Check for pending package updates on systems using pacman (Arch Linux)
        if command -v pacman >/dev/null 2>&1; then
            if [ "$(checkupdates 2>/dev/null | wc -l)" -gt 0 ]; then
                echo "reboot_required"
                exit 0
            fi
        fi

        # Check for pending updates on systems using dnf (Fedora/RHEL)
        if command -v dnf >/dev/null 2>&1; then
            dnf needs-restarting -r >/dev/null 2>&1
            if [ $? -eq 1 ]; then
                echo "reboot_required"
                exit 0
            fi
        fi

        elif [ "$OS_TYPE" = "FreeBSD" ]; then
            RUNNING_VERSION=$(freebsd-version -r)
            INSTALLED_VERSION=$(freebsd-version -k)
            if [ "$RUNNING_VERSION" != "$INSTALLED_VERSION" ]; then
                echo "reboot_required"
                exit 0
            fi
        fi

        # Check for pending updates on systems using apt (Debian/Ubuntu)
        if command -v apt >/dev/null 2>&1; then
            if [ -f /var/run/reboot-required ]; then
                echo "reboot_required"
                exit 0
            fi
        fi
    fi

    echo "no_reboot_required"
    """

    stdout = host.get_fact(Command, command)

    # Ensure stdout is a list for consistent handling
    if isinstance(stdout, str):
        stdout = stdout.splitlines()

    if stdout and stdout[0].strip() == "reboot_required":
        return True

    return False


@deploy("Reboot the system")
def reboot_system(need_reboot=None, force_reboot=False, skip_reboot_check=False):
    """
    Reboot a system if necessary based on various conditions.

    Provides intelligent system reboot functionality with multiple options
    for controlling when and whether to reboot. Can automatically detect
    if a reboot is needed or use manual override parameters.

    .. code:: python

        from infraninja.security.common.reboot_system import reboot_system

        # Auto-detect if reboot is needed
        reboot_system()

        # Force reboot regardless of conditions
        reboot_system(force_reboot=True)

        # Never reboot even if needed
        reboot_system(need_reboot=False)

    :param need_reboot: If True, always reboot. If False, never reboot. If None, check if reboot is required.
    :type need_reboot: bool, optional
    :param force_reboot: If True, override need_reboot and always reboot
    :type force_reboot: bool
    :param skip_reboot_check: If True, skip the reboot check and use need_reboot value directly
    :type skip_reboot_check: bool
    :returns: None
    :rtype: None
    """
    if force_reboot:
        need_reboot = True

    if need_reboot is None and not skip_reboot_check:
        # Check if reboot is required
        need_reboot = check_reboot_required(host)

    if need_reboot is True:
        server.reboot(
            name="Reboot the system",
            delay=90,
            interval=10,
        )
